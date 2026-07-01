
# This is just for josh
# rm -rf .venv
# python3.12 -m venv .venv
# source .venv/bin/activate
# pip install PyQt6 pyqtgraph zaber_motion nidaqmx

#Imports 
import config
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QHBoxLayout, QPushButton,QLabel,QLineEdit,QCheckBox,QComboBox
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import QApplication
import sys
from Viewer import Viewer
from ExperimentNew import Experiment



class Gui(QWidget):
    '''This is the main Gui class. An instance of this class is called when this file is open
    which opens the window. '''
    def __init__(self):
        super().__init__()
        
        
        self.setWhatsThis("This is the main window for the SHG application.")
        #The main layout for the Window. It is in HBox layout,
        # meaning widgets added sequentially will propagate left-right
        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)
        
    
        #This creates an instance of the viewer class,
        # which is the widget that displays the plots
        self.viewer = Viewer()
        
        #Add the control panel
        #This is the widget that contains all of the controls and parameter inputs for the experiment
        control = ControlPanel()
        main_layout.addWidget(control)
        
        #This sets the initial size of the experiment
        self.resize(1000, 600)

        #This connects the start button on the control panel to be connected to the experiment file
        #When start is clicked, experiment.py will run.
      #  self.start_button.clicked.connect(
          #  self.start_experiment)

    def start_experiment(self):
        #This creates an instance of the experiment class from the Experiment.py file
        self.experiment = Experiment()

        #This creates a streaming channel for the single shot data
        self.experiment.new_single.connect(
            self.viewer.update_single
        )

        #This creates a streaming channel for the average shot data
        self.experiment.new_average.connect(
            self.viewer.update_average
        )
        #This allows the GUI to know when the experiment is done running
        self.experiment.finished.connect(
            lambda: print("Finished")
        )
        #This runs the experiment
        self.experiment.start()

class ControlPanel(QWidget):
    '''This is the control panel Widget. It has a QGridLayout, which means widget
    positions must be specified when added by addWidget(widget, row, column)'''
    def __init__(self):
        super().__init__()
        self.setWhatsThis("This is the control panel for the SHG application.")
        
        self.file_info = config.FILE_INFO
        
        #The main control layout
        control_layout = QGridLayout(self)
        #Run button - should initialize experiment
        self.run_button = QPushButton("Run")
        control_layout.addWidget(self.run_button,0,0)
        #Stop button- Should stop the experiment, home the zabers?
        self.stop_button = QPushButton("Stop")
        control_layout.addWidget(self.stop_button,0,1)
        
        #Setting the sample name
        self.sample_input = QLineEdit()
        self.sample_label=QLabel("Sample")
        control_layout.addWidget(self.sample_label,1,1)
        control_layout.addWidget(self.sample_input,1,0)
        self.sample_input.editingFinished.connect(
        lambda: self.update_file_info(
        self.sample_input.text(),
        "sample"
        )
)
        
        
        #Setting the face
        self.face_input = QLineEdit()
        self.face_label=QLabel("Face")
        control_layout.addWidget(self.face_label,2,1)
        control_layout.addWidget(self.face_input,2,0)
        self.face_input.editingFinished.connect(
        lambda: self.update_file_info(
        self.face_input.text(),
        "face"
    )
)
        
        #Setting the number of averages
        self.average_input = QLineEdit()
        self.average_input.setValidator(QIntValidator())
        self.average_label=QLabel("Averages")
        control_layout.addWidget(self.average_label,3,1)
        control_layout.addWidget(self.average_input,3,0)
        self.average_input.editingFinished.connect(
        lambda: self.update_file_info(
        self.average_input.text(),
        "averages"
        )
)
        
        
        
        #Setting the wavelengths
        self.start_wavelength = QLineEdit()
        self.start_wavelength_label = QLabel("Start Wavelength (nm)")
        control_layout.addWidget(self.start_wavelength,4,0)
        control_layout.addWidget(self.start_wavelength_label,4,1)
        self.start_wavelength.editingFinished.connect(
        lambda: self.update_file_info(
        self.start_wavelength.text(),
        "first_wavelength"
        )
)
        self.end_wavelength = QLineEdit()
        self.end_wavelength_label = QLabel("End Wavelength (nm)")
        control_layout.addWidget(self.end_wavelength,5,0)
        control_layout.addWidget(self.end_wavelength_label,5,1)
        self.end_wavelength.editingFinished.connect(
        lambda: self.update_file_info(
        self.end_wavelength.text(),
        "second_wavelength"
        )
)        
        #Temperature
        self.temperature_input = QLineEdit()
        self.temperature_input.setValidator(QIntValidator())
        self.temperature_label = QLabel("Temperature (K)")
        control_layout.addWidget(self.temperature_input,6,0)
        control_layout.addWidget(self.temperature_label,6,1)
        self.temperature_input.editingFinished.connect(
        lambda: self.update_file_info(
        self.temperature_input.text(),
        "temperature"
        )
)
        #Polarization mode
        self.polarization_button = QComboBox()
        self.polarization_button.addItem("H")
        self.polarization_button.addItem("V")
        self.polarization_button.addItem("Parallel")
        self.polarization_button.addItem("Perpendicular")
        self.polarization_button.textActivated.connect(self.change_polarization)
        self.polarization_label= QLabel("Selected: H")
        control_layout.addWidget(self.polarization_button,7,0)
        control_layout.addWidget(self.polarization_label,7,1)
        
        
        
        #Option to save data
        self.save_data = QCheckBox("Save Data")
        control_layout.addWidget(self.save_data,8,0)
        self.save_data.toggled.connect(self.initialize_save)
        
    def initialize_save(self):
        pass
        
    def change_polarization(self,text):
        self.polarization_label.setText(f"Selected: {text}")
        self.file_info["polarization"] = text
        
    def update_file_info(self,value,key):
        if key == "averages" or key=="temperature":
            try:
                
                self.file_info[key] = int(value)
            except:
                pass
        
        else:
            try:
                self.file_info[key] = value
            except:
                pass
        

       
         

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = Gui()
    window.show()

    sys.exit(app.exec())