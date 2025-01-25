# Project for the course _Data Collection and Machine Learning for Critical Cyber-Physical Systems_
Master degree in _Software: Science and Technology_
### Instruction for Ubuntu 24.04
This project is designed to work on Linux because the system monitor relies on some `psutil` functions that are compatible only with Linux.  
If needed, you can modify the file `SystemMonitor.py` to use equivalent `psutil` functions compatible with Windows.  
To run the project, follows these steps:
1. Create and activate a virtual environment: 
``` bash
python3 -m venv venv  
source venv/bin/activate
```
2. Install all dependencies:
``` bash
pip install -r requirements.txt
```
3. Navigate to the project's main directory (e.g., DCML-CPS_Project) and execute the following command to monitor and gather system data:
``` bash
python3 src/main.py  
```
The execution lasts approximately 2.5 hours. If you wish to reduce this duration, you can modify the parameters in the file `main.py` to collect fewer data points.
4. If you only want to run the anomaly detection system, use the following command instead:
``` bash
python3 src/main_anomaly_detector.py  
```

## Folder Structure
DCML-CPS_Project/
|
|---log/ # contains log files generated during the execution of the file main_anomaly_detector.py
|      |--- datapoint_with_predictions.log
|      |--- predictions_with_severity_level.log
|
|---output_folder/ # contains the CSV generated during the execution of the file main.py
|	|--- DCML_Project_dataset.csv # file CSV of the dataset
|
|---saved_models/
|	|--- best_model_stacking.pkl # file of the model with best Accuracy and MCC (Stacking Classifier)
|	|--- scaler.pkl # file of the standard scaler to use at run time (fitted on the training set of the model)
|
|---src/
|      |---monitoring/
|      |          |--- AnomalyDetector.py # class of the anomaly detector
|      |          |--- InjectionManager.py # class to handle injection in the system
|      |          |--- LoadInjector.py # class to load/start/stop injection
|      |          |--- SystemMonitor.py # class to monitor the usage of system’s resources
|      |
|      |---utils/
|      |        |--- SeverityLevel.py # enum to represents the severity level of an ongoing anomaly
|      |        |--- SystemState.py # enum to represents the state of the system
|      |        |--- utilities.py # contains utility functions
|      |
|      |--- DCML_Colab_Project_Agatensi.ipynb # Notebook Google Colab for ML part
|      |--- debug_injectors.json # json used if debug is enabled during monitoring/injection
|      |--- injectors_json.json # json used if debug is disabled
|      |--- main_anomaly_detector.py # main to be executed to run the Anomaly Detector
|      |--- main.py # main to be executed to run the monitoring/injection to build the dataset
|
|--- test_Anomaly_Detector/
|	|--- stress_cycles.sh # shell’s script to stress the system to test the final Anomaly Detector
|
|--- ProjectReport.pdf # Report of the project
|--- README.txt # contains instructions to run the code
|--- requirements.txt # python requirements to run all main*.py files

