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
from matplotlib import path

import numpy as np
from matplotlib.widgets import LassoSelector

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

composite = fits.open("/home/marcus/Desktop/dr_suvi-l2-ci195_g16_s20200701T000000Z_e20200701T000400Z_v1-0-1.fits")
thmap = fits.open("/home/marcus/Desktop/dr_suvi-l2-thmap_g16_s20200701T000000Z_e20200701T000400Z_v1-0-2.fits")


class AnnotationWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()

        self.fig = Figure(figsize=(10, 5))
        static_canvas = FigureCanvas(self.fig)
        layout.addWidget(static_canvas)
        #self.addToolBar(NavigationToolbar(static_canvas, self))

        self.axs = static_canvas.figure.subplots(ncols=2, sharex=True, sharey=True)
        self.preview_axesimage = self.axs[0].imshow(composite[1].data, vmin=0, vmax=1)
        self.thmap_axesimage = self.axs[1].imshow(thmap[0].data, vmin=0, vmax=9)  # TODO: rename with better name
        self.axs[0].set_axis_off()
        self.axs[1].set_axis_off()

        toolbar = NavigationToolbar(static_canvas, self)
        layout.addWidget(toolbar)
        self.setLayout(layout)

        # add selection layer for lasso
        self.selection_array = thmap[0].data.copy()
        self.history = []  # the history of regions drawn for undo feature, just a list of (m,n) thematic maps
        self.shape = (1280, 1280)  # TODO: replace with dynamic detection
        self.pix = np.arange(self.shape[0])  # assumes square image
        xv, yv = np.meshgrid(self.pix, self.pix)
        self.pix = np.vstack((xv.flatten(), yv.flatten())).T

        lineprops = dict(color="red", linewidth=2)
        self.lasso = LassoSelector(self.axs[0], self.onlasso, lineprops=lineprops)

    def onlasso(self, verts):
        """
        Main function to control the action of the lasso, allows user to draw on data image and adjust thematic map
        :param verts: the vertices selected by the lasso
        :return: nothin, but update the selection array so lassoed region now has the selected theme, redraws canvas
        """
        p = path.Path(verts)
        ind = p.contains_points(self.pix, radius=1)
        self.history.append(self.selection_array.copy())
        self.selection_array = self.updateArray(self.selection_array,
                                                ind,
                                                0)
        self.thmap_axesimage.set_data(self.selection_array)
        self.fig.canvas.draw_idle()

    def updateArray(self, array, indices, value):
        """
        updates array so that pixels at indices take on value
        :param array: (m,n) array to adjust
        :param indices: flattened image indices to change value
        :param value: new value to assign
        :return: the changed (m,n) array
        """
        lin = np.arange(array.size)
        new_array = array.flatten()
        new_array[lin[indices]] = value
        return new_array.reshape(array.shape)

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)

        self._setup_menubar()

        layout = QtWidgets.QVBoxLayout(self._main)
        annotator = AnnotationWidget()
        layout.addWidget(annotator)

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
        self.editMenu = self.mainMenu.addMenu("Edit")

        # File Menu
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

        # Edit Menu
        undoEdit = QAction("&Undo Edit", self)
        undoEdit.setShortcut("Ctrl+Z")
        undoEdit.setStatusTip('Undo a change on the thematic map')
        undoEdit.triggered.connect(lambda: print("Attempting to undo an edit"))  # TODO: implement undo edit
        self.editMenu.addAction(undoEdit)

    def file_open(self):
        # TODO: actually update the thematic map
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