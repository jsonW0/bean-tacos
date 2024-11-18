from helper.typing import *


class TimeTranslatorQueue:
    """
    Event queue used for Time Translation
    """

    def __init__(self):
        """
        Initializer
        """
        self.current_time: Time = 0
        self.queue: Dict[Time, Set[LinkId]] = dict()

    def schedule(self,
                 time: Time,
                 link: LinkId) -> None:
        """
        Register a link to be activated at a scheduled time.

        :param time: time to actiave a link
        :param link: link to activate at the given time
        :return: None
        """
        if time not in self.queue:
            self.queue[time] = {link}
        else:
            self.queue[time].add(link)

    def pop(self) -> Tuple[Optional[Time], Optional[Set[LinkId]]]:
        """
        Pop the immediate next time and links to be activated, if exists.

        :return: None if no event is scheduled
                 current_time and set of links to be activated if next event exists.
        """
        if len(self.queue) <= 0:  # no event exists
            return None, None

        # get next time and links
        time = min(self.queue.keys())
        links = self.queue[time]

        # update current time
        del self.queue[time]
        self.current_time = time

        return time, links
