import customtkinter as ctk 
import logging
from tkinter import PhotoImage  # Removed messagebox import
import os
import sys
import asyncio
import threading
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import gui_helpers  # Updated import to match the correct helper file
from PIL import Image
import pystray
import ctypes  # Added for window style modifications
import hid  # Import hid library for HID device interaction
from plyer import notification  # For system notifications
import time  # Required for sleep in monitoring thread
import tray_icon  # Import tray_icon module
import manage_zukey  # Added import for Manage Zukey window
from playwright_helpers import open_page, close_resources  # {{ edit_1 }}
from notification_manager import show_notification  # Ensure necessary imports
from gui_helpers import create_credentials_frame  # Ensure this import is present
import requests  # {{ edit_15 }}
import json  # {{ edit_22 }}
import subprocess  # {{ edit_27 }}
import pyautogui  # {{ edit_28 }}
import keyboard  # {{ edit_39 }}
from queue import Queue  # {{ edit_new }}
import socket  # {{ edit_new }}
from gui_helpers import create_security_keys_list  # Ensure this import is present and correct
import cv2  # Added for image processing and template matching
import numpy as np  # Added for array manipulations
from automation import reset_security_key  # Ensure this import is present
import tkinter as tk  # Added for VPN warning window
from tkinter import messagebox  # Added for VPN warning window

ctk.set_appearance_mode("System")  # {{ set_appearance_mode }} Set appearance mode to system default
ctk.set_default_color_theme("blue")  # {{ set_default_color_theme }} Set default CTk color theme

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Changed from DEBUG to INFO for optimization
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('link_opener.log'),
        logging.StreamHandler()  # Output logs to the terminal
    ]
)

# Define the URLs
LINKS = {
    "GENERAL DASHBOARD": "http://toolkit.corp.amazon.com/",
    "MIDWAY ACCESS": "https://midway-auth.amazon.com/login#midway",
    "TICKETS LINK": "https://sn.opstechit.amazon.dev/now/sow/list/params/list-id/5157c5f0d50016d8460775c0d73bf852/tiny-id/f0dPdsysuOM3HFYqPzQNNuQeKbR8w039",
    "REPORTS": "https://your-reports-page.url"
}

# Define the configuration file path
CONFIG_FILE = "gui_config.json"  # {{ edit_23 }}

VPN_CHECK_URL = "http://internal.example.com"  # Replace with a valid internal VPN-required URL  # {{ edit_new }}

def is_vpn_connected(test_url=VPN_CHECK_URL):  # {{ edit_new }}
    """
    Checks if the system is connected to the VPN by resolving a known internal URL.

    Args:
        test_url (str): A known internal URL that requires VPN access.

    Returns:
        bool: True if the VPN is connected, False otherwise.
    """
    try:
        # Extract hostname from the test URL
        hostname = test_url.split("://")[1].split("/")[0]
        # Attempt to resolve the hostname
        socket.gethostbyname(hostname)
        logging.info("VPN connection is active.")
        return True
    except socket.gaierror:
        logging.error("VPN connection is not active. Failed to resolve hostname.")
        return False

