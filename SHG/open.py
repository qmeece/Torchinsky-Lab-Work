
# This is just for josh
# rm -rf .venv
# python3.12 -m venv .venv
# source .venv/bin/activate
# pip install PyQt6 pyqtgraph


import pyqtgraph as pg
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QHBoxLayout, QPushButton,QLabel,QLineEdit,QCheckBox,QComboBox
from PyQt6.QtWidgets import QApplication
import sys
from Viewer import Viewer
from ExperimentNew import Experiment


class Gui(QWidget):
    def __init__(self):
        super().__init__()
        self.setWhatsThis("This is the main window for the SHG application.")
        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)
        
        #Add the viewer panel
        self.viewer = Viewer.Viewer()
        
        #Add the control panel
        control = ControlPanel()
        main_layout.addWidget(control)
        
        #Geometry
        self.resize(1000, 600)

        self.start_button.clicked.connect(
            self.start_experiment)

    def start_experiment(self):

        self.experiment = Experiment()

        self.experiment.new_single.connect(
            self.viewer.update_single
        )

        self.experiment.new_average.connect(
            self.viewer.update_average
        )

        self.experiment.finished.connect(
            lambda: print("Finished")
        )

        self.experiment.start()

class ControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWhatsThis("This is the control panel for the SHG application.")
        #The main control layout
        control_layout = QGridLayout(self)

        #Run button - should initialize experiment
        self.run_button = QPushButton("Run")
        control_layout.addWidget(self.run_button,0,0)
        #Stop button- Should stop the experiment, home the zabers?
        self.stop_button = QPushButton("Stop")
        control_layout.addWidget(self.stop_button,0,1)
        #Setting the file name
        self.file_input = QLineEdit()
        self.file_label=QLabel("File Name")
        control_layout.addWidget(self.file_label,2,1)
        control_layout.addWidget(self.file_input,2,0)
        #Setting the wavelengths
        self.start_wavelength = QLineEdit()
        self.start_wavelength_label = QLabel("Start Wavelength (nm)")
        control_layout.addWidget(self.start_wavelength,3,0)
        control_layout.addWidget(self.start_wavelength_label,3,1)
        
        self.end_wavelength = QLineEdit()
        self.end_wavelength_label = QLabel("End Wavelength (nm)")
        control_layout.addWidget(self.end_wavelength,4,0)
        control_layout.addWidget(self.end_wavelength_label,4,1)
        
        #Temperature
        self.temperature = QLineEdit()
        self.temperature_label = QLabel("Temperature (K)")
        control_layout.addWidget(self.temperature,5,0)
        control_layout.addWidget(self.temperature_label,5,1)
        #Polarization mode
        self.polarization_button = QComboBox()
        self.polarization_button.addItem("H")
        self.polarization_button.addItem("V")
        self.polarization_button.addItem("Parallel")
        self.polarization_button.addItem("Perpendicular")
        self.polarization_button.textActivated.connect(self.on_selected_changed)
        self.polarization_label= QLabel("Selected: H")
        control_layout.addWidget(self.polarization_button,6,0)
        control_layout.addWidget(self.polarization_label,6,1)
        
        
        #Option to save data
        self.save_data = QCheckBox("Save Data")
        control_layout.addWidget(self.save_data,7,0)
        
        
        
        
    def on_selected_changed(self,text):
        self.polarization_label.setText(f"Selected: {text}")
    
        

       
         

def main():
    app = QApplication(sys.argv)
    gui = Gui()
    gui.show()
    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()