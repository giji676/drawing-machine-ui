import json
import os

from PyQt5.QtWidgets import (QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QSizePolicy, QSpacerItem, QWidget)

from src.utils import constants
from .configuration_canvas import ConfigurationCanvas

# Drawing machine configuration window
class ConfigureMachine(QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self) -> None:
        self.left_input_panel = QWidget()
        self.left_input_panel.setStyleSheet("background-color: #EEE;")

        self.right_canvas = ConfigurationCanvas()

        self.settings = constants.DEFAULT_SETTINGS.copy()
        global settings
        settings = self.settings

        # Creating the lables and inputs
        self.lbl_belt_tooth_distance = QLabel("Belt tooth distance")
        self.txt_belt_tooth_distance = QLineEdit()

        self.lbl_tooth_on_gear = QLabel("Tooth on gear")
        self.txt_tooth_on_gear = QLineEdit()

        self.lbl_steps_per_rev = QLabel("Steps per rev")
        self.txt_steps_per_rev = QLineEdit()

        self.lbl_motor_dir = QLabel("Motor direction")
        self.txt_motor_dir_1 = QLineEdit()
        self.txt_motor_dir_2 = QLineEdit()

        self.lbl_motor_dist = QLabel("Motor distance")
        self.txt_motor_dist = QLineEdit()

        self.lbl_start_dist = QLabel("Start distance")
        self.txt_start_dist_1 = QLineEdit()
        self.txt_start_dist_2 = QLineEdit()

        self.lbl_paper_dimenions = QLabel("Paper dimensions")
        self.txt_paper_dimenions_1 = QLineEdit()
        self.txt_paper_dimenions_2 = QLineEdit()

        self.lbl_paper_offset = QLabel("Paper offset")
        self.txt_paper_offset = QLineEdit()

        self.btn_load_defaults = QPushButton("Load default settings")
        self.btn_save = QPushButton("Save", self)

        self.loadSettings()
        self.setValuesInput(self.settings)

        self.vertical_spacer = QSpacerItem(
            0, 20, QSizePolicy.Fixed, QSizePolicy.Expanding
        )

        # Adding the lables and inputs to the layout
        self.lyt_inputs = QGridLayout()
        self.lyt_inputs.addWidget(self.lbl_belt_tooth_distance, 0, 0)
        self.lyt_inputs.addWidget(self.txt_belt_tooth_distance, 0, 1)
        self.lyt_inputs.addWidget(self.lbl_tooth_on_gear, 1, 0)
        self.lyt_inputs.addWidget(self.txt_tooth_on_gear, 1, 1)
        self.lyt_inputs.addWidget(self.lbl_steps_per_rev, 2, 0)
        self.lyt_inputs.addWidget(self.txt_steps_per_rev, 2, 1)
        self.lyt_inputs.addWidget(self.lbl_motor_dir, 3, 0)
        self.lyt_inputs.addWidget(self.txt_motor_dir_1, 4, 0)
        self.lyt_inputs.addWidget(self.txt_motor_dir_2, 4, 1)
        self.lyt_inputs.addWidget(self.lbl_motor_dist, 5, 0)
        self.lyt_inputs.addWidget(self.txt_motor_dist, 5, 1)
        self.lyt_inputs.addWidget(self.lbl_start_dist, 6, 0)
        self.lyt_inputs.addWidget(self.txt_start_dist_1, 7, 0)
        self.lyt_inputs.addWidget(self.txt_start_dist_2, 7, 1)
        self.lyt_inputs.addWidget(self.lbl_paper_dimenions, 8, 0)
        self.lyt_inputs.addWidget(self.txt_paper_dimenions_1, 9, 0)
        self.lyt_inputs.addWidget(self.txt_paper_dimenions_2, 9, 1)
        self.lyt_inputs.addWidget(self.lbl_paper_offset, 10, 0)
        self.lyt_inputs.addWidget(self.txt_paper_offset, 10, 1)
        self.lyt_inputs.addWidget(self.btn_load_defaults, 11, 0)
        self.lyt_inputs.addWidget(self.btn_save, 11, 1)

        self.lyt_inputs.addItem(self.vertical_spacer)

        self.left_input_panel.setLayout(self.lyt_inputs)

        self.lyt_configure_machine_tab = QHBoxLayout()
        self.lyt_configure_machine_tab.addWidget(self.left_input_panel)
        self.lyt_configure_machine_tab.addWidget(self.right_canvas)
        self.lyt_configure_machine_tab.setStretchFactor(self.left_input_panel, 2)
        self.lyt_configure_machine_tab.setStretchFactor(self.right_canvas, 7)

        self.setLayout(self.lyt_configure_machine_tab)

        # Connecting the inputs to their functions
        self.txt_paper_offset.textChanged.connect(self.processSettings)
        self.txt_motor_dist.textChanged.connect(self.processSettings)
        self.txt_paper_dimenions_1.textChanged.connect(self.processSettings)
        self.txt_paper_dimenions_2.textChanged.connect(self.processSettings)
        self.txt_start_dist_1.textChanged.connect(self.processSettings)
        self.txt_start_dist_2.textChanged.connect(self.processSettings)

        self.btn_save.clicked.connect(self.saveSettings)
        self.btn_load_defaults.clicked.connect(self.loadDefaultSettings)

        self.processSettings()

    def processSettings(self) -> None:
        # Sets the settings to the values of the input fields
        self.settings["beltToothDistance"] = int(
            self.txt_belt_tooth_distance.text())
        self.settings["toothOngear"] = int(self.txt_tooth_on_gear.text())
        self.settings["stepsPerRev"] = int(self.txt_steps_per_rev.text())
        self.settings["motorDir"] = [
            int(self.txt_motor_dir_1.text()),
            int(self.txt_motor_dir_2.text()),
        ]
        self.settings["distanceBetweenMotors"] = int(self.txt_motor_dist.text())
        self.settings["startDistance"] = [
            int(self.txt_start_dist_1.text()),
            int(self.txt_start_dist_2.text()),
        ]
        self.settings["paperSize"] = [
            int(self.txt_paper_dimenions_1.text()),
            int(self.txt_paper_dimenions_2.text()),
        ]
        self.settings["paperOffset"] = int(self.txt_paper_offset.text())

        self.right_canvas.setSettings(self.settings)
        self.right_canvas.update()
        global settings
        settings = self.settings

    def setValuesInput(self, vals: dict) -> None:
        # Sets the input fields to the <vals> values
        if vals is None:
            return

        self.txt_belt_tooth_distance.setText(str(vals["beltToothDistance"]))
        self.txt_tooth_on_gear.setText(str(vals["toothOngear"]))
        self.txt_steps_per_rev.setText(str(vals["stepsPerRev"]))
        self.txt_motor_dir_1.setText(str(vals["motorDir"][0]))
        self.txt_motor_dir_2.setText(str(vals["motorDir"][1]))
        self.txt_motor_dist.setText(str(vals["distanceBetweenMotors"]))
        self.txt_start_dist_1.setText(str(vals["startDistance"][0]))
        self.txt_start_dist_2.setText(str(vals["startDistance"][1]))
        self.txt_paper_dimenions_1.setText(str(vals["paperSize"][0]))
        self.txt_paper_dimenions_2.setText(str(vals["paperSize"][1]))
        self.txt_paper_offset.setText(str(vals["paperOffset"]))

    def loadDefaultSettings(self) -> None:

        self.setValuesInput(constants.DEFAULT_SETTINGS.copy())
        self.processSettings()
        self.right_canvas.setSettings(self.settings)
        self.right_canvas.update()
        global settings
        settings = self.settings

    def saveSettings(self) -> None:
        # Saves settings to <SETTINGS> file
        with open(constants.SETTINGS, "w") as settings_file:
            json.dump(self.settings, settings_file)

    def loadSettings(self) -> None:
        # Loads settings if the <SETTINGS> file exists
        # Otherwise loads default settings
        if not os.path.exists(constants.SETTINGS):
            self.loadDefaultSettings()
            self.saveSettings()

        with open(constants.SETTINGS, "r") as settings_file:
            self.settings = json.load(settings_file)
            global settings
            settings = self.settings
