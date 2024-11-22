import sys
import os
import unittest
from core.gui_helpers import set_window_size

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'FutureUpdate')))

class TestGuiHelpers(unittest.TestCase):
    def test_set_window_size(self):
        import tkinter as tk
        root = tk.Tk()
        set_window_size(root)
        
        # Update the root window to initialize the layout
        root.update()  # Ensures the geometry is calculated
        
        expected_width = int(root.winfo_screenwidth() * 0.6)
        expected_height = int(root.winfo_screenheight() * 0.6)
        
        self.assertEqual(root.winfo_width(), expected_width)
        self.assertEqual(root.winfo_height(), expected_height)
        root.destroy()

if __name__ == '__main__':
    unittest.main() 