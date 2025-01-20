import pandas as pd
import os.path
import threading
from monitoring.SystemMonitor import SystemMonitor
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import StackingClassifier
from utils.SeverityLevel import SeverityLevel
from utils.utilities import current_date_and_time, write_dict_to_csv
from collections import OrderedDict

TRESHOLD_TO_RESET_FLAG = 5
OUT_FOLDER = "output_folder"
LOG_DATAPOINT_AND_PREDICTION_FILENAME = "datapoint_with_predictions.log"
LOG_PREDICTIONS_AND_SEVERITY_LEVEL = "predictions_with_severity_level.log"

class AnomalyDetector():

    def __init__(self, model_clf: StackingClassifier, scaler: StandardScaler = None, monitor: SystemMonitor = SystemMonitor(), feature_to_avoid: list = None):
        """
        Constructor
        :param model_clf: StackingClassifier already trained to use as anomaly detector
        :param scaler: StandardScaler, fitted on the training set used to train the model, to apply to monitored data before to give them in input to the model
        :param monitor: instance of the monitor
        :param feature_to_avoid: list of features to do not give in input to the model
        """
        self.model_clf = model_clf
        self.scaler = scaler  
        self.monitor = monitor  
        self.feature_to_avoid = feature_to_avoid
        self.init()

    def init(self):
        self.is_alive: bool = False
        self.thread_detection = None
        self.severity_level = SeverityLevel.LEVEL_5
        if not os.path.exists(OUT_FOLDER):
            os.mkdir(OUT_FOLDER)
        self.dp_log_filename = os.path.join(OUT_FOLDER, LOG_DATAPOINT_AND_PREDICTION_FILENAME) # path to the log file that stores each datapoint + the prediction of the model on it
        self.sl_log_filename = os.path.join(OUT_FOLDER, LOG_PREDICTIONS_AND_SEVERITY_LEVEL) # path to the log file that stores the prediction of the model on each datapoint + the current severity level

    def detect_anomalies(self) -> None:
        """
        Method that monitor system in loop until the stop method is called to detect ongoing anomalies.
        This method should not be called from the outside of the class.
        """
        with self.lock:
            dp_log_filename = self.dp_log_filename
            sl_log_filename = self.sl_log_filename
            current_sl = self.severity_level
        
        num_anomalies_detec: int = 0 # number of anomalies currently detected
        reset_flag: int = 0 # this is incremented each time a normal behavior is detected. If its value reaches a treshold (TRESHOLD_TO_RESET_FLAG), the num_anomalies_detec variable is set to zero.
                            # This is the case when after a long anomaly is detected, the system is detected as normal enough times to be considered safe
        is_first_time: bool = True
        while not self.force_stop.is_set():
            with self.lock:
                datapoint_monitored: dict = self.monitor.monitor()

                for item in self.feature_to_avoid:
                    del datapoint_monitored[item]

                datapoint = pd.DataFrame([datapoint_monitored])
                if self.scaler is not None:
                    datapoint_std = self.scaler.transform(datapoint)
                anomaly_detected: bool = (self.model_clf.predict(datapoint_std) == 1)
                predicted_proba: float = self.model_clf.predict_proba(datapoint_std)
                if anomaly_detected:
                    num_anomalies_detec += 1
                    reset_flag = 0
                elif reset_flag >= TRESHOLD_TO_RESET_FLAG:
                    reset_flag = 0
                    num_anomalies_detec = 0
                elif num_anomalies_detec > 0:
                    reset_flag += 1
                    num_anomalies_detec -= 1

                self.update_severity_level(num_anomalies_detec)
                self.raise_alert(anomaly_detected)
                current_sl = self.severity_level

            self.log_system_info(datapoint_monitored, prediction="ANOMALY DETECTED" if anomaly_detected else "NORMAL STATE", predicted_proba=predicted_proba,
                                 is_first_time=is_first_time, dp_log_fn=dp_log_filename, sl_log_fn=sl_log_filename,
                                 severity_level=current_sl)
            is_first_time=False

    def start_anomaly_detection(self) -> None:
        """
        Method to call to start run-time anomaly detection
        """
        if self.thread_detection is None or not self.thread_detection.is_alive():
            self.force_stop = threading.Event()
            self.lock = threading.Lock()
            self.thread_detection = threading.Thread(target=self.detect_anomalies)
            self.thread_detection.start()
            self.is_alive = True
            print("The anomaly detector has been started")
        else:
            print("Anomaly detector is already running")

    def stop(self) -> None:
        """
        Method to call to stop ongoing run-time anomaly detection
        """
        if self.thread_detection is not None:
            self.force_stop.set()
            self.thread_detection.join()
            self.thread_detection = None
            self.is_alive = False
            print("The anomaly detector has been stopped")

    def raise_alert(self, ongoing_anomaly: bool) -> None:
        """
        Method to manage the raising of a message, that depends on the current severity anomaly's level
        """
        alert_msg: str = "ANOMALY DETECTED" if ongoing_anomaly else "NORMAL STATE"
        match self.severity_level:
            case SeverityLevel.LEVEL_1:
                alert_msg = f"{alert_msg} - Critical anomaly detected! Immediate action is mandatory to avoid system failure."
            case SeverityLevel.LEVEL_2:
                alert_msg = f"{alert_msg} - High anomaly detected! Action is required to prevent potential issues."
            case SeverityLevel.LEVEL_3:
                alert_msg = f"{alert_msg} - Moderate anomaly detected. Investigate potential causes and take preemptive measures."
            case SeverityLevel.LEVEL_4:
                alert_msg = f"{alert_msg} - Low-level anomaly detected. Monitor the system closely for any changes."
            case SeverityLevel.LEVEL_5:
                alert_msg = f"{alert_msg} - System is operating normally. No action required."
        print(alert_msg)

    def update_severity_level(self, num_obs_anomalies: int):
        """
        This function updates the severity level of the system after each monitoring
        """
        if num_obs_anomalies >= 15:
            self.severity_level = SeverityLevel.LEVEL_1
        elif num_obs_anomalies >= 10:
            self.severity_level = SeverityLevel.LEVEL_2
        elif num_obs_anomalies >= 4:
            self.severity_level = SeverityLevel.LEVEL_3
        elif num_obs_anomalies >= 1:
            self.severity_level = SeverityLevel.LEVEL_4
        else:
            self.severity_level = SeverityLevel.LEVEL_5

    def is_detecting(self) -> bool:
        """
        Method that returns True if the anomaly detection in running; otherwise it returns false
        """
        return self.is_alive
    
    def log_system_info(self, dict_item: dict, prediction, predicted_proba, is_first_time, dp_log_fn, sl_log_fn, severity_level) -> None:
        """
        Method to log in a CSV format info about the system and predictions made by the classifier into two log files dp_log_fn and sl_log_fn
        :param dict_item: dictionary to log into the log file dp_log_fn
        :param prediction: string representing the prediction made by the classifier
        :param predicted_proba: string representing the prediction probability computed by the classifier
        :param is_first_time: True means that is the first log to files
        :param dp_log_fn: name of the log file in which log info about date + time, prediction, predicted probability and datapoints on which the model make predictions
        :param sl_log_fn: name of the log file in which log info about date + time, prediction, predicted probability and the current severity level
        :param severity_level: the current severity level of the system
        :return:
        """
        date_and_time_of_monitoring = current_date_and_time()
        dict_dp = {
            'date_and_time': str(date_and_time_of_monitoring),
            'prediction': str(prediction),
            'predicted_proba': str(predicted_proba)
        }
        dict_dp.update(dict_item)
        
        write_dict_to_csv(dp_log_fn, dict_dp, is_first_time)

        match severity_level:
            case SeverityLevel.LEVEL_1:
                sev_level_string = "LEVEL 1 - Critical anomaly detected"
            case SeverityLevel.LEVEL_2:
                sev_level_string = "LEVEL 2 - High anomaly detected"
            case SeverityLevel.LEVEL_3:
                sev_level_string = "LEVEL 3 - Moderate anomaly detected"
            case SeverityLevel.LEVEL_4:
                sev_level_string = "LEVEL 4 - Low-level anomaly detected"
            case SeverityLevel.LEVEL_5:
                sev_level_string = "LEVEL 5 - System is operating normally"

        dict_sl = OrderedDict([('date_and_time', date_and_time_of_monitoring), ('prediction', prediction), ('predicted_proba', predicted_proba), ('severity_level', sev_level_string)],)
        write_dict_to_csv(sl_log_fn, dict_sl, is_first_time)



