"""
Windowless launcher for Windows.

Double-click this file (or make a shortcut to it) to start Auris in the tray
with no console window. `.pyw` files are run by pythonw.exe on Windows.
"""

from auris.app import main

if __name__ == "__main__":
    main()
