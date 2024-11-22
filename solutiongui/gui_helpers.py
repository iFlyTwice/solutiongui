import customtkinter as ctk
import logging
import manage_zukey  # Add this import
# Add more GUI-related imports if necessary

def create_window_controls(root, on_closing_callback, on_minimize_callback):
    """
    Creates and packs the window control buttons (Minimize and Exit) at the top right.
    Currently not adding buttons to the UI.
    """
    pass  # No buttons will be created

def create_button_frame(root, links, open_link_callback, handle_midway_access_callback, open_manage_zukey_callback, open_general_dashboard_callback):
    """
    Creates and packs the button frame with link buttons.
    """
    button_frame = ctk.CTkFrame(master=root)
    button_frame.pack(pady=10, padx=20, fill="x", expand=False)

    for name, url in links.items():
        if name == "TICKETS LINK":
            continue  # Skip creating the "Tickets Link" button
        if name == "MIDWAY ACCESS":
            button = ctk.CTkButton(
                master=button_frame,
                text=name,
                command=handle_midway_access_callback,
                width=300,
                height=40
            )
        elif name == "GENERAL DASHBOARD":
            button = ctk.CTkButton(
                master=button_frame,
                text=name,
                command=open_general_dashboard_callback,  # Use the new callback
                width=300,
                height=40
            )
        elif name == "REPORTS":
            button = ctk.CTkButton(
                master=button_frame,
                text="CREATE TICKET",
                command=lambda url=url, name=name: open_link_callback(url, name),
                width=300,
                height=40
            )
        else:
            button = ctk.CTkButton(
                master=button_frame,
                text=name,
                command=lambda url=url, name=name: open_link_callback(url, name),
                width=300,
                height=40
            )
        button.pack(pady=5)

    # Add the "Manage Zukey" button
    manage_zukey_button = ctk.CTkButton(
        master=button_frame,
        text="Manage Zukey",
        command=lambda: manage_zukey.open_manage_window(root),  # Updated callback
        width=300,
        height=40
    )
    manage_zukey_button.pack(pady=5)

def create_credentials_frame(root, toggle_pin_visibility_callback):
    """
    Creates and packs the credentials frame with username and PIN entries.

    Args:
        root (ctk.CTk): The main window instance.
        toggle_pin_visibility_callback (function): Callback to toggle PIN visibility.

    Returns:
        tuple: (username_entry, pin_entry, show_pin_button)
    """
    credentials_frame = ctk.CTkFrame(master=root)
    credentials_frame.pack(pady=10, padx=20, fill="x", expand=False)

    # Username label and entry
    username_label = ctk.CTkLabel(master=credentials_frame, text="Username:")
    username_label.pack(side="left", padx=10, pady=5)
    username_entry = ctk.CTkEntry(master=credentials_frame, width=200)
    username_entry.pack(side="left", padx=10, pady=5)

    # PIN label and entry
    pin_label = ctk.CTkLabel(master=credentials_frame, text="PIN:")
    pin_label.pack(side="left", padx=10, pady=5)
    pin_entry = ctk.CTkEntry(master=credentials_frame, width=200, show="*")
    pin_entry.pack(side="left", padx=10, pady=5)

    # Show/Hide button for PIN entry
    show_pin_button = ctk.CTkButton(
        master=credentials_frame,
        text="Show",
        width=60,
        height=30,
        command=toggle_pin_visibility_callback
    )
    show_pin_button.pack(side="left", padx=10, pady=5)

    return username_entry, pin_entry, show_pin_button

def toggle_pin_visibility(pin_entry, show_pin_button, pin_visible):
    """
    Toggles the visibility of the PIN entry.

    Args:
        pin_entry (ctk.CTkEntry): The PIN entry widget.
        show_pin_button (ctk.CTkButton): The show/hide button widget.
        pin_visible (bool): Current visibility state of the PIN.

    Returns:
        bool: Updated visibility state of the PIN.
    """
    if pin_visible:
        pin_entry.configure(show="*")
        show_pin_button.configure(text="Show")
        return False
    else:
        pin_entry.configure(show="")
        show_pin_button.configure(text="Hide")
        return True

def create_security_keys_list(root, on_key_double_click):
    """
    Creates and packs the security keys list view using CTkTextbox.

    Args:
        root (ctk.CTk): The main window instance.
        on_key_double_click (function): Callback function to handle double-click events.

    Returns:
        ctk.CTkTextbox: The textbox widget simulating a listbox for security keys.
    """
    security_keys_frame = ctk.CTkFrame(master=root)
    security_keys_frame.pack(pady=20, padx=10, fill="y", side="right", expand=False)

    security_keys_label = ctk.CTkLabel(master=security_keys_frame, text="Connected Security Keys:")
    security_keys_label.pack(pady=5)

    # Create CTkTextbox to display security keys
    security_keys_list = ctk.CTkTextbox(master=security_keys_frame, width=200, height=300)
    security_keys_list.pack(pady=5)

    # Bind double-click event to the callback function
    security_keys_list.bind("<Double-Button-1>", lambda event: on_key_double_click(security_keys_list))

    return security_keys_list

def update_security_keys_list(security_keys_list, keys):
    """
    Updates the security keys list view with the current connected keys.

    Args:
        security_keys_list (ctk.CTkTextbox): The textbox widget to update.
        keys (list): List of connected security keys.
    """
    try:
        security_keys_list.configure(state="normal")
        security_keys_list.delete("1.0", "end")  # Clear the list
        for key in keys:
            security_keys_list.insert("end", f"{key}\n")  # Add each key
        security_keys_list.configure(state="disabled")
        security_keys_list.see("end")  # Scroll to the bottom
    except Exception as e:
        logging.exception("Failed to update security keys list.")

def set_window_size(root, width=768, height=958):
    """
    Sets the window size and centers it on the screen.
    """
    # Calculate position to center the window
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    position_x = (screen_width - width) // 2
    position_y = (screen_height - height) // 2

    # Set the geometry of the window
    root.geometry(f"{width}x{height}+{position_x}+{position_y}")