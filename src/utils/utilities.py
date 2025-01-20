import time
import csv
import re
from datetime import datetime

def current_ms():
    """
    Reports the current time in milliseconds
    :return: long int
    """
    return round(time.time() * 1000)

def current_date_and_time():
    """
    Reports the current date and time
    :return: long int
    """
    return datetime.now()

def write_dict_to_csv(filename, dict_item, is_first_time) -> None:
    """
    This function writes a dictionary as a row of a CSV file
    :param filename: the name of the CSV file
    :param dict_item: a dictionary containing the items to insert in the CSV file
    :param is_first_time: if True, this function writes the header before the items; if False, the file is open in append mode
    :return:
    """
    if is_first_time:
        f = open(filename, 'w', newline="")
    else:
        f = open(filename, 'a', newline="")
    w = csv.DictWriter(f, dict_item.keys())
    if is_first_time:
        w.writeheader()
    w.writerow(dict_item)
    f.close()

def get_int_number_from_string(str: str) -> int:
    """
    Function that given a string, returns the first integer number inside of it
    :param str: string
    :return: the first integer number inside the input string, if any
    """
    # Regular expression to find the first integer number inside the string
    match = re.search(r'\d+', str)
    if match:
        return int(match.group())
    else:
        return None