def show_vpn_warning():  # {{ edit_new }}
    """
    Shows a custom window indicating that the VPN connection is required, with additional enhancements.
    """
    def on_checkbox_toggle():
        # Enable or disable the "Continue" button based on checkbox state
        if proceed_var.get():
            continue_button.configure(state="normal")
        else:
            continue_button.configure(state="disabled")

    def on_continue_click():
        # Close the VPN warning window and launch the main application
        vpn_window.destroy()
        root = ctk.CTk()  # Create a new root for the main app
        app = QuickLinksApp(root)  # Initialize the QuickLinksApp
        root.mainloop()  # Start the main event loop

    def open_help_page():
        """
        Opens the help page or documentation for VPN setup.
        """
        messagebox.showinfo("Help", "Please connect to the VPN by following the instructions in the documentation.")

    # Create VPN warning window
    vpn_window = ctk.CTk()
    vpn_window.title("VPN Connection Required")
    
    # Set fixed size and disable resizing
    vpn_window.geometry("500x400")  # Changed from "400x300" to "500x400"
    vpn_window.resizable(False, False)  # Disable window resizing
    
    # Center the window on the screen
    screen_width = vpn_window.winfo_screenwidth()
    screen_height = vpn_window.winfo_screenheight()
    position_x = (screen_width // 2) - (500 // 2)
    position_y = (screen_height // 2) - (400 // 2)
    vpn_window.geometry(f"500x400+{position_x}+{position_y}")
    
    # Add fade-in effect
    vpn_window.attributes("-alpha", 0)  # Set initial transparency
    for i in range(10):
        vpn_window.after(100 * i, lambda alpha=i / 10: vpn_window.attributes("-alpha", alpha))
    
    # Add a label with the warning message
    warning_label = ctk.CTkLabel(
        master=vpn_window,
        text="Please connect to the VPN before launching the application.",
        font=("Helvetica", 16, "bold"),  # Increase font size and make it bold
        text_color="yellow",
        anchor="center"
    )
    warning_label.pack(pady=20, padx=20)  # Ensure spacing around the label
    
    # Add a checkbox to proceed without VPN
    proceed_var = ctk.BooleanVar()
    proceed_checkbox = ctk.CTkCheckBox(
        master=vpn_window,
        text="Proceed without VPN",
        variable=proceed_var,
        command=on_checkbox_toggle
    )
    proceed_checkbox.pack(pady=10)  # Add padding for the checkbox
    
    # Add a "Continue" button, initially disabled
    continue_button = ctk.CTkButton(
        master=vpn_window,
        text="Continue",
        command=on_continue_click,
        state="disabled",  # Disabled by default
        width=120,
        height=30,
        hover_color="lightblue",  # Add hover color for visual feedback
        corner_radius=10  # Rounded corners
    )
    continue_button.pack(pady=10)
    
    # Add a "Retry VPN Check" button
    retry_button = ctk.CTkButton(
        master=vpn_window,
        text="Retry VPN Check",
        command=lambda: retry_vpn_check(vpn_window, warning_label),
        width=120,
        height=30
    )
    retry_button.pack(pady=10)
    
    # Add a "Help" button
    help_button = ctk.CTkButton(
        master=vpn_window,
        text="Help",
        command=open_help_page,  # Function to open a help page or documentation
        width=100,
        height=30
    )
    help_button.pack(pady=10)
    
    # Add an "Exit" button
    exit_button = ctk.CTkButton(
        master=vpn_window,
        text="Exit",
        command=sys.exit,
        width=120,
        height=30
    )
    exit_button.pack(pady=10)
    
    vpn_window.mainloop()

def retry_vpn_check(vpn_window, warning_label):
    """
    Retries the VPN connection check and updates the warning message accordingly.
    """
    if is_vpn_connected():
        messagebox.showinfo("VPN Status", "VPN connection is active.")
    else:
        messagebox.showerror("VPN Status", "VPN connection is still not active.")

def save_window_geometry(root):
    """
    Saves the window geometry (size and position) to a JSON file.
    
    Args:
        root (ctk.CTk): The root window instance.
    """
    geometry = root.geometry()  # Get geometry as "WxH+X+Y"
    config = {"geometry": geometry}
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        logging.info(f"Window geometry saved to {CONFIG_FILE}.")
    except Exception as e:
        logging.exception("Failed to save window geometry.")

def load_window_geometry(root):
    """
    Loads the window geometry (size and position) from a JSON file, if it exists.
    
    Args:
        root (ctk.CTk): The root window instance.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            geometry = config.get("geometry", None)
            if geometry:
                root.geometry(geometry)
                logging.info(f"Window geometry loaded from {CONFIG_FILE}: {geometry}")
        except Exception as e:
            logging.warning("Failed to load window geometry. Using default size.")
            root.geometry("800x600")  # Default size
    else:
        logging.info("No configuration file found. Using default window size.")
        root.geometry("800x600")  # Default size

def wait_for_element(template, confidence=0.9, timeout=5):  # {{ edit_new }}
    """
    Waits for an element to appear on the screen using PyAutoGUI.

    Args:
        template (str): Path to the image template for matching.
        confidence (float): Confidence level for the match.
        timeout (int): Maximum time to wait in seconds.

    Returns:
        location: Coordinates of the matched element, or None if not found.
    """
    start = time.time()
    while time.time() - start < timeout:
        location = pyautogui.locateOnScreen(template, confidence=confidence)
        if location:
            return location
        time.sleep(0.1)  # Short interval for faster checks
    return None

def reset_security_key():  # {{ reset_security_key_function }}
    """
    Automates the process of resetting a security key via Windows settings.
    """
    try:
        # Step 1: Open Sign-in Options via Windows settings
        subprocess.run("start ms-settings:signinoptions", shell=True)
        
        # Step 2: Wait for Sign-in Options to load and click Security Key button
        location = wait_for_element("security_key_button.png", confidence=0.9, timeout=5)
        if not location:
            logging.error("Security Key button not found.")
            QuickLinksApp.update_notification_static("Error: Security Key button not found.", "red")
            return
        pyautogui.click(pyautogui.center(location))
        
        # Step 3: Wait for "Manage" button and click it
        location = wait_for_element("manage_button.png", confidence=0.9, timeout=3)
        if not location:
            logging.error("Manage button not found.")
            QuickLinksApp.update_notification_static("Error: Manage button not found.", "red")
            return
        pyautogui.click(pyautogui.center(location))
        
        # Step 4: Wait for "Reset" button and click it
        location = wait_for_element("reset_button.png", confidence=0.9, timeout=3)
        if location:
            pyautogui.click(pyautogui.center(location))
            logging.info("Reset completed successfully.")
            QuickLinksApp.update_notification_static("Security key reset successfully!", "green")
        else:
            logging.error("Reset button not found.")
            QuickLinksApp.update_notification_static("Error: Reset button not found.", "red")
    except Exception as e:
        logging.error(f"An error occurred during the reset process: {e}")
        QuickLinksApp.update_notification_static(f"Error: An error occurred during the reset process: {e}", "red")

class QuickLinksApp:
    _instance = None  # {{ singleton_instance }}

    def __init__(self, root):
        if QuickLinksApp._instance is not None:
            raise Exception("This class is a singleton!")
        QuickLinksApp._instance = self  # {{ set_instance }}
        
        self.root = root
        self.root.title("Quick Links Dashboard")
        
        # Configure root grid to make rows and columns stretchable
        self.root.grid_rowconfigure(0, weight=1)  # For the button frame
        self.root.grid_rowconfigure(1, weight=0)  # For the credentials frame
        self.root.grid_rowconfigure(2, weight=1)  # For the log frame
        self.root.grid_columnconfigure(0, weight=1)  # Single-column layout
        
        # Set window size and position using gui_helpers module
        gui_helpers.set_window_size(self.root)
        
        # Set the window icon
        self.set_window_icon()
        
        # Remove the maximize button without hiding from the taskbar
        if sys.platform.startswith('win'):
            try:
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)
                style &= ~0x00010000  # WS_MAXIMIZEBOX
                ctypes.windll.user32.SetWindowLongW(hwnd, -16, style)
                logging.info("Maximize button disabled.")
            except Exception as e:
                logging.exception("Failed to modify window style to disable maximize button.")
        
        # Initialize PIN visibility state
        self.pin_visible = False

        # Initialize log_queue before adding the log handler
        self.log_queue = Queue()  # {{ edit_new }}
        
        # Create GUI elements
        self.create_widgets()
        
        # Setup system tray icon
        self.setup_tray_icon()
        
        # Initialize security keys list
        self.connected_keys = []
        self.notification_label = self.create_notification_label()  # {{ initialize_notification_label }}
        self.update_keys_lock = threading.Lock()
        
        # Initialize log monitoring variables and batching
        self.stop_log_monitor = threading.Event()  # {{ edit_new }}
        self.log_monitor_thread = None
        self.previous_log_line = ""  # Store the last log line to filter redundant logs
        self.pending_logs = []       # Batch updates to optimize performance
        self.flush_logs_lock = threading.Lock()  # {{ edit_new }}
        
        # Start monitoring security keys
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_security_keys, daemon=True)  # {{ edit_2 }}
        self.monitor_thread.start()
        
        # Add custom logging handler to direct logs to the textbox
        self.add_textbox_log_handler()

        # Restore window size and position
        load_window_geometry(self.root)  # {{ edit_25 }}
        
        # {{ edit_29 }} Initialize automation lock
        self.automation_lock = threading.Lock()

        # Start periodic flushing of logs every 500ms
        self.root.after(500, self.flush_logs_periodically)  # {{ edit_new }}
        
        # Configure textbox highlighting
        self.configure_textbox_highlighting()

        # Start polling the log queue
        self.update_logs_periodically()  # {{ edit_new }}

        # Initialize failure_status_label
        self.failure_status_label = ctk.CTkLabel(
            self.root,
            text="",  # Initially empty
            font=("Helvetica", 14),
            text_color="red",
            anchor="center"
        )

    @classmethod
    def get_instance(cls):  # {{ get_instance_method }}
        """
        Returns the singleton instance of QuickLinksApp.
        """
        return cls._instance

    def add_textbox_log_handler(self):
        """
        Adds a custom logging handler to direct log messages to the log_textbox.
        """
        if hasattr(self, 'log_textbox') and self.log_textbox:
            handler = TextBoxHandler(self.log_queue)  # Pass log_queue {{ edit_1 }}
            handler.setLevel(logging.INFO)  # Changed to INFO for optimization
            logging.getLogger().addHandler(handler)
            logging.info("TextBoxHandler added to logger.")
        else:
            logging.warning("log_textbox not initialized. Cannot add TextBoxHandler.")
    
    def set_window_icon(self):
        """
        Sets the window icon if the icon file exists, otherwise uses a default.
        """
        icon_path = "icon.ico"
        if not os.path.exists(icon_path):
            logging.warning("icon.ico not found. Using default icon.")
            icon_path = os.path.join(os.path.dirname(__file__), "default_icon.ico")  # {{ edit_new }}

        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
                logging.info("Window icon set successfully.")
            except Exception as e:
                logging.warning(f"Failed to set window icon: {e}")
        else:
            logging.error(f"Default icon file {icon_path} not found.")  # {{ edit_new }}
            self.root.after(0, lambda e=None: self.update_notification(
                "Default icon file '{icon_path}' not found. Please ensure it exists.",
                "red"
            ))  # {{ edit_new }}

    def create_widgets(self):
        """
        Creates all the GUI widgets.
        """
        # Create window controls (Minimize and Exit) at top right
        # Commenting out since we are removing the window control buttons
        # gui_helpers.create_window_controls(
        #     root=self.root,
        #     on_closing_callback=self.on_closing,
        #     on_minimize_callback=self.on_minimize
        # )

        # Create button frame and buttons (including "Manage Zukey")
        gui_helpers.create_button_frame(
            root=self.root,
            links=LINKS,
            open_link_callback=self.open_link,
            handle_midway_access_callback=self.handle_midway_access,
            open_manage_zukey_callback=self.open_manage_zukey,
            open_general_dashboard_callback=self.open_general_dashboard_window
        )
        
        # Create credentials frame
        self.username_entry, self.pin_entry, self.show_pin_button = gui_helpers.create_credentials_frame(
            root=self.root,
            toggle_pin_visibility_callback=self.toggle_pin_visibility
        )
        
        # Add status label below credentials with fixed space
        self.midway_status_label = ctk.CTkLabel(
            self.root,
            text="",  # Initially empty
            font=("Helvetica", 14),
            text_color="green",
            anchor="center"
        )
        self.midway_status_label.pack(pady=10, padx=60, fill="x")  # Positioned appropriately
        
        # Create security keys list with double-click support {{ edit_24 }}
        self.security_keys_list = gui_helpers.create_security_keys_list(
            self.root, 
            self.on_security_key_double_click  # {{ edit_24 }}
        )
        
        # Create Log Frame
        self.log_frame = ctk.CTkFrame(self.root)
        self.log_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Add Debug Logs Label
        self.log_label = ctk.CTkLabel(self.log_frame, text="Debug Logs", font=("Helvetica", 16))
        self.log_label.pack(padx=10, pady=5, anchor="w")

        # Add Log Textbox
        self.log_textbox = ctk.CTkTextbox(self.log_frame, wrap="word", width=600, height=400, state="disabled")
        self.log_textbox.pack(padx=10, pady=5, fill="both", expand=True)

        # Create a frame to hold the buttons
        buttons_container = ctk.CTkFrame(self.log_frame)
        buttons_container.pack(fill="x", pady=5)

        # Refresh Logs Button (Aligned Left)
        self.refresh_button = ctk.CTkButton(
            buttons_container,
            text="Refresh Logs",
            command=self.load_logs,
            width=100
        )
        self.refresh_button.pack(side="left", padx=10)

        # View Full Logs Button (Aligned Right)
        self.view_full_logs_button = ctk.CTkButton(
            buttons_container,
            text="View Full Logs",
            command=self.show_full_logs,
            width=100
        )
        self.view_full_logs_button.pack(side="right", padx=10)

        # New Scanner APW button
        self.scanner_apw_button = ctk.CTkButton(
            buttons_container,
            text="Scanner APW",
            command=self.open_scanner_apw,  # Define this method for functionality
            width=120
        )
        self.scanner_apw_button.pack(side="left", padx=10)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(
            self.root,
            orientation="horizontal",
            mode="indeterminate"
        )
        self.progress_bar.pack(pady=5, padx=20, fill="x")
        self.progress_bar.stop()

        # Bind the window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Add "Reset Security Key" button
        self.reset_security_key_button = ctk.CTkButton(
            self.root,
            text="Reset Security Key",
            command=self.reset_security_key,  # {{ edit_new }}
            width=150
        )
        self.reset_security_key_button.pack(pady=10)

        # Add Failure Status Label
        self.failure_status_label = ctk.CTkLabel(
            self.root,
            text="",  # Start with an empty message
            font=("Helvetica", 14),
            text_color="red",
            anchor="center"
        )
        self.failure_status_label.pack(pady=10, padx=60, fill="x")  # Positioned below other elements

        # Add the notification label at the top
        self.notification_label = self.create_notification_label()  # {{ initialize_notification_label }}

    def load_logs(self):
        """
        Loads the contents of the log file into the log textbox.
        """
        try:
            with open('link_opener.log', 'r') as log_file:
                content = log_file.read()
            self.log_textbox.configure(state="normal")
            self.log_textbox.delete("0.0", "end")
            self.log_textbox.insert("0.0", content)
            self.log_textbox.configure(state="disabled")
        except Exception as e:
            logging.exception("Failed to load log file.")
            self.log_textbox.configure(state="normal")
            self.log_textbox.delete("0.0", "end")
            self.log_textbox.insert("0.0", f"Failed to load log file.\nError: {e}")
            self.log_textbox.configure(state="disabled")

    def toggle_pin_visibility(self):
        self.pin_visible = gui_helpers.toggle_pin_visibility(
            pin_entry=self.pin_entry,
            show_pin_button=self.show_pin_button,
            pin_visible=self.pin_visible
        )

    def open_link(self, url, name):
        thread = threading.Thread(target=self.open_link_thread, args=(url, name), daemon=True)
        thread.start()

    def open_link_thread(self, url, name):
        try:
            loop = asyncio.new_event_loop()      # Create a new event loop
            asyncio.set_event_loop(loop)         # Set it as the current event loop in this thread
            loop.run_until_complete(self.async_open_link(url, name))
        except Exception as e:
            logging.exception(f"Failed to open URL with Playwright: {name} - {url}")
            self.root.after(0, lambda e=e: self.update_notification(f"Failed to open {name}.\nError: {e}", "red"))  # Added error message

    async def setup_playwright(self, channel="chrome", headless=False, args=None):
        """
        Sets up Playwright with a new browser, context, and page.

        Args:
            channel (str): The browser channel to use.
            headless (bool): Whether to run the browser in headless mode.
            args (list): Additional arguments for browser launch.

        Returns:
            tuple: (page, context, browser, playwright)
        """
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(channel=channel, headless=headless, args=args or [])
            context = await browser.new_context()
            page = await context.new_page()
            return page, context, browser, playwright
        except Exception as e:
            logging.exception("Failed to setup Playwright.")
            raise

    async def navigate_to_page(self, page, url, timeout=60000):
        """
        Navigates the Playwright page to the specified URL.

        Args:
            page (Page): The Playwright Page object.
            url (str): The URL to navigate to.
            timeout (int): The timeout for page navigation in milliseconds.
        """
        try:
            await page.goto(url, timeout=timeout)
            logging.info(f"Successfully navigated to {url}.")
        except PlaywrightTimeoutError:
            logging.error(f"Timeout while navigating to {url}.")
            raise
        except Exception as e:
            logging.exception(f"Failed to navigate to {url}.")
            raise

    async def async_open_link(self, url, name):
        try:
            # Check VPN connection before proceeding {{ edit_18 }}
            if "corp.amazon.com" in url and not self.check_vpn_connection():
                logging.error("VPN is not connected. Cannot access internal URLs.")
                self.update_notification(
                    "VPN Connection Error",
                    "Please connect to the corporate VPN before running this script."
                )
                return
            
            page, context, browser, playwright = await self.setup_playwright(args=["--start-maximized"])
            await self.navigate_to_page(page, url)
            logging.info(f"Opened URL with Playwright: {name} - {url}")
            page_title = await page.title()
            logging.info(f"Page Title for {name}: {page_title}")
        finally:
            await close_resources(page, context, browser, playwright)

    def create_notification_label(self):  # {{ create_notification_label }}
        """
        Creates a notification label below the PIN field for status updates.
        """
        notification_label = ctk.CTkLabel(
            self.root,
            text="",  # Initially empty
            font=("Helvetica", 12),
            text_color="green",
            anchor="w"
        )
        # Place the label below the PIN field (adjust coordinates as needed)
        notification_label.place(x=150, y=120)  # Adjust `x` and `y` based on GUI layout
        return notification_label

    def monitor_security_keys(self):  # {{ edit_4 }}
        """
        Monitors connected security keys and updates the GUI accordingly.
        """
        while self.monitoring:
            try:
                new_keys = []
                if HAS_HID:
                    # Enumerate devices using hid
                    devices = hid.enumerate()
                    new_keys = [
                        f"{device['manufacturer_string']} {device['product_string']}"
                        for device in devices if self.is_security_key(device)
                    ]
                elif HAS_PYUSB:
                    # Enumerate devices using pyusb
                    devices = usb.core.find(find_all=True)
                    for device in devices:
                        try:
                            manufacturer = usb.util.get_string(device, device.iManufacturer)
                            product = usb.util.get_string(device, device.iProduct)
                            device_info = {
                                "vendor_id": device.idVendor,
                                "product_string": product,
                                "manufacturer": manufacturer
                            }
                            if self.is_security_key(device_info):
                                new_keys.append(f"{manufacturer} {product}")
                        except Exception as e:
                            logging.error(f"Error retrieving device information with pyusb: {e}")
                            continue

                with self.update_keys_lock:
                    # Detect added and removed keys
                    added_keys = list(set(new_keys) - set(self.connected_keys))
                    removed_keys = list(set(self.connected_keys) - set(new_keys))
                    self.connected_keys = new_keys

                    if added_keys or removed_keys:
                        self.update_security_keys_list(new_keys)
                        if added_keys:
                            self.notify_key_event(added_keys, "added")
                            for key in added_keys:
                                logging.info(f"Detected new security key: {key}")
                        if removed_keys:
                            self.notify_key_event(removed_keys, "removed")
                            for key in removed_keys:
                                logging.info(f"Detected removed security key: {key}")
            except Exception as e:
                logging.error(f"Error monitoring security keys: {e}")
            time.sleep(1)  # Delay to reduce CPU usage

    def is_security_key(self, device):  # Updated method to handle both hid and pywin32
        """
        Determines if a device is a security key.

        Args:
            device (dict): Device information dictionary.

        Returns:
            bool: True if the device is a recognized security key, False otherwise.
        """
        known_vendors = [0x1050, 0x096e, 0x1949]  # Example vendor IDs for security keys
        if "vendor_id" in device and device["vendor_id"] in known_vendors:
            return True

        product = device.get("product_string", "").lower()
        key_keywords = ["yubikey", "titan", "authenticator", "zukey"]
        return any(keyword in product for keyword in key_keywords)

    def is_security_key_pywin32(self, device):  # {{ edit_6 }}
        """
        Determines if a device is a security key using pywin32.
        """
        known_vendors = [0x1050, 0x096e, 0x1949]  # Add known vendor IDs for security keys
        if device['VendorId'] in known_vendors:
            return True
        key_keywords = ["yubikey", "titan", "authenticator", "zukey"]  # Add relevant keywords
        product = device['ProductName'].lower()
        return any(keyword in product for keyword in key_keywords)

    def get_usb_devices_with_pywin32(self):  # {{ edit_new }}
        """
        Retrieves USB devices using pywin32.

        Returns:
            list: A list of dictionaries containing device information.
        """
        devices = []
        try:
            import win32com.client
            wmi = win32com.client.GetObject("winmgmts:")
            for usb in wmi.InstancesOf("Win32_USBHub"):
                device = {
                    "Manufacturer": usb.Manufacturer or "Unknown",
                    "ProductName": usb.Name or "Unknown",
                    "VendorId": int(usb.DeviceID.split("&")[1], 16),
                    "ProductId": int(usb.DeviceID.split("&")[2], 16)
                }
                devices.append(device)
        except Exception as e:
            logging.error(f"Failed to retrieve USB devices with pywin32: {e}")
        return devices

    def update_security_keys_list(self, keys):  # {{ edit_7 }}
        """
        Updates the security keys list in the GUI.
        """
        self.security_keys_list.configure(state="normal")
        self.security_keys_list.delete("1.0", "end")
        for key in keys:
            self.security_keys_list.insert("end", f"{key}\n")
        self.security_keys_list.configure(state="disabled")

    def notify_key_event(self, keys, event):  # {{ edit_8 }}
        """
        Displays a notification for added/removed keys.
        """
        message = f"{', '.join(keys)} has been {event}."
        notification.notify(
            title=f"Security Key {event.capitalize()}",
            message=message,
            timeout=5  # Notification will disappear after 5 seconds
        )
        logging.info(f"Security Key {event.capitalize()}: {message}")

        # Update notification label in the GUI
        self.notification_label.configure(text=message)
        self.root.after(5000, lambda: self.notification_label.configure(text=""))  # Clear message after 5 seconds

    def on_closing(self):
        """
        Handles the window close event. Stops the monitoring thread and saves the window geometry before closing.
        """
        try:
            # Save window size and position before stopping the monitoring thread
            save_window_geometry(self.root)  # {{ edit_26 }}
        except Exception as e:
            logging.warning(f"Failed to save window geometry: {e}")
        
        # Stop the monitoring thread
        self.monitoring = False  # {{ edit_existing }}
        if self.monitor_thread.is_alive():
            logging.info("Waiting for monitoring thread to stop...")
            self.monitor_thread.join()  # Wait for the thread to exit cleanly
        
        # Destroy the root window
        self.root.destroy()  # Ensure this is called last
        logging.info("Application closed.")

    def on_minimize(self):
        """
        Handles the window minimize event.
        """
        self.root.iconify()

    def handle_midway_access(self):
        """
        Handles the MIDWAY ACCESS button click and validates username and PIN inputs.
        """
        username = self.username_entry.get().strip()
        pin = self.pin_entry.get().strip()

        if not username or not pin:
            # Update the status label to show the error message
            self.midway_status_label.configure(
                text="Error: Username and PIN fields cannot be empty.",
                text_color="red"
            )
            # Schedule to clear the label after 5 seconds
            self.root.after(5000, self.clear_failure_status_label)
            return

        # If validation passes, proceed with the automation
        threading.Thread(target=self.run_midway_automation, daemon=True).start()

    def run_midway_automation(self):  # {{ edit_4 }}
        """
        Runs the MIDWAY ACCESS automation.
        """
        try:
            self.start_loading()  # Start progress bar animation {{ edit_5 }}
            asyncio.run(self.midway_automation())
        except Exception as e:
            logging.exception("An error occurred during MIDWAY ACCESS automation.")
            error_message = f"Automation failed: {str(e)}"
            self.show_failure_status(error_message)  # Show the failure message
        finally:
            self.stop_loading()  # Stop progress bar animation {{ edit_6 }}

    async def midway_automation(self):  # {{ edit_1 }}
        """
        Automates accessing MIDWAY ACCESS.
        """
        # Check VPN connection before proceeding
        if not self.check_vpn_connection("http://internal.example.com"):  # {{ edit_2 }}
            self.midway_status_label.configure(
                text="Error: Please connect to the corporate VPN.",
                text_color="red"
            )
            logging.error("VPN is not connected. Cannot access MIDWAY ACCESS.")
            return

        url = LINKS["MIDWAY ACCESS"]
        try:
            page, context, browser, playwright = await open_page(url)
        
            # Define the possible selectors
            username_selectors = ['#user_name', 'input[name="user_name"]']
            pin_selectors = ['#password', 'input[name="password"]']
            submit_button_selectors = ['#verify_btn', 'input[type="submit"]']
        
            # Helper to find the first available selector
            async def find_selector(page, selectors):
                for selector in selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=3000)
                        return selector
                    except PlaywrightTimeoutError:
                        continue
                raise Exception(f"No valid selector found in {selectors}")
        
            # Interact with the login fields
            username_selector = await find_selector(page, username_selectors)
            pin_selector = await find_selector(page, pin_selectors)
            submit_button_selector = await find_selector(page, submit_button_selectors)
        
            # Fill out the form
            username = self.username_entry.get()
            pin = self.pin_entry.get()
            await page.fill(username_selector, username)
            await page.fill(pin_selector, pin)
        
            # Submit the form
            await page.click(submit_button_selector)
            logging.info("Login form submitted.")
        
            # Wait for navigation or a success indicator
            await page.wait_for_load_state('networkidle', timeout=15000)
            success_title = await page.title()
            logging.info(f"Login successful. Page Title: {success_title}")
            
            # Update the success label
            self.midway_status_label.configure(
                text=f"Successfully logged into MIDWAY ACCESS.\nPage Title: {success_title}",
                text_color="green"
            )
            # Schedule the label to be cleared after 5 seconds
            self.root.after(5000, self.clear_failure_status_label)
        except PlaywrightTimeoutError:
            logging.exception("Timeout occurred during MIDWAY ACCESS automation.")
            self.midway_status_label.configure(
                text="Timeout occurred while automating MIDWAY ACCESS.",
                text_color="red"
            )
            # Schedule the label to be cleared after 5 seconds
            self.root.after(5000, self.clear_failure_status_label)
        except Exception as e:
            if "ERR_NAME_NOT_RESOLVED" in str(e):
                self.midway_status_label.configure(
                    text="Error: Unable to resolve the domain. Please check your VPN connection.",
                    text_color="red"
                )
            else:
                self.midway_status_label.configure(
                    text=f"Automation Error: {e}",
                    text_color="red"
                )
            logging.exception("Failed to complete MIDWAY ACCESS automation.")
            self.root.after(5000, self.clear_failure_status_label)

    def start_loading(self):  # {{ edit_11 }}
        """
        Starts the progress bar animation.
        """
        if hasattr(self, "progress_bar"):
            self.progress_bar.start()
        else:
            logging.error("Progress bar not initialized.")
    
    def stop_loading(self):  # {{ edit_12 }}
        """
        Stops the progress bar animation.
        """
        if hasattr(self, "progress_bar"):
            self.progress_bar.stop()
        else:
            logging.error("Progress bar not initialized.")

    def show_message(self, title, message):  # {{ edit_13 }}
        """
        Shows a success message using a messagebox.

        Args:
            title (str): Title of the messagebox.
            message (str): Message to display.
        """
        self.root.after(0, lambda: self.update_notification(title, message))

    def show_error(self, title, message):  # {{ edit_14 }}
        """
        Shows an error message using a messagebox.

        Args:
            title (str): Title of the messagebox.
            message (str): Message to display.
        """
        self.root.after(0, lambda: self.update_notification(title, message))

    def setup_tray_icon(self):
        """
        Sets up the system tray icon using pystray.
        """
        try:
            # Use absolute path for reliability
            icon_path = os.path.join(os.path.dirname(__file__), "tray_icon.ico")
            if not os.path.exists(icon_path):
                raise FileNotFoundError(f"Tray icon file not found at: {icon_path}")
            
            image = Image.open(icon_path)
            menu = pystray.Menu(
                pystray.MenuItem("Open", self.show_window),
                pystray.MenuItem("Exit", self.exit_application)
            )
            self.tray_icon = pystray.Icon("QuickLinksApp", image, "Quick Links Dashboard", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            logging.info("System tray icon initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to set up tray icon: {e}")
            self.update_notification("Failed to set up system tray icon.", "red")

    def show_window(self):
        """
        Restores the main window from the system tray.
        """
        self.root.deiconify()

    def exit_application(self):
        """
        Exits the application gracefully.
        """
        try:
            self.tray_icon.stop()
        except Exception:
            pass
        self.root.quit()

    def open_manage_zukey(self):
        """
        Opens the Manage Zukey window.
        """
        try:
            manage_zukey.open_manage_window(self.root)
            logging.info("Manage Zukey window opened.")
        except Exception as e:
            logging.error(f"Failed to open Manage Zukey window: {e}")
            self.update_notification("Failed to open Manage Zukey window.", "red")

    def open_general_dashboard_window(self):
        """
        Opens the General Dashboard window.
        """
        try:
            dashboard_window = ctk.CTkToplevel(self.root)
            dashboard_window.title("General Dashboard")
            dashboard_window.geometry("800x600")
            # Add dashboard widgets here
            logging.info("General Dashboard window opened.")
        except Exception as e:
            logging.error(f"Failed to open General Dashboard window: {e}")
            self.update_notification("Failed to open General Dashboard window.", "red")

    def show_failure_status(self, error_message):
        """
        Updates and displays the failure status label with the provided error message.

        Args:
            error_message (str): The error message to display.
        """
        self.failure_status_label.configure(text=error_message)
        self.failure_status_label.pack(fill="x", padx=60, pady=10)  # Ensure it's visible
        # Schedule to clear the label after 5 seconds
        self.root.after(5000, self.clear_failure_status_label)
    
    def clear_failure_status_label(self):
        """
        Clears the failure_status_label text.
        """
        self.failure_status_label.configure(text="")  # {{ edit_clear_failure_status_label }}

    def open_windows_hello_setup(self, key_name):  # {{ edit_open_windows_hello_setup }}
        """
        Opens the Windows Hello Security Key PIN and Reset dialog using template matching.
        
        Args:
            key_name (str): Name of the security key.
        """
        try:
            logging.info(f"Opening Windows Hello setup for security key: {key_name}")

            # Step 1: Open Sign-in Options via ms-settings
            subprocess.run("start ms-settings:signinoptions", shell=True, check=True)
            time.sleep(5)  # Wait for Settings to open

            # Step 2: Automate navigation to Security Key settings using template matching
            templates = [
                ("accounts_button.png", 0.8),
                ("sign_in_options_button.png", 0.8),
                ("security_key_button.png", 0.8),
                ("manage_button.png", 0.8)
            ]

            for template, confidence in templates:
                if not self.locate_and_click(template, confidence, wait_time=2):
                    logging.error(f"Failed to locate and click on {template}.")
                    self.update_notification(f"Error: Could not navigate to {template}.", "red")  # {{ replace_messagebox }}
                    return

            logging.info("Windows Hello Security Key dialog opened successfully.")
            self.update_notification(f"Windows Hello setup opened for: {key_name}", "green")  # {{ replace_messagebox_success }}
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to open Sign-in Options: {e}")
            self.update_notification(f"Error: Failed to open Sign-in Options.\n{e}", "red")  # {{ replace_messagebox_error }}
        except Exception as e:
            logging.error(f"An error occurred while opening Windows Hello setup: {e}")
            self.update_notification(f"Error: An unexpected error occurred.\n{e}", "red")  # {{ replace_messagebox_error }}
    
    def locate_and_click(self, template_path, confidence=0.8, wait_time=1):  # {{ edit_new }}
        """
        Locates an image on the screen and clicks on it using template matching.
    
        Args:
            template_path (str): Path to the image template for matching.
            confidence (float): Confidence level for template matching.
            wait_time (int): Time to wait after clicking.
    
        Returns:
            bool: True if the image was found and clicked, False otherwise.
        """
        try:
            logging.info(f"Looking for {template_path} on the screen...")
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                logging.error(f"Template image {template_path} not found.")
                return False
            screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= confidence)
            if len(loc[0]) > 0:
                top_left = (loc[1][0], loc[0][0])
                center_x = top_left[0] + template.shape[1] // 2
                center_y = top_left[1] + template.shape[0] // 2
                pyautogui.click(center_x, center_y)
                logging.info(f"Clicked on {template_path}.")
                time.sleep(wait_time)
                return True
            else:
                logging.warning(f"{template_path} not found on the screen.")
                return False
        except Exception as e:
            logging.error(f"Error locating or clicking {template_path}: {e}")
            return False

    def show_full_logs(self):  # {{ edit_43 }}
        """
        Opens a new window displaying the full logs from the log file in real time.
        """
        try:
            # Create a new window to display the logs
            log_window = ctk.CTkToplevel(self.root)
            log_window.title("Full Logs")
            log_window.geometry("800x600")
    
            # Add a textbox to display log contents
            self.full_log_textbox = ctk.CTkTextbox(log_window, wrap="word", width=800, height=600, state="disabled")
            self.full_log_textbox.pack(padx=10, pady=10, fill="both", expand=True)
    
            # Configure textbox highlighting
            self.configure_textbox_highlighting()  # {{ edit_48 }}
    
            # Start monitoring the log file in real time
            self.stop_log_monitor.clear()
            self.log_monitor_thread = threading.Thread(target=self.update_full_logs_realtime, daemon=True)
            self.log_monitor_thread.start()
    
            # Create a frame for buttons
            button_frame = ctk.CTkFrame(log_window)
            button_frame.pack(pady=10, fill="x")
    
            # Add Copy button
            copy_button = ctk.CTkButton(
                button_frame, 
                text="Copy", 
                command=self.copy_logs_to_clipboard,  # Function to copy logs
                width=100
            )
            copy_button.pack(side="left", padx=20)
    
            # Add Close button
            close_button = ctk.CTkButton(
                button_frame, 
                text="Close", 
                command=lambda: self.close_full_logs(log_window),
                width=100
            )
            close_button.pack(side="right", padx=20)
        except Exception as e:
            logging.error(f"Failed to open Full Logs window: {e}")
            self.update_notification("Failed to open Full Logs window.", "red")
    
    def update_full_logs_realtime(self):  # {{ edit_44 }}
        """
        Reads the log file in real time, filters out redundant logs, batches updates,
        and highlights important log entries.
        """
        log_file_path = 'link_opener.log'
        try:
            with open(log_file_path, 'r') as log_file:
                # Start reading from the end of the file
                log_file.seek(0, os.SEEK_END)
                while not self.stop_log_monitor.is_set():
                    line = log_file.readline()
                    if not line:
                        self.stop_log_monitor.wait(0.5)  # Event-driven waiting
                        continue
                    
                    stripped_line = line.strip()
                    
                    # {{ edit_49 }} Filter redundant logs
                    if stripped_line == self.previous_log_line:
                        continue
                    self.previous_log_line = stripped_line  # Update the last log line
    
                    # {{ edit_50 }} Add log to pending_logs for batch update
                    self.pending_logs.append(stripped_line)
                    if len(self.pending_logs) >= 10:  # Adjust batch size as needed
                        self.flush_logs_to_gui()
    
                # Flush any remaining logs before stopping
                self.flush_logs_to_gui()
    
        except Exception as e:
            logging.error(f"Failed to monitor log file in real time: {e}")
            self.update_notification("Failed to monitor log file in real time.", "red")

    def flush_logs_to_gui(self):  # {{ edit_51 }}
        """
        Appends pending logs to the GUI and clears the pending log list.
        Highlights lines containing specific keywords.
        """
        with self.flush_logs_lock:
            if not self.pending_logs:
                return
            self.log_textbox.configure(state="normal")
            for log_line in self.pending_logs:
                if "Detected keys" in log_line:
                    self.log_textbox.insert("end", log_line + "\n", "highlight")
                else:
                    self.log_textbox.insert("end", log_line + "\n")
            self.log_textbox.configure(state="disabled")
            self.log_textbox.see("end")  # Auto-scroll to the latest log
            self.pending_logs = []  # Clear the batch list

    def copy_logs_to_clipboard(self):  # {{ edit_46 }}
        """
        Copies the content of the full logs textbox to the clipboard.
        """
        try:
            self.full_log_textbox.configure(state="normal")
            log_content = self.full_log_textbox.get("1.0", "end").strip()
            self.full_log_textbox.configure(state="disabled")
            self.root.clipboard_clear()  # Clear the clipboard
            self.root.clipboard_append(log_content)  # Append the log content
            self.root.update()  # Update clipboard content
            self.update_notification("Logs copied to clipboard successfully!", "green")
        except Exception as e:
            logging.error(f"Failed to copy logs: {e}")
            self.update_notification("Failed to copy logs.", "red")

    def configure_textbox_highlighting(self):  # {{ edit_55 }}
        """
        Configures highlighting for specific keywords in the log textbox.
        """
        if hasattr(self, 'log_textbox') and self.log_textbox:
            self.log_textbox.tag_config("highlight", foreground="green")  # {{ edit_55 }}
            # Removed 'font' parameter as it's incompatible with CTkTextbox scaling
        else:
            logging.warning("log_textbox not initialized. Cannot configure highlighting.")

    def update_logs_in_main_thread(self, log_entry):  # {{ edit_49 }}
        """
        Appends a log entry to the log textbox in the main thread.
        """
        self.log_queue.put(log_entry)  # {{ edit_2 }}

    def flush_pending_logs(self):  # {{ edit_50 }}
        """
        Flushes pending logs to the GUI.
        """
        for log_entry in self.pending_logs:
            self.root.after(0, self.update_logs_in_main_thread, log_entry)
        self.pending_logs.clear()

    def setup_gui(self):  # {{ edit_54 }}
        """
        Sets up the GUI components.
        """
        # ... existing GUI setup code ...

        # Create the log textbox
        self.log_textbox = ctk.CTkTextbox(self.root, wrap="word", width=800, height=600, state="disabled")
        self.log_textbox.pack(padx=10, pady=10, fill="both", expand=True)

        # Configure textbox highlighting
        self.configure_textbox_highlighting()

        # Add the custom log handler
        self.add_textbox_log_handler()

        # ... rest of GUI setup ...

    def flush_logs_periodically(self):  # {{ edit_new }}
        """
        Periodically flushes pending logs to the GUI.
        """
        self.flush_logs_to_gui()
        self.root.after(1000, self.flush_logs_periodically)  # Schedule next flush

    def update_logs_periodically(self):  # {{ edit_new }}
        """
        Periodically checks the log queue and updates the GUI.
        """
        while not self.log_queue.empty():
            log_entry = self.log_queue.get()
            self.pending_logs.append(log_entry)
        self.root.after(1000, self.update_logs_periodically)  # Schedule next check

    def check_vpn_connection(self, test_url="http://internal.example.com"):  # {{ edit_new }}
        """
        Checks if the system is connected to the VPN by attempting to resolve a known internal URL.

        Args:
            test_url (str): A known internal URL that requires VPN access.

        Returns:
            bool: True if the VPN is connected, False otherwise.
        """
        try:
            # Extract hostname from the test URL
            hostname = test_url.split("://")[1].split("/")[0]
            # Attempt to resolve the hostname
            socket.gethostbyname(hostname)
            logging.info("VPN connection is active.")
            return True
        except socket.gaierror:
            logging.error("VPN connection is not active. Failed to resolve hostname.")
            return False

    def on_security_key_double_click(self, security_keys_list):  # {{ on_security_key_double_click }}
        """
        Handles double-click events on the security keys list.

        Args:
            security_keys_list (CTkTextbox): The textbox widget simulating the security key list.
        """
        try:
            # Get the cursor position within the textbox
            cursor_position = security_keys_list.index("@%d,%d" % (security_keys_list.winfo_pointerx(), security_keys_list.winfo_pointery()))
            line_start = cursor_position.split(".")[0]
            key_name = security_keys_list.get(f"{line_start}.0", f"{line_start}.end").strip()

            if key_name:
                logging.info(f"Double-clicked on security key: {key_name}")
                self.open_windows_hello_setup(key_name)
            else:
                logging.warning("Double-clicked but no valid key was found.")
                self.update_notification("No valid security key was selected.", "red")
        except Exception as e:
            logging.error(f"Error handling double-click event: {e}")
            self.update_notification(f"Error: An error occurred while handling the double-click event.\n{e}", "red")
    
    def reset_security_key(self):  # {{ edit_reset_security_key }}
        """
        Triggers the reset_security_key automation.
        """
        reset_thread = threading.Thread(target=reset_security_key, daemon=True)
        reset_thread.start()
        self.update_notification("Starting security key reset...", "green")  # Notify start

    def update_notification(self, message, color="green"):  # {{ update_notification }}
        """
        Updates the notification label in the GUI with the given message.
        
        Args:
            message (str): The notification message to display.
            color (str): The text color of the message ("green", "red", etc.).
        """
        if hasattr(self, 'notification_label') and self.notification_label:
            self.root.after(0, lambda: self.notification_label.configure(text=message, text_color=color))
            self.root.after(0, lambda: self.notification_label.pack(fill="x", padx=10, pady=5))

    @staticmethod
    def update_notification_static(message, color="green"):  # {{ update_notification_static }}
        """
        Static method to update the notification label from outside the class.
        """
        instance = QuickLinksApp.get_instance()  # {{ use_get_instance }}
        if instance:
            instance.update_notification(message, color)

    def click_animation(self):
        """
        Handles the click animation.
        """
        # Implement your click animation logic here
        logging.info("click_animation method called.")
        pass  # Replace with actual animation code

    def update(self):
        """
        Updates the GUI components or performs scheduled updates.
        """
        # Implement your update logic here
        logging.info("Update method called.")
        # Example: Refresh certain GUI elements
        pass  # Replace with actual update code

    def check_dpi_scaling(self):
        """
        Checks and handles DPI scaling settings for the application.
        """
        # Implement DPI scaling logic here
        logging.info("check_dpi_scaling method called.")
        # Example: Adjust GUI scaling based on system DPI settings
        pass  # Replace with actual DPI scaling code

    def open_scanner_apw(self):
        """
        Opens the Scanner APW functionality.
        """
        try:
            # Logic for Scanner APW
            logging.info("Scanner APW button clicked.")
            self.update_notification("Scanner APW feature is under development!", "green")
        except Exception as e:
            logging.error(f"Failed to open Scanner APW: {e}")
            self.update_notification(f"Error opening Scanner APW: {e}", "red")

class TextBoxHandler(logging.Handler):
    """
    Custom logging handler that writes log records to a queue.
    """
    def __init__(self, log_queue):  # {{ edit_1 }}
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        log_entry = self.format(record)
        self.log_queue.put(log_entry)  # {{ edit_2 }}

def check_dependencies():
    """
    Verifies that all required dependencies are installed.
    
    Raises:
        EnvironmentError: If any dependencies are missing.
    """
    missing = []
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        missing.append("Playwright")
    
    try:
        import hid
    except ImportError:
        missing.append("hidapi")
    
    if missing:
        raise EnvironmentError(f"Missing dependencies: {', '.join(missing)}")

def main():  # {{ edit_main_function }}
    """
    Main entry point of the application.
    Checks VPN connectivity and dependencies before launching the main application.
    """
    try:
        check_dependencies()  # Ensure all dependencies are installed
    except EnvironmentError as e:
        logging.error(e)
        sys.exit(1)  # Exit the application if dependencies are missing
    
    if not is_vpn_connected():
        show_vpn_warning()
        return

    try:
        root = ctk.CTk()
        app = QuickLinksApp(root)
        root.mainloop()
    except Exception as e:
        logging.exception("An unhandled exception occurred in the main loop.")
        if QuickLinksApp.get_instance():
            QuickLinksApp.get_instance().update_notification("An error occurred.", "red")  # Use app instead of self

if __name__ == "__main__":
    main()
