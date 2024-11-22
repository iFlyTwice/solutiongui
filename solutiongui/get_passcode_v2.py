import argparse
import multiprocessing
import os
import re
import traceback
import uuid
from enum import Enum
from typing import Optional
import threading

try:
    import boto3
    import requests
    from requests_aws4auth import AWS4Auth
    from requests import Response
    import customtkinter as ctk
except ImportError:
    print(
        "Run `pip install boto3 requests requests-aws4auth customtkinter` to install the missing packages"
    )
    print(traceback.format_exc())
    exit(1)

audience = "cognito.amazon.com"
windows = "nt"


class Region(Enum):
    us_west_2 = "us-west-2"
    ap_northeast_1 = "ap-northeast-1"
    ap_south_1 = "ap-south-1"
    eu_west_1 = "eu-west-1"
    us_east_1 = "us-east-1"

    def __str__(self):
        return self.value


device_admin_lambda_accounts = {
    Region.us_west_2: {
        "aws_account_id": "315464380417",
        "identity_pool_id": "us-west-2:d40aaf6c-7dac-4055-8521-5536b1ca0f0b",
        "endpoint": "https://device-admin.integ.us-west-2.device-manager.a2z.com",
    },
    Region.ap_northeast_1: {
        "aws_account_id": "020236585023",
        "identity_pool_id": "ap-northeast-1:e31b73b6-40be-4593-bf81-8453ac65002e",
        "endpoint": "https://device-admin.prod.ap-northeast-1.device-manager.a2z.com",
    },
    Region.ap_south_1: {
        "aws_account_id": "844454935789",
        "identity_pool_id": "ap-south-1:78af6327-f5b3-4d4a-871a-3fa139199f8a",
        "endpoint": "https://device-admin.prod.ap-south-1.device-manager.a2z.com",
    },
    Region.eu_west_1: {
        "aws_account_id": "431731427104",
        "identity_pool_id": "eu-west-1:3db507bd-17b3-4b71-b62a-8f8cc4d16a21",
        "endpoint": "https://device-admin.prod.eu-west-1.device-manager.a2z.com",
    },
    Region.us_east_1: {
        "aws_account_id": "350385424153",
        "identity_pool_id": "us-east-1:a4768e9b-429c-4bfd-82da-574f0cca1630",
        "endpoint": "https://device-admin.prod.us-east-1.device-manager.a2z.com",
    },
}


def retry(f, times):
    """
    Attempts to execute function f up to a specified number of times. Mitigates timeouts due to lambda stack cold start.

    :param f: function to execute
    :param times: number of attempts for function execution
    :return: result of executing function f
    """
    try:
        return f()
    except Exception as e:
        if times == 0:
            raise e
        else:
            return retry(f, times - 1)


def first_or_none(iterable, predicate):
    return next((i for i in iterable if predicate(i)), None)


class MidwayAuthHelper:
    def __init__(self):
        self.cookies = self._get_cookies()
        self.jwt = self._get_midway_token(self.cookies, audience)

    def get_creds(self, aws_account_id, identity_pool_id) -> "tuple[str, str, str]":
        cognito_id = self._get_cognito_id_for_jwt(
            aws_account_id,
            identity_pool_id,
            self.jwt,
        )
        access, secret, session = self._issue_creds_for_cognito_id(cognito_id, self.jwt)
        return access, secret, session

    def _get_cookies(self) -> "dict[str, str]":
        cookies = {}
        home_dir = "HOME" if os.name != windows else "userprofile"
        midway_cookie_path = os.path.join(os.environ.get(home_dir), ".midway", "cookie")
        try:
            with open(midway_cookie_path, "r") as file:
                for line in file:
                    parts = line.split()
                    if len(parts) == 7:
                        cookies[parts[5]] = parts[6]
        except FileNotFoundError:
            print("Midway token not found. Please run 'mwinit --aea' before retry")
            exit(1)
        return cookies

    def _get_midway_token(self, cookies: "dict[str, str]", audience: str) -> str:
        midway_url = "https://midway-auth.amazon.com/SSO"
        audience_url = f"https://{audience}:443"
        headers = {"host": "midway-auth.amazon.com", "origin": audience}
        params = {
            "response_type": "id_token",
            "scope": "openid",
            "client_id": audience,
            "redirect_uri": audience_url,
            "nonce": uuid.uuid4().hex,
        }
        response = requests.get(
            midway_url, params=params, cookies=cookies, headers=headers
        )
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to get midway token: {e}")
        return response.text

    def _get_cognito_id_for_jwt(
            self, aws_account: str, cognito_pool_id: str, jwt: str
    ) -> str:
        identity_response = boto3.client("cognito-identity").get_id(
            AccountId=aws_account,
            IdentityPoolId=cognito_pool_id,
            Logins={"midway-auth.amazon.com": jwt},
        )

        return identity_response["IdentityId"]

    def _issue_creds_for_cognito_id(
            self, cognito_id: str, jwt: str
    ) -> "tuple[str, str, str]":
        credentials_response = boto3.client(
            "cognito-identity"
        ).get_credentials_for_identity(
            IdentityId=cognito_id, Logins={"midway-auth.amazon.com": jwt}
        )
        credentials = credentials_response["Credentials"]
        access_key_id = credentials["AccessKeyId"]
        secret_key = credentials["SecretKey"]
        session_token = credentials["SessionToken"]
        return access_key_id, secret_key, session_token


