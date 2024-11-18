from helper.typing import *
import numpy as np
from time_translator.npu import Npu
from time_translator.link import Link
from time_translator.time_translator_queue import TimeTranslatorQueue
from topology.topology import Topology
from collective.collective import Collective


class SimpleTranslator:
    """
    Time domain translation (TEN -> continuous)
    Assuming no congestion happens -- no arbitration (ordering) required.
    """

    def __init__(self,
                 topology: Topology,
                 collective: Collective,
                 ordered_path: np.array):
        """
        Initializer of SimpleTranslator

        :param topology: target topology
        :param collective: target collective
        :param path: found path to translate ([c, n, n, t] numpy array)
        """
        # parameters
        self.topology = topology
        self.collective = collective
        self.ordered_path = ordered_path

        # common vars
        # self.time_max = ordered_path.shape[-1]
        self.npus_count = self.topology.npus_count
        self.chunks_count = self.collective.chunks_count

        # Simulation structure
        self.queue = TimeTranslatorQueue()
        Link.queue = self.queue
        self._construct_topology()

    def run(self) -> Time:
        # initialize queue
        self._initialize_events()

        # run while all events finish
        next_time, links_to_wakeup = self.queue.pop()
        while next_time is not None:
            self._process_link_events(links=links_to_wakeup)
            next_time, links_to_wakeup = self.queue.pop()

        # time translation done, return the calculated time (which is stored inside event_queue)
        return self.queue.current_time

    def _initialize_events(self) -> None:
        """
        Initialize time_translator_queue
        This is done by just waking up links for the first time.

        :return: None
        """
        for link in self.links.values():
            link.wakeup()

    def _process_link_events(self,
                             links: Set[LinkId]) -> None:
        """
        Wakeup given links (i.e., process events acccordingly)

        :param links: links to wakeup and process events
        :return: None
        """
        for link in links:
            # dest NPUs should receive
            chunk = self.links[link].pop_current_chunk()
            self.npus[link[1]].receive(chunk)

        # wakeup links
        # 1. should wakeup given link
        # 2. should also wakeup the dest NPU's egress links accordingly
        #       so that they can process based on the chunk that just arrived
        for link in links:
            self.links[link].wakeup()

            for next_link in self.npu_links[link[1]]:
                next_link.wakeup()

    def _construct_topology(self) -> None:
        """
        Initialize NPUs and links as directed

        :return: None
        """

        self.npus = [Npu(i) for i in range(self.npus_count)]
        self.links: Dict[LinkId, Link] = dict()  # LinkID -> Link
        self.npu_links: Dict[NpuId, Set[Link]] = dict()  # NpuID -> List[Link]

        # Create NPUs
        for src in range(self.npus_count):
            self.npu_links[src] = set()

        for chunk, npu in self.collective.precondition:
            # starts with precondition chunks
            self.npus[npu].receive(chunk=chunk)

        # Create links
        for src in range(self.npus_count):
            for dest in range(self.npus_count):
                link = (src, dest)
                link_ordering = self.ordered_path.get_ordering(link=link)

                if link_ordering is not None:
                    # link exists, assign new link
                    link_alpha_beta = (self.topology.alpha[link], self.topology.beta[link])

                    new_link = Link(chunk_ordering=link_ordering,
                                    src=self.npus[src],
                                    dest=self.npus[dest],
                                    link_alpha_beta=link_alpha_beta,
                                    chunk_size=self.collective.chunk_size)
                    self.links[link] = new_link
                    self.npu_links[src].add(new_link)
