from helper.typing import *
import heapq


class EventQueue:
    """
    Event Queue implementation

    This can be viewed as a min-heap but all elements are unique (no duplicates)
    """

    def __init__(self):
        """
        Initializer

        """
        self.current_time = 0  # track current time

        self.event_queue = list()
        self.events: Set[Time] = set()  # used to track the uniqueness of each element

    def schedule(self,
                 next_time: Time) -> None:
        """
        Add a new times to the event_queue, if it's unique.

        :param next_time: next time to add to the queue
        :return: None
        """

        # check the uniqueness
        if next_time in self.events:
            return

        # do min-heap insertion
        heapq.heappush(self.event_queue, next_time)
        self.events.add(next_time)

    def pop(self) -> Optional[Time]:
        """
        Pop next time from the heap

        :return: next time value to be processed, if exists.
                 None is the eveyt_queue is empty
        """
        if len(self.event_queue) <= 0:
            return None

        # return heap element
        time = heapq.heappop(self.event_queue)
        self.events.remove(time)

        # update current time
        self.current_time = time

        return time

    def empty(self) -> bool:
        """
        Check whether the event queue is empty.

        :return: True if no event is assigned, False otherwise.
        """
        return len(self.events) == 0
