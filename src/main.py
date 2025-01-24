import os.path
from time import sleep
from monitoring.SystemMonitor import SystemMonitor
from monitoring.InjectionManager import InjectionManager
from utils.utilities import write_dict_to_csv
from utils.SystemState import SystemState

DEBUG: bool = True

if __name__ == "__main__":
    """
    Main method that starts a system monitoring by alternating normal behavior with abnormal behavior due to fault injection
    """

    # General variables
    csv_filename = 'DCML_Project_dataset.csv'
    out_folder = 'output_folder'

    if not DEBUG:
        obs_per_inj = 80 # number of observation for each injection
        obs_norm_behav = 120 # number of observation to do after each injection
        inj_number = 60 # number of injection to perform
        inj_json = 'src/injectors_json.json'
        verbose = True
    else:
        obs_per_inj = 10 # number of observation for each injection
        obs_norm_behav = 15 # number of observation to do after each injection
        inj_number = -1 # number of injection to perform
        inj_json = 'src/injectors_json.json'
        #inj_json = 'src/debug_injectors.json'
        verbose = True
    sleep_time_after_obs = 0.1 # time to sleep before to make a new observation

    # Checking if output_folder already exists: if yes, delete
    if not os.path.exists(out_folder):
        os.mkdir(out_folder)

    # Checking if csv_filename already exists: if yes, delete
    csv_filename = os.path.join(out_folder, csv_filename)
    if os.path.exists(csv_filename):
        os.remove(csv_filename)

    monitor = SystemMonitor()

    real_time_between_obs = sleep_time_after_obs + monitor.get_estimation_monitoring_time_per_obs()

    injection_manager = InjectionManager(json_object=inj_json, obs_per_inj=obs_per_inj, inj_number=inj_number, inj_duration=obs_per_inj*real_time_between_obs*1000, verbose=verbose)
    injection_manager.read_injectors(shuffle=True) # fill up the list of injectors with those specified in the JSON file and perform a shuffle of the elements in the list
    
    # Variables used in the loop as flags to do the "switch" between normal and abnormal behavior of the system
    num_obs_done: int = 0
    num_obs_to_do: int = obs_norm_behav # the process starts monitoring the normal behavior of the system
    
    is_first_time: bool = True

    while True:
        if num_obs_to_do - num_obs_done > 0:
            monitored_data = monitor.monitor()
            write_dict_to_csv(csv_filename, monitored_data, is_first_time)
            is_first_time = False
            num_obs_done += 1
            sleep(sleep_time_after_obs)
        else:
            if monitor.get_system_state() == SystemState.NORMAL: # starts an injection
                if not injection_manager.injectors_list_is_empty():
                    monitor.start_injection(injection_manager.inject_fault())
                    num_obs_to_do = obs_per_inj
                else:
                    break
            else: # stops the current injection
                injection_manager.stop_injection()
                monitor.end_injection()
                num_obs_to_do = obs_norm_behav
                if injection_manager.injectors_list_is_empty():
                    break 
            num_obs_done = 0
    
    print("Monitoring finished. All fault injections performed correctly!\nYou can find all monitored data in the output folder in the CSV file DCML_Project_dataset.csv")