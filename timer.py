from threading import Thread
from time import sleep
from utilities import synchronized, override


class Timer(Thread):
    # Fields related to time are all represented as seconds
    def __init__(self, duration=None, cycle=1.0):
        Thread.__init__(self)
        self.current_time = 0
        self.duration = duration
        self.cycle = cycle
        self.stop = False

    @override
    def run(self):
        while not self.stop and not self.reach_end():
            self.time_increment()
            sleep(self.cycle)

    @synchronized
    def abort(self):
        self.stop = True

    @synchronized
    def reach_end(self):
        if self.duration is None:
            return False
        else:
            return self.get_current_time() >= self.duration

    @synchronized
    def get_current_time(self):
        return self.current_time 

    @synchronized
    def time_increment(self):
        self.current_time += 1
