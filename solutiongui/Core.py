import customtkinter as ctk 
import logging
from solutiongui.gui.gui_helpers import create_credentials_frame  # Converted to absolute import

def main():
    # Your main application logic
    root = ctk.CTk()
    app = QuickLinksApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
