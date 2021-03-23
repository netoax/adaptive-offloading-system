from skmultiflow.drift_detection.adwin import ADWIN

ALGORITHMS = {
    "ADWIN": ADWIN
}

class Detector:
    def __init__(self, detector, model):
        self.detector = ALGORITHMS[detector]
        self.model = model

    def set_callback_drift_detected(self, callback):
        self._drift_detected_callback = callback

    def set_callback_drift_warning(self, callback):
        self._drift_warning_callback = callback

    def fit(self, status):
        if status == True:
            self.detector.add_element(1)
        else:
            self.detector.add_element(0)

        if self.detector.detected_change():
            self.logger.info("concept drift detected")
            self.model.reset() # Should this happen?
            self._drift_detected_callback()

        if self.detector.detected_warning_zone():
            self.logger.info("concept warning detected")
            self._drift_warning_callback()
