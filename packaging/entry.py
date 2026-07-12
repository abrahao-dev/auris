"""PyInstaller entry point. Delegates to the package's argparse main so the
frozen binary still supports --version / --cli / --selftest, and defaults to the
tray app when launched with no arguments."""

from auris.__main__ import main

if __name__ == "__main__":
    main()
