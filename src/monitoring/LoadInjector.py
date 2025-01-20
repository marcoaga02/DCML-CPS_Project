import threading
import time
import random
import multiprocessing
from utils.utilities import current_ms, get_int_number_from_string
from cpu_load_generator import load_all_cores, load_single_core
from monitoring.SystemMonitor import SystemMonitor     

# ABSTRACT CLASS FOR INJECTIONS
class LoadInjector:
    """
    Abstract class for Injecting Errors in the System
    Should you want to implement your own injector, just extend/override this class
    """

    def __init__(self, tag: str = '', duration_ms: float = 0):
        """
        Constructor
        """
        self.valid = True
        self.tag: str = tag
        self.duration_ms = duration_ms
        self.inj_thread = None
        self.completed_flag = True
        self.start_inj_time = 0
        self.end_inj_time = 0
        self.injected_interval = []
        self.init()

    def is_valid(self) -> bool:
        return self.valid

    def init(self):
        """
        Override needed only if the injector needs some pre-setup to be run. Default is an empty method
        :return:
        """
        pass

    def inject_body(self):
        """
        Abstract method to be overridden
        """
        pass

    def inject(self):
        """
        Caller of the body of the injection mechanism, which will be executed in a separate thread
        """
        self.inj_thread = threading.Thread(target=self.inject_body, args=())
        self.inj_thread.start()

    def is_injector_running(self):
        """
        True if the injector has finished working (end of the 'injection_body' function)
        """
        return not self.completed_flag

    def force_close(self):
        """
        Tries to force-close the injector
        """
        pass

    def get_injections(self) -> list:
        """
        Returns start-end times of injections exercised with this method
        """
        return self.injected_interval

    def get_name(self) -> str:
        """
        Abstract method to be overridden, provides a string description of the injector
        """
        return "[" + self.tag + "]Injector" + "(d" + str(self.duration_ms) + ")"

    @classmethod
    def fromJSON(cls, job):
        """
        This function allows to create an instance of an injector from a json description of the injector
        :param job: the JSON description of the injector
        :return: the injector object (subclass of LoadInjector)
        """
        if job is not None:
            if 'type' in job:
                if job['type'] in {'Memory', 'RAM', 'MemoryUsage', 'Mem', 'MemoryStress'}:
                    return MemoryStressInjection.fromJSON(job)
                if job['type'] in {'CPU', 'Proc', 'CPUUsage', 'CPUStress'}:
                    return CPUStressInjection.fromJSON(job)
        return None


# SUBCLASSES OF THE LOADINJECTOR CLASS

class CPUStressInjection(LoadInjector):
    """
    CPUStress Error, execute an external process to stress the entire CPU or a specific core
    without storing results anywhere
    """

    def __init__(self, tag: str = '', duration_ms: float = 0):
        """
        Constructor
        """
        LoadInjector.__init__(self, tag, duration_ms)

    def inject_body(self):
        """
        Method to call to start the CPU stress injection
        """
        self.completed_flag = False
        self.start_inj_time = current_ms()
        self.stop_inj = multiprocessing.Event()
        if self.tag == "CPU_default":
            self.load_process = multiprocessing.Process(target=self.stress_cpu, args=())
        else:
            core_number = get_int_number_from_string(self.tag)
            self.load_process = multiprocessing.Process(target=self.stress_logical_core, args=(core_number,))
        self.load_process.start()

    def force_close(self):
        """
        Method to call when you want to stop a CPU fault injection
        """
        self.completed_flag = True
        self.stop_inj.set()
        self.load_process.join()      
        self.end_inj_time = current_ms()
        self.injected_interval.append({'start': self.start_inj_time, 'end': self.end_inj_time})

    def get_name(self) -> str:
        """
        Method to get a string description of the injected fault
        """
        return "[" + self.tag + "]CPUStressInjection" + "(d" + str(self.duration_ms) + ")"
    
    def stress_cpu(self):
        """
        Method to be used to stress the whole CPU.
        """
        while not self.stop_inj.is_set():
            if random.choice([True, False]): # randomly, if True CPU Overloaded to 100%
                load_all_cores(0.8, 1)
            else:
                load_all_cores(0.8, random.uniform(0.9, 1))
    
    def stress_logical_core(self, core_number: int):
        """
        Method to stress a specific core of the cpu
        :param core_number: the id number of the core to be stressed
        """
        cpu_monitor = SystemMonitor(monitor_cpu=True, monitor_vm=False, interval_cpu_cores_percent=0.2, interval_cpu_times_percent=0)
        shared_cpu_data = {}
        lock = threading.Lock()
        self.dict_fill = threading.Event()
        self.stop_monitoring = threading.Event()
        monitor_thread = threading.Thread(target=self.monitor_cpu_in_loop, args=(cpu_monitor, shared_cpu_data, lock))
        monitor_thread.start()
        self.dict_fill.wait() # the first time it waits for the dictionary to be filled
        while not self.stop_inj.is_set():
            with lock:
                logical_core_usage = {
                    str(k): v for k, v in shared_cpu_data.items() if str(k).startswith("%logical_core_") and str(k).endswith("_usage") and get_int_number_from_string(str(k)) != core_number
                }
            target_load = min(100, max(logical_core_usage.values()) + random.uniform(50, 80)) # we get the maximum core load, we sum to it a number between 50 and 80 and if this value is over 100, we set the target load of the core at 100
            if random.choice([True, False]): # randomly, if True CPU core Overloaded to 100%
                load_single_core(core_number, 0.8, 1)
            else:
                load_single_core(core_number, 0.4, target_load/100)
        self.stop_monitoring.set()
        monitor_thread.join()

    def monitor_cpu_in_loop(self, cpu_monitor: SystemMonitor, data_dict: dict, lock) -> None:
        """
        Method to update a shared dict with information about the CPU
        :param cpu_monitor: object of type SystemMonitor to monitor CPU data
        :param data_dict: shared dict updated by this method
        :param lock: lock on the shared dict data_dict 
        """
        while not self.stop_monitoring.is_set():
            cpu_data = cpu_monitor.monitor()
            with lock:
                data_dict.clear()
                data_dict.update(cpu_data)
                self.dict_fill.set()

    @classmethod
    def fromJSON(cls, job):
        return CPUStressInjection(tag=(job['tag'] if 'tag' in job else ''),
                                  duration_ms=(job['duration_ms'] if 'duration_ms' in job else 0))


