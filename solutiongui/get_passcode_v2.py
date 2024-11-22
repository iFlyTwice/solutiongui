import argparse
import multiprocessing
import os
import re
import traceback
import uuid
from enum import Enum
from typing import Optional

try:
    import boto3
    import requests
    from requests_aws4auth import AWS4Auth
    from requests import Response
except ImportError:
    print(
        "Run `pip install boto3 requests requests-aws4auth` to install the missing packages"
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
    except:
        if times == 0:
            raise
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Example: \"python3 get_passcode.py \
        -s 012345678910 \
        -r us-east-1\".\
        Available regions: \
          \"us-east-1\" (for North America), \
          \"eu-west-1\" (for Europe), \
          \"ap-south-1\" (for South Asia Pacific regions), \
          \"ap-northeast-1\" (for North-East Asia Pacific regions)."
    )
    parser.add_argument(
        "-s", "--serial-number", required=True, help="Device serial number"
    )
    parser.add_argument(
        "-r",
        "--region",
        type=Region,
        required=False,
        help="Region the device is enrolled in",
    )
    args = parser.parse_args()
    if args.region:
        regions = [args.region]
    else:
        regions = [region.value for region in Region]
    serial_number = parse_sn(args.serial_number)
    if not serial_number:
        print('  Error: invalid serial number')
    else:
        midway_helper = MidwayAuthHelper()
        with multiprocessing.Pool(len(regions)) as pool:
            results = pool.starmap(get_passcode, [(serial_number, region, midway_helper) for region in regions])
            result = first_or_none(results, lambda res: "reported" in res[1])
            if result:
                region, data = result
                print(f"Result for {region}:")
                if "desired" in data and data["reported"] != data["desired"]:
                    print(f'  Current passcode: {data["reported"]}, upcoming passcode: {data["desired"]}')
                else:
                    print(f'  Passcode: {data["reported"]}')
            else:
                for region, data in results:
                    message = "  Passcode not found" if "error" not in data else f'  {data["error"]}'
                    print(f"Result for {region}:")
                    print(message)
