from skmultiflow.drift_detection.adwin import ADWIN
import json

ALGORITHMS = {
    "ADWIN": ADWIN
}

class Detector:
    def __init__(self, detector, trainer, logger):
        self.detector = ALGORITHMS[detector]()
        self.__trainer = trainer
        self.__logger = logger

    def on_drift_detected(self, callback):
        self._drift_detected_callback = callback

    def set_callback_drift_warning(self, callback):
        self._drift_warning_callback = callback

    def fit(self, status):
        classification = status
        self.__logger.info("updating drift detector")

        if classification["result"] == True:
            self.detector.add_element(1)
        else:
            self.detector.add_element(0)

        if self.detector.detected_change():
            self.__logger.warning("concept drift detected")
            self.__trainer.reset() # Should this happen?
            self._drift_detected_callback()

        if self.detector.detected_warning_zone():
            self.__logger.warning("concept warning detected")
            self._drift_warning_callback()
