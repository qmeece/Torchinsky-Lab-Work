
import pyqtgraph as pg
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from Viewer import Viewer
from PyQt6.QtWidgets import QApplication
import sys


class Gui(QWidget):
    def __init__(self):
        super().__init__()
        self.setWhatsThis("This is the main window for the SHG application.")
        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)



def main():
    app = QApplication(sys.argv)
    gui = Gui()
    gui.show()  


if __name__ == "__main__":
    main()