import joblib
from time import sleep
from monitoring.AnomalyDetector import AnomalyDetector
from monitoring.SystemMonitor import SystemMonitor
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import StackingClassifier

if __name__ == "__main__":
     stacking_classifier: StackingClassifier = joblib.load('saved_models/best_model_stacking.pkl')
     standard_scaler: StandardScaler = joblib.load('saved_models/scaler.pkl')
 
     features_to_remove = ['time', 'datetime','virtual_mem_total','injector',\
                                          'core_0_%nice', 'core_0_%iowait', 'core_0_%softirq', 'core_0_%irq', 'core_0_%steal', 'core_0_%guest', 'core_0_%guest_nice',\
                                          'core_1_%nice', 'core_1_%iowait', 'core_1_%softirq', 'core_1_%irq', 'core_1_%steal', 'core_1_%guest', 'core_1_%guest_nice',\
                                          'core_2_%nice', 'core_2_%iowait', 'core_2_%softirq', 'core_2_%irq', 'core_2_%steal', 'core_2_%guest', 'core_2_%guest_nice',\
                                          'core_3_%nice', 'core_3_%iowait', 'core_3_%softirq', 'core_3_%irq', 'core_3_%steal', 'core_3_%guest', 'core_3_%guest_nice',\
                                          'core_4_%nice', 'core_4_%iowait', 'core_4_%softirq', 'core_4_%irq', 'core_4_%steal', 'core_4_%guest', 'core_4_%guest_nice',\
                                          'core_5_%nice', 'core_5_%iowait', 'core_5_%softirq', 'core_5_%irq', 'core_5_%steal', 'core_5_%guest', 'core_5_%guest_nice',\
                                          'core_6_%nice', 'core_6_%iowait', 'core_6_%softirq', 'core_6_%irq', 'core_6_%steal', 'core_6_%guest', 'core_6_%guest_nice',\
                                          'core_7_%nice', 'core_7_%iowait', 'core_7_%softirq', 'core_7_%irq', 'core_7_%steal', 'core_7_%guest', 'core_7_%guest_nice']
                                             
     anomaly_detector = AnomalyDetector(stacking_classifier, standard_scaler, SystemMonitor(interval_cpu_cores_percent=0.9), features_to_remove)
     anomaly_detector.start_anomaly_detection()
     try:
          print("Press Ctrl+C to stop the anomaly detector")
          while anomaly_detector.is_detecting():
               sleep(0.5)
     except KeyboardInterrupt:
          anomaly_detector.stop()
