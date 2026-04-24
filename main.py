"""
🤖 MusQuira —  AI Voice Assistant
Run this file to launch.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui import MusQuiraApp
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    app  = MusQuiraApp(root)
    root.mainloop()
