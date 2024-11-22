import customtkinter as ctk
import json
import os
import logging

class SettingsWindow:
    def __init__(self, parent, on_settings_saved_callback):
        """
        Initializes the settings window.

        Args:
            parent: Parent window.
            on_settings_saved_callback (function, optional): Callback to execute after settings are saved.
        """
        self.parent = parent
        self.on_settings_saved_callback = on_settings_saved_callback
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Settings")
        self.window.geometry("400x300")
        self.window.resizable(False, False)

        # Create tabs
        self.tabs = ctk.CTkTabview(self.window)
        self.tabs.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

        # Add tabs
        self.add_general_tab()
        self.add_playwright_tab()

        # Save and Cancel buttons using grid
        button_frame = ctk.CTkFrame(self.window)
        button_frame.grid(row=1, column=0, pady=10, sticky="e", padx=10)

        self.save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_settings)
        self.save_button.grid(row=0, column=0, padx=5)

        self.cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=self.window.destroy)
        self.cancel_button.grid(row=0, column=1, padx=5)

        # Load existing settings
        self.settings = self.load_settings()

    def add_general_tab(self):
        """
        Adds the General tab to the settings window.
        """
        self.general_tab = self.tabs.add("General")

        # Appearance Mode
        appearance_label = ctk.CTkLabel(self.general_tab, text="Appearance Mode:")
        appearance_label.pack(pady=10)

        self.appearance_mode = ctk.StringVar(value=self.settings.get("appearance_mode", "dark"))
        self.appearance_menu = ctk.CTkOptionMenu(
            master=self.general_tab,
            values=["light", "dark", "system"],
            variable=self.appearance_mode
        )
        self.appearance_menu.pack(pady=10)

        # VPN URL
        vpn_url_label = ctk.CTkLabel(self.general_tab, text="VPN Check URL:")
        vpn_url_label.pack(pady=5)

        self.vpn_url_entry = ctk.CTkEntry(self.general_tab)
        self.vpn_url_entry.pack(pady=5, fill="x")
        self.vpn_url_entry.insert(0, self.settings.get("vpn_url", ""))

    def add_playwright_tab(self):
        """
        Adds the Playwright tab to the settings window.
        """
        self.playwright_tab = self.tabs.add("Playwright")

        # Browser Selection
        browser_label = ctk.CTkLabel(self.playwright_tab, text="Browser Type:")
        browser_label.pack(pady=5)

        self.browser_type = ctk.StringVar(value=self.settings.get("browser_type", "chromium"))
        chromium_button = ctk.CTkRadioButton(
            self.playwright_tab, text="Chromium", variable=self.browser_type, value="chromium"
        )
        chromium_button.pack(pady=5)

        firefox_button = ctk.CTkRadioButton(
            self.playwright_tab, text="Firefox", variable=self.browser_type, value="firefox"
        )
        firefox_button.pack(pady=5)

        # Headless Mode
        self.headless_mode = ctk.BooleanVar(value=self.settings.get("headless_mode", False))
        headless_checkbox = ctk.CTkCheckBox(
            self.playwright_tab, text="Enable Headless Mode", variable=self.headless_mode
        )
        headless_checkbox.pack(pady=5)

    def load_settings(self):
        """
        Loads settings from a JSON file.
        """
        config_file = "gui_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    settings = json.load(f)
                return settings
            except Exception as e:
                logging.warning(f"Failed to load settings: {e}")
        return {}

    def save_settings(self):
        """
        Saves settings to the configuration file and notifies the parent.
        """
        try:
            updated_settings = {
                "appearance_mode": self.appearance_mode.get(),
                "vpn_url": self.vpn_url_entry.get(),
                "browser_type": self.browser_type.get(),
                "headless_mode": self.headless_mode.get()
            }
            self.on_settings_saved_callback(updated_settings)
            self.window.destroy()
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
            # Optionally, you can add a messagebox here to inform the user 