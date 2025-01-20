import json
import random
import os
from .LoadInjector import LoadInjector

class InjectionManager:
    """
    Class to manage easily fault injections given a JSON file containing the description of each fault injection
    """

    def __init__(self, json_object, inj_duration, obs_per_inj: int, inj_number: int = -1, verbose: bool = False):
        """
        Constructor
        :param json_object: the json object or file containing a json object
        :param inj_duration: estimated duration of each fault injection in milliseconds
        :param obs_per_inj: number of observation per injection
        :param inj_number: number of injection to perform. If the injectors in the json are less, injectors are replicated randomly to reach this value. 
            In case of default value -1, the number of injections to perform are those in the json file
        :param verbose: True is debug information has to be shown 
        """
        self.json_object = json_object      
        self.inj_duration = inj_duration
        self.obs_per_inj = obs_per_inj
        self.inj_number = inj_number
        self.verbose = verbose
        self.injectors = []
        self.current_inj: LoadInjector = None
        self.num_inj_already_performed = 0 # this is the number of injection already performed

    def read_injectors(self, shuffle: bool = False) -> None:
        """
        Method to read a JSON object and extract injectors into a list based on the following parameters
        :param shuffle: if True the list of available injectors is randomly shuffled before being returned
        """
        try:
            json_object = json.loads(self.json_object)
        except ValueError:
            if os.path.exists(self.json_object):
                with open(self.json_object) as f:
                    json_object = json.load(f)
            else:
                print("Could not parse input %s" % self.json_object)
                json_object = None
        number_of_inj = len(json_object)

        if self.inj_number != -1 and self.inj_number < number_of_inj:
            self.inj_number = -1 # default value
            print("Wrong value inj_number. Set to default value -1") # a sort of defensive initialization to make this class more robust

        json_injectors = []
        if json_object is not None:
            # Means it is a JSON object
            json_injectors = []
            for job in json_object:
                job["duration_ms"] = self.inj_duration
                new_inj = LoadInjector.fromJSON(job)
                if new_inj is not None and new_inj.is_valid():
                    # Means it was a valid JSON specification of an Injector
                    json_injectors.append(new_inj)
                    self.if_verbose('New injector loaded from JSON: %s' % new_inj.get_name())

        if not json_injectors:
            raise ValueError("No valid injectors found in the input JSON")

        number_of_inj_to_add = self.inj_number - len(json_injectors) if self.inj_number != -1 else 0
        while number_of_inj_to_add > 0:
            random_job = random.choice(json_object)
            random_job["duration_ms"] = self.inj_duration
            new_inj = LoadInjector.fromJSON(random_job)
            if new_inj is not None and new_inj.is_valid():
                json_injectors.append(new_inj)
                number_of_inj_to_add -= 1
                self.if_verbose('New injector loaded randomly from JSON to reach the inj_number value: %s' % new_inj.get_name())
        
        self.if_verbose("The number of injections to perform is " + str(len(json_injectors)))

        if shuffle:
            random.shuffle(json_injectors)
            self.if_verbose("The list of injectors has been shuffled")

        self.injectors = json_injectors
    
    def inject_fault(self) -> str:
        """
        Method to inject the next fault of the list of injectors (if there are no injections ongoing)
        :return: the type of the injected fault
        """
        if not self.injectors_list_is_empty() and self.current_inj is None:
            self.current_inj = self.injectors.pop(0)
            self.if_verbose("Injecting with injector '%s'" % self.current_inj.get_name())
            # Starts the injection
            self.current_inj.inject()
            return self.current_inj.get_name()
        else:
            print("All injectors have been injected. None available for injection")
            return None

    def stop_injection(self) -> None:
        """
        Method to stop the current fault injection
        """
        if self.current_inj is not None:
            self.if_verbose("Stop of the injection of injector '%s'" % self.current_inj.get_name())
            self.current_inj.force_close()
            self.current_inj = None
        else:
            self.if_verbose("There are no ongoing injections to stop")

    def injectors_list_is_empty(self) -> bool:
        """
        This method check if the injectors are finished
        :return: True if injectors are finished
        """
        return not self.injectors
    
    def set_debug(self, activate: bool = False) -> None:
        """
        Method to activate/deactivate debug information
        :param activate: True is debug information has to be shown
        """
        self.verbose = activate
        if activate:
            self.if_verbose('Debug information activated')
        else:
            self.if_verbose('Debug information deactivated')

    def if_verbose(self, msg: str):
        if self.verbose:
            print(msg)