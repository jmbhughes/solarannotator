"""
===============
Embedding in Qt
===============

Simple Qt application embedding Matplotlib canvases.  This program will work
equally well using Qt4 and Qt5.  Either version of Qt can be selected (for
example) by setting the ``MPLBACKEND`` environment variable to "Qt4Agg" or
"Qt5Agg", or by first importing the desired version of PyQt.
"""

import sys
import PyQt5
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtWidgets import QWidget, QLabel, QAction, QTabWidget, QPushButton, QFileDialog
from PyQt5.QtGui import QIcon

from astropy.io import fits

import numpy as np

from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
if is_pyqt5():
    from matplotlib.backends.backend_qt5agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
else:
    from matplotlib.backends.backend_qt4agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)

        self._setup_menubar()

        layout = QtWidgets.QVBoxLayout(self._main)

        static_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        layout.addWidget(static_canvas)
        self.addToolBar(NavigationToolbar(static_canvas, self))

        self._static_ax = static_canvas.figure.subplots(ncols=2)
        t = np.linspace(0, 10, 501)
        self._static_ax[0].plot(t, np.tan(t), ".")

        control_layout = QtWidgets.QHBoxLayout()
        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.resize(300, 200)

        # Add tabs
        self.tabs.addTab(self.tab1, "Tab 1")
        self.tabs.addTab(self.tab2, "Tab 2")

        # Create first tab
        self.tab1.layout = QtWidgets.QVBoxLayout(self)
        self.pushButton1 = QPushButton("PyQt5 button")
        self.tab1.layout.addWidget(self.pushButton1)
        self.tab1.setLayout(self.tab1.layout)

        # Add tabs to widget
        control_layout.addWidget(self.tabs)

        label1 = QLabel()
        label2 = QLabel()
        label1.setText("Label1")
        label2.setText("Label2")
        control_layout.addWidget(label1)
        control_layout.addWidget(label2)
        layout.addLayout(control_layout)

    def _setup_menubar(self):
        self.mainMenu = self.menuBar()
        self.fileMenu = self.mainMenu.addMenu('File')

        newButton = QAction("New", self)
        newButton.setShortcut('Ctrl+N')
        newButton.setStatusTip('Create new thematic map')
        newButton.triggered.connect(lambda: print("New clicked"))
        self.fileMenu.addAction(newButton)

        openFile = QAction("&Open File", self)
        openFile.setShortcut("Ctrl+O")
        openFile.setStatusTip('Open File')
        openFile.triggered.connect(self.file_open)
        self.fileMenu.addAction(openFile)

        saveFile = QAction("&Save File", self)
        saveFile.setShortcut("Ctrl+S")
        saveFile.setStatusTip('Save File')
        saveFile.triggered.connect(self.file_save)
        self.fileMenu.addAction(saveFile)

        exitButton = QAction('Exit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.setStatusTip('Exit application')
        exitButton.triggered.connect(self.close)
        self.fileMenu.addAction(exitButton)

    def file_open(self):
        dlg = QFileDialog()
        fname = dlg.getOpenFileName(None, "Open Thematic Map", "", "FITS files (*.fits)")
        if fname != ('', ''):
            with fits.open(fname[0]) as hdulist:
                data = hdulist[0].data
                print(data)

    def file_save(self):
        dlg = QFileDialog()
        fname = dlg.getSaveFileName(None, "Open Thematic Map", "", "FITS files (*.fits)")
        if fname != ('', ''):
           pass # TODO : actually save a thematic map


if __name__ == "__main__":
    # Check whether there is already a running QApplication (e.g., if running
    # from an IDE).
    qapp = QtWidgets.QApplication.instance()
    if not qapp:
        qapp = QtWidgets.QApplication(sys.argv)

    app = ApplicationWindow()
    app.show()
    app.activateWindow()
    app.raise_()
    qapp.exec_()