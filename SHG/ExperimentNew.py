import config
import Viewer
import daq
import zaber
import saver
import time
import threading
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
import sys

class Experiment(QObject):
    finished = pyqtSignal()
    new_single = pyqtSignal(object)
    new_average = pyqtSignal(object)

    def __init__(
        self,
        File=config.FILE_INFO,
        Polarization=config.POLARIZATION_MODE,
        Averages=config.AVERAGES,
        Save_scan=config.SAVE_SCAN
    ):
        super().__init__()

        self.File = File
        self.Polarization = Polarization
        self.Averages = Averages
        self.Save_scan = Save_scan
    
    def start(self):
        self.zaber = zaber.Zaber(
            POLARIZATION_MODE=self.Polarization
        )
        self.zaber.main(39000)

        self.pulse = daq.PulseData(
            averages=self.Averages
        )

        self.saver = saver.ScanSaver(
            File=self.File
        )

        self.pulse.callback = self._callback

        threading.Thread(
            target=self._run_acquisition,
            daemon=True
        ).start()

    def _callback(self, single, avg, n):
        self.new_single.emit(single)
        self.new_average.emit(avg)

    def _run_acquisition(self):
        self.pulse.update()

        if self.Save_scan:
            self.saver.save(self.pulse)

        self.zaber.close()
        self.finished.emit()