import numpy as np
from helper.typing import *
from topology.topology import Topology
from collective.collective import Collective


class TimeExpandedNetwork:
    """
    Given a Topology, translate it into a Time-expanded Network (TEN).
    """

    def __init__(self,
                 topology: Topology,
                 timesteps_count: int,
                 chunk_size: ChunkSize,
                 unit_rate: Optional[Time] = None):
        """

        :param topology: target topology to translate
        :param timesteps_count: TEN's width (end time)
                                 e.g., if timesteps_count=10, this TEN starts T=0 and ends at T=10
        :param chunk_size: chunk size to consider when discretizing network
        :param unit_rate: desired unit rate to be used when discretizing newtork latencies.
                          (if None, automatic discretization takes place.)
        """
        # parameters
        self.topology = topology
        self.timesteps_count = timesteps_count

        # frequently accessed parameters
        self.npus_count = topology.npus_count

        # discretize graph and calculate link weights
        self.topology.add_self_loop()
        self.link_weights = topology.discretize_graph(chunk_size=chunk_size,
                                                      unit_rate=unit_rate)

        # Representations of TEN
        # if links_id[2, 5, 7] = 13:
        #    then there exists a link (5 -> 7) from timestep 2 through (2 + link_weights[5, 7])
        #    and this link's unique identifier number is 13.
        # Assume all non-negative IDs are valid identifiers.
        self.link_ids = np.full(shape=(timesteps_count, self.npus_count, self.npus_count),
                                fill_value=-1, dtype=int)
        self.links_count = -1  # counts the number of total existing TEN links

        # Used to unroll link full data
        # LinkId -> (start_timestep, finish_timestep, src, dest)
        self.link_unroll_map: Dict[TenLinkId, TenLinkDataFull] = dict()

        # Used to track changelist (i.e., removed links)
        self.removed_links: Dict[TenLinkId, TenLinkData] = dict()

        # construct TEN
        self._construct_ten()

    def _construct_ten(self) -> None:
        """
        Initializer helper function.
        Constructs TEN of a given topology.
        :return: None
        """

        # Creates a link whenever a link exists between (src, dest)
        # repeat this over every timesteps.
        link_id = 0

        for start_timestep in range(self.timesteps_count):
            for src in range(self.npus_count):
                for dest in range(self.npus_count):
                    if self.topology.topology[src, dest]:
                        # link exists: create a TEN link.
                        #   (only create links if it's within the range of TEN).
                        #   (i.e., link ends within timesteps_count range)
                        link_weight = self.link_weights[src, dest]
                        finish_timestep = start_timestep + link_weight

                        if finish_timestep <= self.timesteps_count:
                            self.link_ids[start_timestep, src, dest] = link_id
                            self.link_unroll_map[link_id] = (start_timestep, finish_timestep, src, dest)
                            link_id += 1  # increment link identifier

        self.links_count = link_id  # link_id tracks created TEN links count in total

    def incoming_links(self,
                       dest: NpuId,
                       timestep: TenTimestep) -> List[TenLinkId]:
        """
        Return the list of links incoming through the given NPU, arriving at the given timestep.

        :param timestep: (arriving) timestep
        :param dest: target NPU to test incoming links
        :return: list of all incoming links (start_timestep, finish_timestep, src, dest)
        """

        # search for all incoming links
        incoming_links = list()

        for src in range(self.npus_count):
            # check whether (src -> dest) is connected
            if self.topology.topology[src, dest]:
                # now check whether it starts at the valid time
                link_weight = self.link_weights[src, dest]
                start_timestep = timestep - link_weight
                if start_timestep >= 0:
                    link_id = self.link_ids[start_timestep, src, dest]
                    if link_id >= 0:
                        # valid TEN incoming link found
                        incoming_links.append(link_id)

        return incoming_links

    def outgoing_links(self,
                       src: NpuId,
                       timestep: TenTimestep) -> List[TenLinkData]:
        """
        Return the list of links outgoing from the given NPU, starting at the given timestep.

        :param timestep: (beginning) timestep
        :param src: target NPU to test outgoing links
        :return: list of all outgoing links (start_timestep, finish_timestep, src, dest)
        """

        # search for all outgoing links
        outgoing_links = list()

        for dest in range(self.npus_count):
            # check whether a valid TEN link exists
            link_id = self.link_ids[timestep, src, dest]
            if link_id >= 0:
                # valid TEN link found
                outgoing_links.append(link_id)

        return outgoing_links

    def unroll_link_id(self,
                       link_id: TenLinkId) -> TenLinkDataFull:
        """
        Given link_id, return TEN link full data

        :param link_id: LinkID to unroll info
        :return: TEN link full data (start_timestep, finish_timestep, src, dest).
        """
        return self.link_unroll_map[link_id]

    def conflicting_links(self,
                          link_id: TenLinkId) -> List[TenLinkId]:
        """
        Given a TEN link, return the list of links that can create network congestions.

        :param link_id: LinkID to query
        :return: list of LinkIDs that can create congestion with the given link.
        """
        start_timestep, finish_timestep, src, dest = self.unroll_link_id(link_id=link_id)

        conflicting_links = list()

        if src == dest:
            # this means a packet just stays inside the same NPU
            # meaning no conflict with any other links

            # return empty list
            return list()

        # all links connecting (src -> dest) between the given timestep creates conflict
        for timestep in range(start_timestep, finish_timestep):
            conflict_link_id = self.link_ids[timestep, src, dest]

            if conflict_link_id >= 0:
                # valid link; add to the conflict list
                conflicting_links.append(conflict_link_id)

        return conflicting_links

    def remove_link(self,
                    link_id: TenLinkId) -> None:
        # track removed links
        start_timestep, _, src, dest = self.unroll_link_id(link_id=link_id)
        self.removed_links[link_id] = (start_timestep, src, dest)

        # remove link
        self.link_ids[start_timestep, src, dest] = -1

    def reset(self) -> None:
        # recover links
        for link_id, (start_timestep, src, dest) in self.removed_links.items():
            self.link_ids[start_timestep, src, dest] = link_id

        # reset removed_links tracker
        self.removed_links = dict()
