import sys
import PyQt5
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QWidget, QLabel, QAction, QTabWidget, QPushButton, QFileDialog, QRadioButton, QMessageBox, \
    QComboBox, QLineEdit, QSizePolicy
from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QIcon, QDoubleValidator
from datetime import datetime, timedelta
from matplotlib import path
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
from skimage.morphology import binary_erosion
import scipy
import numpy as np
from matplotlib.widgets import LassoSelector
from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
from PIL import ImageColor

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
        self.composites = ImageSet.create_empty()
        self.current_theme_index = 0

        self.preview_data = self.composites['94'].data.copy()
        self.thmap_data = np.zeros((1280, 1280))
        self.thmap = ThematicMap(self.thmap_data, {'DATE-OBS': str(datetime.today())}, config.solar_class_name)

        self.history = []

        layout = QtWidgets.QVBoxLayout()

        self.fig = Figure(figsize=(15, 10))
        canvas = FigureCanvas(self.fig)
        canvas.mpl_connect('button_press_event', self.onclick)

        layout.addWidget(canvas)

        self.region_patches = []
        self.axs = canvas.figure.subplots(ncols=2, sharex=True, sharey=True)
        self.preview_axesimage = self.axs[0].imshow(self.preview_data, vmin=0, vmax=1, cmap='gray', origin='lower')
        self.thmap_axesimage = self.axs[1].imshow(self.thmap_data, origin='lower',
                                                  vmin=0, vmax=config.max_index, cmap=config.solar_cmap)
        self.axs[0].set_axis_off()
        self.axs[1].set_axis_off()
        self.axs[0].set_title("Preview")
        self.axs[1].set_title("Thematic Map")

        self.toolbar = NavigationToolbar(canvas, self)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)

        # add selection layer for lasso
        self.shape = (1280, 1280)  # TODO: replace with dynamic detection
        self.pix = np.arange(self.shape[0])  # assumes square image
        xv, yv = np.meshgrid(self.pix, self.pix)
        self.pix = np.vstack((xv.flatten(), yv.flatten())).T

        lineprops = dict(color="red", linewidth=2)
        self.lasso = LassoSelector(self.axs[0], self.onlasso, lineprops=lineprops)
        self.fig.tight_layout()

    def onlasso(self, verts):
        """
        Main function to control the action of the lasso, allows user to draw on data image and adjust thematic map
        :param verts: the vertices selected by the lasso
        :return: nothin, but update the selection array so lassoed region now has the selected theme, redraws canvas
        """
        p = path.Path(verts)
        ind = p.contains_points(self.pix, radius=1)
        self.history.append(self.thmap_data.copy())
        self.thmap_data = self.updateArray(self.thmap_data,
                                                ind,
                                                self.current_theme_index)
        self.thmap_axesimage.set_data(self.thmap_data)
        self.fig.canvas.draw_idle()
        self.thmap.data = self.thmap_data

    def rename_region(self, event):
        # draw patches
        y, x = int(event.xdata), int(event.ydata)
        self.history.append(self.thmap_data.copy())
        label = self.thmap_data[x, y]
        contiguous_regions = scipy.ndimage.label(self.thmap_data == label)[0]
        this_region = contiguous_regions == (contiguous_regions[x, y])
        self.thmap_data[this_region] = self.current_theme_index
        self.thmap_axesimage.set_data(self.thmap_data)
        self.thmap.data = self.thmap_data
        self.fig.canvas.draw_idle()

    def draw_event_region_boundary(self, event):
        """
        Draw a patch around the contiguous region in the preview image
        :param event:
        :return:
        """
        # draw patches
        y, x = int(event.xdata), int(event.ydata)
        label = self.thmap_data[x, y]
        contiguous_regions = scipy.ndimage.label(self.thmap_data == label)[0]
        this_region = contiguous_regions == (contiguous_regions[x, y])

        # remove the boundaries so any region touching the edge isn't drawn odd
        this_region[0, :] = 0
        this_region[:, 0] = 0
        this_region[this_region.shape[0] - 1, :] = 0
        this_region[:, this_region.shape[1] - 1] = 0

        # convert the region mask into just a true/false array of its boundary pixels
        edges = binary_erosion(this_region) ^ this_region

        # convert the boundary pixels into a path, moving around instead of just where
        x, y = np.where(edges)
        coords = np.dstack([x, y])[0]
        path = [coords[0]]
        coords = coords[1:]

        while len(coords):
            dist = np.sum(np.abs(path[-1] - coords), axis=1)
            neighbor_index = np.argmin(dist)

            if dist[neighbor_index] < 5:
                path.append(coords[neighbor_index].copy())
                coords[neighbor_index:-1] = coords[neighbor_index + 1:]
                coords = coords[:-1]
            else:
                break

        path = np.array(path)

        clips = []
        while len(coords) > 5:
            dist = np.sum(np.abs(path[-1] - coords), axis=1)
            neighbor_index = np.argmin(dist)
            clip = [coords[neighbor_index].copy()]
            coords[neighbor_index:-1] = coords[neighbor_index + 1:]
            coords = coords[:-1]
            while len(coords):
                dist = np.sum(np.abs(clip[-1] - coords), axis=1)
                neighbor_index = np.argmin(dist)
                if dist[neighbor_index] < 5:
                    clip.append(coords[neighbor_index].copy())
                    coords[neighbor_index:-1] = coords[neighbor_index + 1:]
                    coords = coords[:-1]
                else:
                    break
            clips.append(np.array(clip))

        # draw the continguous  on the selection area
        self.region_patches.append(PatchCollection(
            [Polygon(np.dstack([path[:, 1], path[:, 0]])[0], False,
                     fill=False, facecolor=None,
                     edgecolor="black", alpha=1, lw=2.5)] +
            [Polygon(np.dstack([clip[:, 1], clip[:, 0]])[0], False,
                     fill=False, facecolor=None,
                     edgecolor="black", alpha=1, lw=2.0) for clip in clips],
            match_original=True))
        self.axs[0].add_collection(self.region_patches[-1])
        self.fig.canvas.draw_idle()

    def undo_action(self):
        """ when undo is clicked, revert the thematic map to the previous state"""
        if len(self.history) > 1:
            old = self.history.pop(-1)
            self.thmap_data = old
            self.thmap.data = self.thmap_data
            self.thmap_axesimage.set_data(old)
            self.fig.canvas.draw_idle()

    def onclick(self, event):
        """
        Draw contours on the data for a click in the thematic map
        :param event: mouse click on thematic map preview
        """
        if event.inaxes == self.axs[1]:
            if event.button == 3:  # right click feature
                self.draw_event_region_boundary(event)
            if event.button == 1 and self.toolbar.mode == "":
                self.rename_region(event)

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

    def clearBoundaries(self):
        for patch in self.region_patches:
            patch.remove()
        self.region_patches = []
        self.fig.canvas.draw_idle()

    def loadThematicMap(self, thmap):
        try:
            download_message = QMessageBox.information(self,
                                                       'Downloading',
                                                       "Downloads may take a few moments. Click 'ok' to proceed.",
                                                       QMessageBox.Ok)
            self.composites = ImageSet.retrieve(thmap.date_obs)
        except RuntimeError:
            self.data_does_not_exist_popup()
        else:
            self.thmap = thmap
            self.thmap.copy_195_metadata(self.composites)
            self.history = [thmap.data.copy()]
            self.thmap_data = thmap.data
            self.thmap_axesimage.set_data(self.thmap_data)
            self.preview_axesimage.set_data(self.composites['94'].data)
            self.fig.canvas.draw_idle()

    def updateSingleColorImage(self, channel, lower_percentile, upper_percentile, scale):
        self.preview_data = self.composites[channel].data.copy()
        self.preview_data = np.power(np.abs(self.preview_data), scale) * np.sign(self.preview_data)
        lower = np.nanpercentile(self.preview_data, lower_percentile)
        upper = np.nanpercentile(self.preview_data, upper_percentile)
        self.preview_data[self.preview_data < lower] = lower
        self.preview_data[self.preview_data > upper] = upper
        self.preview_data /= np.nanmax(self.preview_data)
        self.preview_axesimage.set_data(self.preview_data)
        self.fig.canvas.draw_idle()

    def updateThreeColorImage(self, red_channel, green_channel, blue_channel,
                              red_min, green_min, blue_min,
                              red_max, green_max, blue_max,
                              red_scale, green_scale, blue_scale):
        self.preview_data = np.stack([self.composites[red_channel].data.copy(),
                                     self.composites[green_channel].data.copy(),
                                     self.composites[blue_channel].data.copy()], axis=2)
        self.preview_data[:, :, 0] = np.power(self.preview_data[:, :, 0], red_scale)
        self.preview_data[:, :, 1] = np.power(self.preview_data[:, :, 1], green_scale)
        self.preview_data[:, :, 2] = np.power(self.preview_data[:, :, 2], blue_scale)

        red_lower = np.nanpercentile(self.preview_data[:, :, 0], red_min)
        green_lower = np.nanpercentile(self.preview_data[:, :, 1], green_min)
        blue_lower = np.nanpercentile(self.preview_data[:, :, 2], blue_min)

        red_upper = np.nanpercentile(self.preview_data[:, :, 0], red_max)
        green_upper = np.nanpercentile(self.preview_data[:, :, 1], green_max)
        blue_upper = np.nanpercentile(self.preview_data[:, :, ], blue_max)

        self.preview_data[self.preview_data[:, :, 0] < red_lower] = red_lower
        self.preview_data[self.preview_data[:, :, 0] > red_upper] = red_upper
        self.preview_data[self.preview_data[:, :, 1] < green_lower] = green_lower
        self.preview_data[self.preview_data[:, :, 1] > green_upper] = green_upper
        self.preview_data[self.preview_data[:, :, 2] < blue_lower] = blue_lower
        self.preview_data[self.preview_data[:, :, 2] > blue_upper] = blue_upper
        
        for index in [0, 1, 2]:
            self.preview_data[:, :, index] /= np.nanmax(self.preview_data[:, :, index])

        self.preview_axesimage.set_data(self.preview_data)
        self.fig.canvas.draw_idle()

    def data_does_not_exist_popup(self):
        QMessageBox.critical(self,
                             'Error: Could not open',
                             'Composite data does not exist for that date.',
                             QMessageBox.Close)


