import customtkinter as ctk
import logging
from tkinter import messagebox
import threading
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set theming preferences
ctk.set_appearance_mode("dark")  # Options: "light", "dark", "system"
ctk.set_default_color_theme("green")

class ManageZukeyWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Manage Zukey")
        self.window.geometry("800x600")
        
        # Make the window topmost
        self.window.attributes("-topmost", True)
        
        # Configure grid layout for responsiveness
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
        # Create Notebook for tabs
        self.notebook = ctk.CTkTabview(self.window)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Add tabs
        self.create_pin_management_tab()
        self.create_credential_management_tab()
        
        # Status Bar
        self.status_bar = ctk.CTkLabel(self.window, text="Ready", anchor="w")
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,10))
        
        logging.info("Manage Zukey window initialized.")
        
    def create_pin_management_tab(self):
        self.notebook.add("PIN Management")
        pin_tab = self.notebook.tab("PIN Management")
        
        # Set PIN Frame
        set_pin_frame = ctk.CTkFrame(pin_tab)
        set_pin_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        pin_tab.grid_rowconfigure(0, weight=1)
        pin_tab.grid_columnconfigure(0, weight=1)
        
        set_pin_label = ctk.CTkLabel(set_pin_frame, text="Set or Change PIN:")
        set_pin_label.grid(row=0, column=0, pady=5, sticky="w")
        
        self.new_pin_entry = ctk.CTkEntry(set_pin_frame, show="*")
        self.new_pin_entry.grid(row=1, column=0, pady=5, sticky="ew")
        set_pin_frame.grid_columnconfigure(0, weight=1)
        
        self.set_pin_button = ctk.CTkButton(set_pin_frame, text="Set PIN", command=self.set_pin)
        self.set_pin_button.grid(row=2, column=0, pady=5, sticky="e")
        
        # Verify PIN Frame
        verify_pin_frame = ctk.CTkFrame(pin_tab)
        verify_pin_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        verify_pin_label = ctk.CTkLabel(verify_pin_frame, text="Verify PIN:")
        verify_pin_label.grid(row=0, column=0, pady=5, sticky="w")
        
        self.verify_pin_entry = ctk.CTkEntry(verify_pin_frame, show="*")
        self.verify_pin_entry.grid(row=1, column=0, pady=5, sticky="ew")
        verify_pin_frame.grid_columnconfigure(0, weight=1)
        
        self.verify_pin_button = ctk.CTkButton(verify_pin_frame, text="Verify PIN", command=self.verify_pin)
        self.verify_pin_button.grid(row=2, column=0, pady=5, sticky="e")
        
        # Reset PIN Frame
        reset_pin_frame = ctk.CTkFrame(pin_tab)
        reset_pin_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        reset_pin_label = ctk.CTkLabel(reset_pin_frame, text="Reset PIN:")
        reset_pin_label.grid(row=0, column=0, pady=5, sticky="w")
        
        reset_pin_button = ctk.CTkButton(reset_pin_frame, text="Reset PIN", command=self.reset_pin)
        reset_pin_button.grid(row=1, column=0, pady=5, sticky="e")
        
        # Delete Credentials Frame
        delete_cred_frame = ctk.CTkFrame(pin_tab)
        delete_cred_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        
        delete_cred_label = ctk.CTkLabel(delete_cred_frame, text="Delete Credential:")
        delete_cred_label.grid(row=0, column=0, pady=5, sticky="w")
        
        self.delete_cred_entry = ctk.CTkEntry(delete_cred_frame)
        self.delete_cred_entry.grid(row=1, column=0, pady=5, sticky="ew")
        delete_cred_frame.grid_columnconfigure(0, weight=1)
        
        self.delete_cred_button = ctk.CTkButton(delete_cred_frame, text="Delete Credential", command=self.delete_credential)
        self.delete_cred_button.grid(row=2, column=0, pady=5, sticky="e")
        
    def create_credential_management_tab(self):
        self.notebook.add("Credential Management")
        cred_tab = self.notebook.tab("Credential Management")
        
        # View Credentials Frame
        view_cred_frame = ctk.CTkFrame(cred_tab)
        view_cred_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        cred_tab.grid_rowconfigure(0, weight=1)
        cred_tab.grid_columnconfigure(0, weight=1)
        
        view_cred_label = ctk.CTkLabel(view_cred_frame, text="Resident Credentials:")
        view_cred_label.grid(row=0, column=0, pady=5, sticky="w")
        
        self.credentials_listbox = ctk.CTkTextbox(view_cred_frame, width=400, height=300, state="disabled")
        self.credentials_listbox.grid(row=1, column=0, pady=5, sticky="nsew")
        view_cred_frame.grid_rowconfigure(1, weight=1)
        view_cred_frame.grid_columnconfigure(0, weight=1)
        
        view_cred_button = ctk.CTkButton(view_cred_frame, text="Refresh Credentials", command=self.view_credentials)
        view_cred_button.grid(row=2, column=0, pady=5, sticky="e")
        
        # Delete Credentials Frame
        delete_cred_frame = ctk.CTkFrame(cred_tab)
        delete_cred_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        delete_cred_label = ctk.CTkLabel(delete_cred_frame, text="Delete Credential:")
        delete_cred_label.grid(row=0, column=0, pady=5, sticky="w")
        
        self.delete_cred_entry = ctk.CTkEntry(delete_cred_frame)
        self.delete_cred_entry.grid(row=1, column=0, pady=5, sticky="ew")
        delete_cred_frame.grid_columnconfigure(0, weight=1)
        
        self.delete_cred_button = ctk.CTkButton(delete_cred_frame, text="Delete Credential", command=self.delete_credential)
        self.delete_cred_button.grid(row=2, column=0, pady=5, sticky="e")
        
    def set_pin(self):
        new_pin = self.new_pin_entry.get()
        if not new_pin:
            self.update_status("Set PIN failed: No PIN entered.")
            messagebox.showwarning("Input Error", "Please enter a new PIN.")
            return
        # Disable the button to prevent multiple clicks
        self.set_pin_button.config(state="disabled")
        try:
            # Implement the logic to set or change the PIN
            # This might involve interacting with the HID device
            logging.info("Setting new PIN.")  # Ensure all logs use appropriate levels
            self.update_status("Setting new PIN...")
            messagebox.showinfo("Success", "PIN has been set successfully.")
            self.new_pin_entry.delete(0, 'end')
            self.update_status("PIN set successfully.")
        finally:
            # Re-enable the button regardless of success or failure
            self.set_pin_button.config(state="normal")
        
    def verify_pin(self):
        pin = self.verify_pin_entry.get()
        if not pin:
            self.update_status("Verify PIN failed: No PIN entered.")
            messagebox.showwarning("Input Error", "Please enter the PIN to verify.")
            return
        # Disable the button to prevent multiple clicks
        self.verify_pin_button.config(state="disabled")
        try:
            # Implement the logic to verify the PIN
            # This might involve interacting with the HID device
            logging.info("Verifying PIN.")  # Removed logging of the actual PIN for security
            self.update_status("Verifying PIN...")
            # Placeholder for verification result
            is_valid = True  # Replace with actual verification
            if is_valid:
                messagebox.showinfo("Success", "PIN verification successful.")
                self.update_status("PIN verification successful.")
            else:
                messagebox.showerror("Failure", "PIN verification failed.")
                self.update_status("PIN verification failed.")
            self.verify_pin_entry.delete(0, 'end')
        finally:
            # Re-enable the button regardless of success or failure
            self.verify_pin_button.config(state="normal")
        
    def reset_pin(self):
        # Implement the logic to reset the PIN
        # This might involve resetting the FIDO2 application on the key
        logging.info("Resetting PIN.")
        messagebox.showinfo("Success", "PIN has been reset successfully.")
        
    def view_credentials(self):
        # Implement the logic to view resident credentials stored on the key
        # This might involve interacting with the HID device
        logging.info("Fetching resident credentials.")
        # Placeholder for credentials
        credentials = ["Credential 1", "Credential 2", "Credential 3"]  # Replace with actual credentials
        self.credentials_listbox.configure(state="normal")
        self.credentials_listbox.delete("1.0", "end")
        for cred in credentials:
            self.credentials_listbox.insert("end", f"{cred}\n")
        self.credentials_listbox.configure(state="disabled")
        
    def delete_credential(self):
        cred_to_delete = self.delete_cred_entry.get()
        if not cred_to_delete:
            self.update_status("Delete Credential failed: No credential entered.")
            messagebox.showwarning("Input Error", "Please enter the credential to delete.")
            return
        # Disable the button to prevent multiple clicks
        self.delete_cred_button.config(state="disabled")
        try:
            # Implement the logic to delete the specified credential
            # This might involve interacting with the HID device
            logging.info(f"Deleting credential: {cred_to_delete}")
            self.update_status(f"Deleting credential: {cred_to_delete}...")
            messagebox.showinfo("Success", f"Credential '{cred_to_delete}' has been deleted successfully.")
            self.delete_cred_entry.delete(0, 'end')
            self.update_status("Credential deleted successfully.")
        finally:
            # Re-enable the button regardless of success or failure
            self.delete_cred_button.config(state="normal")
        
    def update_status(self, message):
        self.status_bar.configure(text=message) 

def open_manage_window(root):
    """
    Opens the Manage Zukey window.

    Args:
        root (ctk.CTk): The main window instance.
    """
    ManageZukeyWindow(root)

def main():
    # Example function to demonstrate environment variable usage
    username = os.getenv("USERNAME")
    pin = os.getenv("PIN")
    logging.info(f"Manage Zukey initialized with USERNAME: {username}")

if __name__ == "__main__":
    main() 