# -*- coding: utf-8 -*-


import sys
from pathlib import Path


_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from avtomoyka.ui.kiosk_app import KioskApp


def main():
    KioskApp().run()


if __name__ == "__main__":
    main()