class MemoryStressInjection(LoadInjector):
    """
    Loops and adds data to an array simulating memory usage
    """

    def __init__(self, tag: str = '', duration_ms: float = 0, items_for_loop: int = 1234567):
        """
        Constructor
        """
        LoadInjector.__init__(self, tag, duration_ms)
        self.items_for_loop = items_for_loop

    def inject_body(self):
        """
        Method to call to start the VM stress injection
        """
        self.completed_flag = False
        self.start_inj_timetime = current_ms()
        self.stop_inj = multiprocessing.Event()
        self.load_process = multiprocessing.Process(target=self.stress_virtual_memory, args=())
        self.load_process.start()

    def force_close(self):
        """
        Method to call when you want to stop a VM fault injection
        """
        self.completed_flag = True
        self.stop_inj.set()
        self.load_process.join()
        self.end_inj_time = current_ms()
        self.injected_interval.append({'start': self.start_inj_time, 'end': self.end_inj_time})

    def get_name(self) -> str:
        """
        Method to get a string description of the injected fault
        """
        return "[" + self.tag + "]MemoryStressInjection(d" + str(self.duration_ms) + "-i" \
               + str(self.items_for_loop) + ")"
    
    def stress_virtual_memory(self):
        """
        Method to be used to stress the VM.
        """
        my_list = []
        vm_monitor = SystemMonitor(monitor_cpu=False, monitor_vm=True, interval_cpu_cores_percent=0.4, interval_cpu_times_percent=0)
        shared_vm_data: dict = {}
        lock = threading.Lock()
        self.dict_fill = threading.Event()
        self.stop_monitoring = threading.Event()
        monitor_thread = threading.Thread(target=self.monitor_vm_in_loop, args=(vm_monitor, shared_vm_data, lock))
        monitor_thread.start()
        self.dict_fill.wait()
        while not self.stop_inj.is_set():
            with lock:
                perc_vm_usage = shared_vm_data["virtual_mem_percent"]

            if perc_vm_usage > 90: # we clean a part of the VM to avoid a system crash
                num_to_clear = int(len(my_list) * random.uniform(0.2, 0.8))
                my_list = my_list[num_to_clear:]

            my_list.append([999 for i in range(0, self.items_for_loop)])
            time.sleep(0.001)
        self.stop_monitoring.set()
        monitor_thread.join()
    
    def monitor_vm_in_loop(self, vm_monitor: SystemMonitor, vm_shared_data: dict, lock) -> None:
        """
        Method to update a shared dict with information about the percentage of VM used
        :param vm_monitor: object of type SystemMonitor to monitor vm data
        :param vm_shared_data: shared dict updated by this method
        :param lock: lock on the shared dict vm_shared_data 
        """
        while not self.stop_monitoring.is_set():
            vm_data = vm_monitor.monitor()
            vm_perc_usage = {"virtual_mem_percent": vm_data.get("virtual_mem_percent")}
            with lock:
                vm_shared_data.clear()
                vm_shared_data.update(vm_perc_usage)
                self.dict_fill.set()
            time.sleep(0.5)

    @classmethod
    def fromJSON(cls, job):
        return MemoryStressInjection(tag=(job['tag'] if 'tag' in job else ''),
                                     duration_ms=(job['duration_ms'] if 'duration_ms' in job else 0),
                                     items_for_loop=(job['items_for_loop']
                                                     if 'items_for_loop' in job else 1234567))
