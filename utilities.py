import os
from string import ascii_letters, digits
from random import choice
from threading import Lock


def as_seconds(time_str):
    mult = 1
    seconds = 0
    time_components = time_str.split(':')
    while time_components:
        seconds += int(time_components.pop().strip()) * mult
        mult *= 60
    return seconds


def random_string(length=26, chars=ascii_letters + digits):
    return ''.join([choice(chars) for _ in range(length)])
    

def search_file_recursively(filename, search_path="."):
    result = []
    for root, _, files in os.walk(search_path):
        if filename in files:
            result.append(os.path.join(root, filename))
    return result


def file_exists(file_path):
    return os.path.exists(file_path)


def override(method):
    method.is_overridden = True
    return method


def synchronized(method):
    outer_lock = Lock()
    lock_name = "__" + method.__name__ + "_lock" + "__"

    def wrapper(self, *args, **kws):
        with outer_lock:
            if not hasattr(self, lock_name):
                setattr(self, lock_name, Lock())
            lock = getattr(self, lock_name)
            with lock:
                return method(self, *args, **kws)

    return wrapper