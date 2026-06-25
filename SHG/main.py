import config
import Viewer
import SHG_Test
import zaber
import saver
import time
import threading
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
import sys

class Bridge(QObject):
    new_single = pyqtSignal(object)
    new_average = pyqtSignal(object)
    finished = pyqtSignal()

def main():
    app = QApplication(sys.argv)

    zaber_instance = zaber.Zaber()
    zaber_instance.start_Zaber(39000)

    bridge = Bridge()

    viewer = Viewer.Viewer()
    viewer.show()

    bridge.new_single.connect(viewer.update_single)
    bridge.new_average.connect(viewer.update_average)

    def on_finished():
        print("Acquisition finished")
        zaber_instance.close()

    bridge.finished.connect(on_finished)

    pulse = SHG_Test.PulseData()

    saver_instance = saver.ScanSaver()

    pulse.callback = lambda single, avg, n: (
        bridge.new_single.emit(single),
        bridge.new_average.emit(avg)
    )

    def run_acquisition():
        pulse.update()
        if config.SAVE_SCAN:
            saver_instance.save(pulse)
        bridge.finished.emit()

    threading.Thread(
        target=run_acquisition,
        daemon=True
    ).start()

    app.exec()

    # cleanup AFTER GUI loop ends
    zaber_instance.close()

if __name__ == "__main__":
    main()
