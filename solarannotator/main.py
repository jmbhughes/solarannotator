#!/usr/bin/env python3

from solarannotator.gui import ApplicationWindow
from PyQt5 import QtWidgets
import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description='Annotate solar images with labels')
    parser.add_argument('--config', help='a configuration file to load',
                        default=os.path.join(sys.prefix, 'solarannotator/default.json'))
    args = parser.parse_args()

    # Check whether there is already a running QApplication (e.g., if running
    # from an IDE).
    qapp = QtWidgets.QApplication.instance()
    if not qapp:
        qapp = QtWidgets.QApplication(sys.argv)

    app = ApplicationWindow(args.config)
    app.show()
    app.activateWindow()
    app.raise_()
    qapp.exec_()


if __name__ == "__main__":
    main()
