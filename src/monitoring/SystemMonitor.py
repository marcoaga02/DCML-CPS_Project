import psutil
from datetime import datetime
from utils.utilities import current_ms
from utils.SystemState import SystemState

class SystemMonitor:
    """
    Class to build a system monitor to monitor the usage of resources in the system
    """
    def __init__(self, monitor_cpu: bool = True, monitor_vm: bool = True, interval_cpu_times_percent: int = 0.10, interval_cpu_cores_percent: int = 0.50):
        """
        Constructor
        :param monitor_cpu: True is CPU data has to be monitored
        :param monitor_vm: True is VM data has to be monitored
        :param interval_cpu_times_percent: CPU time percentage data collection interval duration, in seconds
        :param interval_cpu_cores_percent: CPU usage percentage data collection interval duration per core, in seconds
        """
        self.monitor_cpu = monitor_cpu
        self.monitor_vm = monitor_vm
        self.interval_cpu_times_percent = interval_cpu_times_percent
        self.interval_cpu_cores_percent = interval_cpu_cores_percent
        self.system_state = SystemState.NORMAL
        self.injector: str = "None"

    def monitor(self) -> dict:
        """
        Method that read data about the resources usage in the system
        :return:  dictionary
        """
        data_dict = {"time": current_ms(), "datetime": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        if self.monitor_cpu:
            self.cpu_probe(data_dict)
        if self.monitor_vm:
            self.vm_probe(data_dict)
        data_dict["injector"] = self.injector
        return data_dict

    def cpu_probe(self, data_dict: dict) -> None:
        """
        This method reads CPU data from the system and uses it to update the dict passed as parameter
        :param data_dict: dictionary that will be updated with the cpu data monitored
        """
        # CPU time monitoring
        cpu_t = psutil.cpu_times_percent(interval=self.interval_cpu_times_percent, percpu=True)
        for core_id, core_data in enumerate(cpu_t):
            for time_type, value in core_data._asdict().items():
                key = f"core_{core_id}_%{time_type}"
                data_dict[key] = value
    
        # CPU usage monitoring
        data_dict["freq_cpu_global_usage"] = psutil.cpu_freq().current
        cpu_percent_per_core = psutil.cpu_percent(interval=self.interval_cpu_cores_percent, percpu=True)
        cpu_freq_per_core = psutil.cpu_freq(percpu=True)
        data_dict["%cpu_global_usage"] = sum(cpu_percent_per_core)/len(cpu_percent_per_core) # CPU usage percentage is the average of all core usage percentages
        for i, perc in enumerate(cpu_percent_per_core): # this for cycle add the percentage usage of each logic core to the dictionary
            data_dict[f"%logical_core_{i}_usage"] = perc
            data_dict[f"freq_logical_core_{i}_usage"] = cpu_freq_per_core[i].current
 
        # CPU physical cores temperatures monitoring
        temperatures = psutil.sensors_temperatures()
        count = 0
        for _, temp in enumerate(temperatures["coretemp"]):
            if "Core" in temp.label:
                data_dict[f"physical_core_{count}_temp"] = temp.current
                count += 1
  
    def vm_probe(self, data_dict: dict) -> None:
        """
        This method reads VM data from the system and uses it to update the dict passed as parameter
        :param data_dict: dictionary that will be updated with the VM data monitored
        """
        vm_data = psutil.virtual_memory()._asdict()
        for type, data in vm_data.items():
            data_dict["virtual_mem_"+type] = data

    def start_injection(self, injector: str) -> None:
        """
        This method  is called when a fault injection is started and set the system state to under fault injection and save the type of fault injected into the system
        :param injector: the type of the fault injected into the system
        :return:
        """
        self.system_state = SystemState.UNDER_INJECTION
        self.injector = injector

    def end_injection(self) -> None:
        """
        This method is called when a fault injection is finished to set the system state to normal
        """
        self.system_state = SystemState.NORMAL
        self.injector = "None"

    def get_system_state(self) -> SystemState:
        return self.system_state
    
    def get_estimation_monitoring_time_per_obs(self) -> float:
        """
        This method gives an estimation of the time needed to monitor the system at each observation
        :return: the estimation of the time needed to monitor
        """
        return self.interval_cpu_times_percent + self.interval_cpu_cores_percent
  