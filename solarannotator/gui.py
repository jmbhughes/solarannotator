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
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget, QLabel, QAction, QTabWidget, QPushButton, QFileDialog, QRadioButton, QMessageBox
from PyQt5.QtGui import QIcon
from datetime import datetime
from astropy.io import fits
from matplotlib import path

import numpy as np
from matplotlib.widgets import LassoSelector
from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
if is_pyqt5():  # TODO: update to use the non-deprecated approach
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

from .config import Config
from .io import ThematicMap, ImageSet


class AnnotationWidget(QtWidgets.QWidget):
    def __init__(self, config):
        super().__init__()
        self.composites = None
        self.current_theme_index = 0

        self.preview_data = np.zeros((1280, 1280))
        self.thmap_data = np.zeros((1280, 1280))
        self.thmap = ThematicMap(self.thmap_data, {'DATE-OBS': str(datetime.today())}, config.solar_class_name)

        layout = QtWidgets.QVBoxLayout()

        self.fig = Figure(figsize=(10, 5))
        static_canvas = FigureCanvas(self.fig)
        layout.addWidget(static_canvas)

        self.axs = static_canvas.figure.subplots(ncols=2, sharex=True, sharey=True)
        self.preview_axesimage = self.axs[0].imshow(self.preview_data, vmin=0, vmax=5, cmap='gray')
        self.thmap_axesimage = self.axs[1].imshow(self.thmap_data,
                                                  vmin=0, vmax=config.max_index, cmap=config.solar_cmap)
        self.axs[0].set_axis_off()
        self.axs[1].set_axis_off()
        self.axs[0].set_title("Preview")
        self.axs[1].set_title("Thematic Map")

        toolbar = NavigationToolbar(static_canvas, self)
        layout.addWidget(toolbar)
        self.setLayout(layout)

        # add selection layer for lasso
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
        self.thmap_data = self.updateArray(self.thmap_data,
                                                ind,
                                                self.current_theme_index)
        self.thmap_axesimage.set_data(self.thmap_data)
        self.fig.canvas.draw_idle()
        self.thmap.data = self.thmap_data

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

    def loadThematicMap(self, thmap):
        self.thmap = thmap
        self.thmap_data = thmap.data
        self.thmap_axesimage.set_data(self.thmap_data)
        self.composites = ImageSet.retrieve(thmap.date_obs)
        self.preview_axesimage.set_data(self.composites[195].data)
        self.fig.canvas.draw_idle()


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self, config_path):
        super().__init__()
        self.config = Config(config_path)
        self.output_fn = None
        self.initUI()

    def initUI(self):
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)

        self._setup_menubar()

        layout = QtWidgets.QVBoxLayout(self._main)
        self.annotator = AnnotationWidget(self.config)
        layout.addWidget(self.annotator)

        self._setup_control_layout()
        layout.addLayout(self.control_layout)

    def _setup_control_layout(self):
        self.control_layout = QtWidgets.QHBoxLayout()
        self._setup_preview_control_panel()
        self._setup_theme_radio_buttons()

    def _setup_preview_control_panel(self):
        # Left control panel
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.resize(300, 200)

        # Add tabs
        self.tabs.addTab(self.tab1, "Single")
        self.tabs.addTab(self.tab2, "Three-color")

        # Create first tab
        self.tab1.layout = QtWidgets.QVBoxLayout(self)
        self.pushButton1 = QPushButton("PyQt5 button")
        self.tab1.layout.addWidget(self.pushButton1)
        self.tab1.setLayout(self.tab1.layout)
        self.control_layout.addWidget(self.tabs)

    def _setup_theme_radio_buttons(self):
        theme_selection_layout = QtWidgets.QVBoxLayout()
        radiobuttons = dict()

        # add unlabelled button
        radiobuttons['unlabeled'] = QRadioButton("unlabeled")
        radiobuttons['unlabeled'].index = 0
        radiobuttons['unlabeled'].setChecked(True)
        radiobuttons['unlabeled'].toggled.connect(self.onClickedRadioButton)
        theme_selection_layout.addWidget(radiobuttons['unlabeled'])

        # add rest of theme buttons
        for theme, index in self.config.solar_class_index.items():
            radiobuttons[theme] = QRadioButton(theme)
            radiobuttons[theme].index = index
            radiobuttons[theme].toggled.connect(self.onClickedRadioButton)
            theme_selection_layout.addWidget(radiobuttons[theme])
        self.control_layout.addLayout(theme_selection_layout)

    def onClickedRadioButton(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            self.annotator.current_theme_index = radioButton.index

    def _setup_menubar(self):
        self.mainMenu = self.menuBar()
        self.fileMenu = self.mainMenu.addMenu('File')

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

        saveFile = QAction("&Save", self)
        saveFile.setShortcut("Ctrl+S")
        saveFile.setStatusTip('Save File')
        saveFile.triggered.connect(self.file_save)
        self.fileMenu.addAction(saveFile)
        self.fileMenu.addSeparator()

        saveAsFile = QAction("&Save As...", self)
        saveAsFile.setStatusTip('Save As...')
        saveAsFile.triggered.connect(self.file_save_as)
        self.fileMenu.addAction(saveAsFile)
        self.fileMenu.addSeparator()

        exitButton = QAction('Exit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.setStatusTip('Exit application')
        exitButton.triggered.connect(self.close)
        self.fileMenu.addAction(exitButton)

        # # Edit Menu
        # self.editMenu = self.mainMenu.addMenu("Edit")
        # undoEdit = QAction("&Undo Edit", self)
        # undoEdit.setShortcut("Ctrl+Z")
        # undoEdit.setStatusTip('Undo a change on the thematic map')
        # undoEdit.triggered.connect(lambda: print("Attempting to undo an edit"))  # TODO: implement undo edit
        # self.editMenu.addAction(undoEdit)

    def file_open(self):
        dlg = QFileDialog()
        fname = dlg.getOpenFileName(None, "Open Thematic Map", "", "FITS files (*.fits)")
        if fname != ('', ''):
            thmap = ThematicMap.load(fname[0])
            if thmap.complies_with_mapping(self.config.solar_class_name):
                self.annotator.loadThematicMap(thmap)
            else:
                QMessageBox.critical(self,
                                     'Error: Could not open',
                                     'Thematic map could not open because theme mapping differs from configuration',
                                      QMessageBox.Close)

    def file_save(self):
        if self.output_fn is None:
            self.file_save_as()
        else:
            self.annotator.thmap.save(self.output_fn)

    def file_save_as(self):
        dlg = QFileDialog()
        fname = dlg.getSaveFileName(None, "Open Thematic Map", "", "FITS files (*.fits)")
        if fname != ('', ''):
            self.annotator.thmap.save(fname[0])
            self.output_fn = fname[0]