class ControlWidget(QtWidgets.QWidget):
    def __init__(self, annotator):
        super().__init__()
        self.annotator = annotator

        layout = QtWidgets.QHBoxLayout()
        self.tabs = QTabWidget()
        self.one_color_tab = QWidget()
        self.three_color_tab = QWidget()

        # Add tabs
        self.tabs.addTab(self.one_color_tab, "Single")
        self.tabs.addTab(self.three_color_tab, "Three-color")
        self.tabs.currentChanged.connect(self.onTabChange)

        self.initSingleColorUI()
        self.initThreeColorUI()

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def initSingleColorUI(self):
        # Create single color tab
        self.one_color_tab.layout = QtWidgets.QGridLayout(self)

        self.single_color_label = QLabel()
        self.single_color_label.setText("Channel")
        self.one_color_tab.layout.addWidget(self.single_color_label)
        self.single_color_combo_box = QComboBox()
        self.single_color_combo_box.addItems(self.annotator.composites.channels())
        self.single_color_combo_box.currentTextChanged.connect(self.onSingleColorChange)

        self.one_color_min_editor = QLineEdit()
        self.one_color_min_editor.setValidator(QDoubleValidator(0.0, 100.0, 3))
        self.one_color_min_editor.setText("0.0")
        self.one_color_min_editor.editingFinished.connect(self.onSingleColorChange)

        self.one_color_max_editor = QLineEdit()
        self.one_color_max_editor.setValidator(QDoubleValidator(0.0, 100.0, 3))
        self.one_color_max_editor.setText("99.9")
        self.one_color_max_editor.editingFinished.connect(self.onSingleColorChange)

        self.one_color_scale_editor = QLineEdit()
        self.one_color_scale_editor.setValidator(QDoubleValidator(0.0, 100.0, 3))
        self.one_color_scale_editor.setText("0.25")
        self.one_color_scale_editor.editingFinished.connect(self.onSingleColorChange)

        channel_label = QLabel("Channel", self)
        channel_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        min_label = QLabel("Min", self)
        min_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        max_label = QLabel("Max", self)
        max_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        scale_label = QLabel("Scale", self)
        scale_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)

        self.one_color_tab.setLayout(self.one_color_tab.layout)
        self.one_color_tab.layout.addWidget(channel_label, 0, 1)
        self.one_color_tab.layout.addWidget(min_label, 0, 2)
        self.one_color_tab.layout.addWidget(max_label, 0, 3)
        self.one_color_tab.layout.addWidget(scale_label, 0, 4)
        self.one_color_tab.layout.addWidget(self.single_color_label, 1, 0)
        self.one_color_tab.layout.addWidget(self.single_color_combo_box, 1, 1)
        self.one_color_tab.layout.addWidget(self.one_color_min_editor, 1, 2)
        self.one_color_tab.layout.addWidget(self.one_color_max_editor, 1, 3)
        self.one_color_tab.layout.addWidget(self.one_color_scale_editor, 1, 4)


    def initThreeColorUI(self):
        self.three_color_tab.layout = QtWidgets.QGridLayout(self)

        channel_label = QLabel("Channel")
        channel_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        min_label = QLabel("Min")
        min_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        max_label = QLabel("Max")
        max_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
        scale_label = QLabel("Scale")
        scale_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)

        self.red_label = QLabel()
        self.red_label.setText("Red Channel")
        self.red_label.setAlignment(QtCore.Qt.AlignRight)
        self.red_combo_box = QComboBox()
        self.red_combo_box.addItems(self.annotator.composites.channels())
        self.red_combo_box.setCurrentIndex(2)
        self.red_combo_box.currentTextChanged.connect(self.onThreeColorChange)
        self.red_min_editor = QLineEdit()
        self.red_min_editor.setValidator(QDoubleValidator(0.0, 100.0, 3))
        self.red_min_editor.setText("0.0")
        self.red_min_editor.editingFinished.connect(self.onThreeColorChange)
        self.red_max_editor = QLineEdit()
        self.red_max_editor.setValidator(QDoubleValidator(0.0, 100.0, 3))
        self.red_max_editor.setText("100")
        self.red_max_editor.editingFinished.connect(self.onThreeColorChange)
        self.red_scale_editor = QLineEdit()
        self.red_scale_editor.setValidator(QDoubleValidator(0.0, 100.0, 3))
        self.red_scale_editor.setText("0.25")
        self.red_scale_editor.editingFinished.connect(self.onThreeColorChange)

        self.green_label = QLabel()
        self.green_label.setText("Green Channel")
        self.green_label.setAlignment(QtCore.Qt.AlignRight)
        self.green_combo_box = QComboBox()
        self.green_combo_box.addItems(self.annotator.composites.channels())
        self.green_combo_box.setCurrentIndex(3)
        self.green_combo_box.currentTextChanged.connect(self.onThreeColorChange)
        self.green_min_editor = QLineEdit()
        self.green_min_editor.setValidator(QDoubleValidator(0.0, 100.0, 3))
        self.green_min_editor.setText("0.0")
        self.green_min_editor.editingFinished.connect(self.onThreeColorChange)
        self.green_max_editor = QLineEdit()
        self.green_max_editor.setValidator(QDoubleValidator(0.0, 100.0, 3))
        self.green_max_editor.setText("100")
        self.green_max_editor.editingFinished.connect(self.onThreeColorChange)
        self.green_scale_editor = QLineEdit()
        self.green_scale_editor.setValidator(QDoubleValidator(0.0, 100.0, 3))
        self.green_scale_editor.setText("0.25")
        self.green_scale_editor.editingFinished.connect(self.onThreeColorChange)

        self.blue_label = QLabel()
        self.blue_label.setText("Blue Channel")
        self.blue_label.setAlignment(QtCore.Qt.AlignRight)
        self.blue_combo_box = QComboBox()
        self.blue_combo_box.addItems(self.annotator.composites.channels())
        self.blue_combo_box.setCurrentIndex(4)
        self.blue_combo_box.currentTextChanged.connect(self.onThreeColorChange)
        self.blue_min_editor = QLineEdit()
        self.blue_min_editor.setValidator(QDoubleValidator(0.0, 100.0, 3))
        self.blue_min_editor.setText("0.0")
        self.blue_min_editor.editingFinished.connect(self.onThreeColorChange)
        self.blue_max_editor = QLineEdit()
        self.blue_max_editor.setValidator(QDoubleValidator(0.0, 100.0, 3))
        self.blue_max_editor.setText("100")
        self.blue_max_editor.editingFinished.connect(self.onThreeColorChange)
        self.blue_scale_editor = QLineEdit()
        self.blue_scale_editor.setValidator(QDoubleValidator(0.0, 100.0, 3))
        self.blue_scale_editor.setText("0.25")
        self.blue_scale_editor.editingFinished.connect(self.onThreeColorChange)

        self.three_color_tab.setLayout(self.three_color_tab.layout)
        self.three_color_tab.layout.addWidget(self.red_label, 1, 0)
        self.three_color_tab.layout.addWidget(self.green_label, 2, 0)
        self.three_color_tab.layout.addWidget(self.blue_label, 3, 0)
        self.three_color_tab.layout.addWidget(channel_label, 0, 1)
        self.three_color_tab.layout.addWidget(self.red_combo_box, 1, 1)
        self.three_color_tab.layout.addWidget(self.green_combo_box, 2, 1)
        self.three_color_tab.layout.addWidget(self.blue_combo_box, 3, 1)
        self.three_color_tab.layout.addWidget(min_label, 0, 2)
        self.three_color_tab.layout.addWidget(self.red_min_editor, 1, 2)
        self.three_color_tab.layout.addWidget(self.green_min_editor, 2, 2)
        self.three_color_tab.layout.addWidget(self.blue_min_editor, 3, 2)
        self.three_color_tab.layout.addWidget(max_label, 0, 3)
        self.three_color_tab.layout.addWidget(self.red_max_editor, 1, 3)
        self.three_color_tab.layout.addWidget(self.green_max_editor, 2, 3)
        self.three_color_tab.layout.addWidget(self.blue_max_editor, 3, 3)
        self.three_color_tab.layout.addWidget(scale_label, 0, 4)
        self.three_color_tab.layout.addWidget(self.red_scale_editor, 1, 4)
        self.three_color_tab.layout.addWidget(self.green_scale_editor, 2, 4)
        self.three_color_tab.layout.addWidget(self.blue_scale_editor, 3, 4)

    def onTabChange(self):
        if self.tabs.currentIndex() == 0:
            self.onSingleColorChange()
        elif self.tabs.currentIndex() == 1:
            self.onThreeColorChange()

    def onSingleColorChange(self):
        self.annotator.updateSingleColorImage(self.single_color_combo_box.currentText(),
                                              float(self.one_color_min_editor.text()),
                                              float(self.one_color_max_editor.text()),
                                              float(self.one_color_scale_editor.text()))

    def onThreeColorChange(self):
        red_channel = self.red_combo_box.currentText()
        green_channel = self.green_combo_box.currentText()
        blue_channel = self.blue_combo_box.currentText()
        self.annotator.updateThreeColorImage(red_channel, green_channel, blue_channel,
                                             float(self.red_min_editor.text()),
                                             float(self.green_min_editor.text()),
                                             float(self.blue_min_editor.text()),
                                             float(self.red_max_editor.text()),
                                             float(self.green_max_editor.text()),
                                             float(self.blue_max_editor.text()),
                                             float(self.red_scale_editor.text()),
                                             float(self.green_scale_editor.text()),
                                             float(self.blue_scale_editor.text()))