def get_passcode(serial_number: str, region_string, midway_helper):
    region = Region(region_string)
    boto3.setup_default_session(region_name=region.value)
    try:
        access, secret, session = midway_helper.get_creds(
            device_admin_lambda_accounts[region]["aws_account_id"],
            device_admin_lambda_accounts[region]["identity_pool_id"]
        )
        aws_auth = AWS4Auth(
            access,
            secret,
            region.value,
            "execute-api",
            session_token=session,
        )
        url = f"{device_admin_lambda_accounts[region]['endpoint']}/devices/{serial_number}/passcode"

        def get() -> Response:
            response = requests.get(url, auth=aws_auth, timeout=30)
            response.raise_for_status()
            return response

        return region, retry(get, 3).json()
    except Exception as e:
        return region, {"error": str(e)}


def parse_sn(sn: str) -> Optional[str]:
    pattern = re.compile("[sS]?([a-zA-Z0-9]+)(_[a-zA-Z0-9]*)?")
    match = pattern.match(sn)
    groups = [] if not match else match.groups()
    if not groups:
        return None
    else:
        return groups[0]


class PasscodeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Passcode Retriever")
        self.geometry("400x300")
        self.resizable(False, False)

        # Serial Number Input
        self.serial_label = ctk.CTkLabel(self, text="Device Serial Number:")
        self.serial_label.pack(pady=(20, 5))
        self.serial_entry = ctk.CTkEntry(self, width=300)
        self.serial_entry.pack(pady=5)

        # Region Selection
        self.region_label = ctk.CTkLabel(self, text="Select Region:")
        self.region_label.pack(pady=(20, 5))
        self.region_var = ctk.StringVar(value="us-east-1")
        regions = [region.value for region in Region]
        self.region_dropdown = ctk.CTkOptionMenu(self, values=regions, variable=self.region_var)
        self.region_dropdown.pack(pady=5)

        # Submit Button
        self.submit_button = ctk.CTkButton(self, text="Get Passcode", command=self.fetch_passcode)
        self.submit_button.pack(pady=(20, 10))

        # Result Display
        self.result_label = ctk.CTkLabel(self, text="", text_color="green")
        self.result_label.pack(pady=5)

        # Error Display
        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.pack(pady=5)

        # Initialize MidwayAuthHelper
        self.midway_helper = MidwayAuthHelper()

    def fetch_passcode(self):
        serial_number = self.serial_entry.get().strip()
        region = self.region_var.get()

        if not serial_number:
            self.error_label.configure(text="Please enter a serial number.")
            self.result_label.configure(text="")
            return

        parsed_sn = parse_sn(serial_number)
        if not parsed_sn:
            self.error_label.configure(text="Invalid serial number format.")
            self.result_label.configure(text="")
            return

        self.error_label.configure(text="")
        self.result_label.configure(text="Fetching passcode...")

        # Run in a separate thread to avoid blocking the GUI
        threading.Thread(target=self.retrieve_passcode, args=(parsed_sn, region), daemon=True).start()

    def retrieve_passcode(self, serial_number, region):
        region_enum = next((r for r in Region if r.value == region), None)
        if not region_enum:
            self.update_result("Selected region is invalid.", error=True)
            return

        region, data = get_passcode(serial_number, region, self.midway_helper)

        if "error" in data:
            self.update_result(f"Error: {data['error']}", error=True)
        else:
            if "desired" in data and data["reported"] != data["desired"]:
                message = f"Current passcode: {data['reported']}\nUpcoming passcode: {data['desired']}"
            else:
                message = f"Passcode: {data['reported']}"
            self.update_result(message, error=False)

    def update_result(self, message, error=False):
        if error:
            self.error_label.configure(text=message)
            self.result_label.configure(text="")
        else:
            self.result_label.configure(text=message)
            self.error_label.configure(text="")


if __name__ == "__main__":
    app = PasscodeApp()
    app.mainloop()
