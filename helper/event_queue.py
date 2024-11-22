from helper.typing import *
import heapq
from collections import defaultdict


class EventQueue:
    """
    Event Queue is just a min-heap priority queue
    """
    def __init__(self):
        self.event_queue: List[Time] = []
        self.event_times: Set[Time] = set()
        self.events: Dict[Time,List[Event]] = defaultdict(list)

    def push(self, event: Event) -> None:
        """
        Add a new event to the event_queue
        :param event: next event to add to the queue
        """
        edge,chunk,send_time,receive_time = event
        if receive_time not in self.event_times:
            heapq.heappush(self.event_queue, receive_time)
            self.event_times.add(receive_time)
        self.events[receive_time].append(event)

    def pop(self) -> Optional[Tuple[Time,List[Event]]]:
        """
        Pop next time from the heap
        """
        if len(self.event_queue) <= 0:
            return None
        time = heapq.heappop(self.event_queue)
        events = self.events.pop(time)
        return time, events

    def empty(self) -> bool:
        return len(self.events) == 0
