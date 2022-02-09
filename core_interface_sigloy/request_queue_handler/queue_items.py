import time

from settings import settings


class PrioritizedItem(object):
    """Prioritized item to be used inside priority queue.
        Compare operators has been overridden to use "priority"
        field for comparing purposes.
    """

    def __init__(self, init_priority: int, data: any, arrived_time=time.time()) -> None:
        self._arrival_time = arrived_time
        self._default_priority = self.priority = init_priority
        self._elapsed = 0
        self.data = data
        self.timed_out = False

    @property
    def default_priority(self):
        return self._default_priority

    @property
    def priority(self):
        # each time we use "priority" variable, this function will refresh
        # the priority according to elapsed time.
        self.prioritize()
        return self._priority

    @priority.setter
    def priority(self, v):
        # to get better view of the priority(bigger numbers)
        self._priority = v * 1000

    @property
    def elapsed(self):
        now = time.time()
        self._elapsed = now - self._arrival_time
        return self._elapsed

    def prioritize(self):
        """calculates priority again and set it"""
        # bellow zero increase the priority too fast
        if self.elapsed > 1:
            self.priority = self._default_priority / self.elapsed  # formula of the priority

    def is_timed_out(self):
        # after specific seconds item should be dropped out
        if self.elapsed > settings.REQUEST_TIMEOUT:
            return True
        return False

    def __lt__(self, other):
        return self.priority < other.priority

    def __le__(self, other):
        return self.priority <= other.priority

    def __eq__(self, other):
        return self.priority == other.priority

    def __ne__(self, other):
        return self.priority != other.priority

    def __gt__(self, other):
        return self.priority > other.priority

    def __ge__(self, other):
        return self.priority >= other.priority

    def __repr__(self):
        return f"Job(init_time: {self._arrival_time}," + \
               f"elapsed: {self.elapsed}," + \
               f"init_priority: {self._default_priority}," + \
               f"current_priority: {self._priority}, data: {self.data})"