class NewFilePopup(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QHBoxLayout()
        instructions = QLabel("Please select a time for the new file.", self)
        self.dateEdit = QtWidgets.QDateTimeEdit(QDateTime.currentDateTime())
        submit_button = QPushButton("Submit")
        layout.addWidget(instructions)
        layout.addWidget(self.dateEdit)
        layout.addWidget(submit_button)
        self.setLayout(layout)
        submit_button.clicked.connect(self.onSubmit)

    def onSubmit(self):
        # set the date in the application and close
        self.parent.date = self.dateEdit.dateTime().toPyDateTime()
        new_thmap = ThematicMap(np.zeros((1280, 1280)),
                                {'DATE-OBS': str(self.parent.date),
                                 'DATE': str(datetime.today())},
                                self.parent.config.solar_class_name)
        self.parent.annotator.loadThematicMap(new_thmap)
        self.parent.controls.onTabChange()  # Us
        self.close()


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self, config_path):
        super().__init__()
        self.config = Config(config_path)
        self.output_fn = None
        self.initialized = False
        self.initUI()
        self.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.CustomizeWindowHint |
            QtCore.Qt.WindowTitleHint |
            QtCore.Qt.WindowCloseButtonHint |
            QtCore.Qt.WindowStaysOnTopHint
        )


    def initUI(self):
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)


        layout = QtWidgets.QVBoxLayout(self._main)
        self.annotator = AnnotationWidget(self.config)
        layout.addWidget(self.annotator)

        self._setup_control_layout()
        layout.addLayout(self.control_layout)
        self._setup_menubar()


    def _setup_control_layout(self):
        self.control_layout = QtWidgets.QHBoxLayout()
        self.controls = ControlWidget(self.annotator)
        self.control_layout.addWidget(self.controls)
        self._setup_theme_radio_buttons()

    def _setup_theme_radio_buttons(self):
        def radio_button_font_color(background_color_hex):
            """
            Select white for dark color backgrounds and black for light colored backgrounds
            """
            background_color_rgb = ImageColor.getcolor(background_color_hex, "RGB")
            if any([c < 50 for c in background_color_rgb]):
                return "#FFFFFF"
            else:
                return "#000000"

        theme_selection_layout = QtWidgets.QVBoxLayout()
        radiobuttons = dict()

        # add unlabelled button
        radiobuttons['unlabeled'] = QRadioButton("unlabeled")
        radiobuttons['unlabeled'].index = 0
        radiobuttons['unlabeled'].setChecked(True)
        radiobuttons['unlabeled'].toggled.connect(self.onClickedRadioButton)
        background_color = '#FFFFFF'
        font_color = radio_button_font_color(background_color)
        radiobuttons['unlabeled'].setStyleSheet("QRadioButton"
                                          "{"
                                          "background-color : " + background_color + ";"
                                          "color :" + font_color + ""
                                           "}")
        theme_selection_layout.addWidget(radiobuttons['unlabeled'])

        # add rest of theme buttons
        for theme, index in self.config.solar_class_index.items():
            radiobuttons[theme] = QRadioButton(theme)
            radiobuttons[theme].index = index
            radiobuttons[theme].toggled.connect(self.onClickedRadioButton)
            background_color = self.config.solar_colors[theme]
            font_color = radio_button_font_color(background_color)
            radiobuttons[theme].setStyleSheet("QRadioButton"
                                       "{"
                                       "background-color : " + background_color + ";"
                                       "color :" + font_color + ""                                       
                                       "}")

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
        newButton.triggered.connect(self.new_file)
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
        exitButton.triggered.connect(self.exit)
        self.fileMenu.addAction(exitButton)

        # Edit Menu
        self.editMenu = self.mainMenu.addMenu("Edit")
        undoEdit = QAction("&Undo Edit", self)
        undoEdit.setShortcut("Ctrl+Z")
        undoEdit.setStatusTip('Undo a change on the thematic map')
        undoEdit.triggered.connect(self.annotator.undo_action)
        self.editMenu.addAction(undoEdit)
        self.editMenu.addSeparator()

        eraseBoundaries = QAction("&Erase boundaries", self)
        eraseBoundaries.setShortcut("Ctrl+E")
        eraseBoundaries.setStatusTip("Remove all the boundaries drawn on a map")
        eraseBoundaries.triggered.connect(self.annotator.clearBoundaries)
        self.editMenu.addAction(eraseBoundaries)

    def exit(self):
        if self.initialized:
            answer = QMessageBox.question(self, '', "Would you like to save?",
                                          QMessageBox.Yes | QMessageBox.No)
            if answer == QMessageBox.Yes:
                self.file_save_as()
        sys.exit()

    def closeEvent(self, *args, **kwargs):
        self.exit()

    def new_file(self):
        self.new_file_popup = NewFilePopup(self)
        self.new_file_popup.setGeometry(100, 200, 100, 100)
        self.new_file_popup.show()
        self.annotator.clearBoundaries()
        self.initialized = True

    def file_open(self):
        dlg = QFileDialog()
        fname = dlg.getOpenFileName(None, "Open Thematic Map", "", "FITS files (*.fits)")
        if fname != ('', ''):
            thmap = ThematicMap.load(fname[0])
            if thmap.complies_with_mapping(self.config.solar_class_name):
                self.annotator.loadThematicMap(thmap)
                self.controls.onTabChange()  # Use the tab change to automatically load the right image
                self.annotator.clearBoundaries()
                self.initialized = True
            else:
                QMessageBox.critical(self,
                                    'Error: Could not open',
                                     'Thematic map could not open because theme mapping differs from configuration',
                                     QMessageBox.Close)

    def prompt_not_initialized(self):
        QMessageBox.critical(self,
                            "Error: Could not save",
                            "You must create a new thematic map or load one before saving.",
                            QMessageBox.Close)

    def file_save(self):
        if self.initialized:
            if self.output_fn is None:
                self.file_save_as()
            else:
                self.annotator.thmap.metadata['DATE'] = str(datetime.today())
                self.annotator.thmap.save(self.output_fn)
        else:
            self.prompt_not_initialized()

    def file_save_as(self):
        if self.initialized:
            dlg = QFileDialog()
            fname = dlg.getSaveFileName(None, "Save Thematic Map", "", "FITS files (*.fits)")
            if fname != ('', ''):
                self.annotator.thmap.metadata['DATE'] = str(datetime.today())
                self.annotator.thmap.save(fname[0])
                self.output_fn = fname[0]
        else:
            self.prompt_not_initialized()
