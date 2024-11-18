import numpy as np
from helper.typing import *
from topology.topology import Topology


class OrderedPath:
    """
    Path data structure, which stores already ordered path (i.e., arbitration already taken place)
    """

    def __init__(self,
                 topology: Topology,
                 chunks_count: int):
        """
        Initializer

        :param topology: physical topology where the path is defined over
        :param chunks_count: number of total chunks of a collective
        """
        # params
        self.topology = topology
        self.chunks_count = chunks_count

        # frequent vars
        self.npus_count = topology.npus_count

        # path: stores chunk ordering
        # e.g., if Link 0 -> 2 has chunk [2, 5, 8, 1] scheduled,
        # then path[0, 2] = [2, 5, 8, 1, -1, -1, -1, ..., -1] (trailing -1 means no chunk is scheduled)
        self.path = np.full(shape=(self.npus_count, self.npus_count, chunks_count),
                            fill_value=-1, dtype=ChunkId)

        # stores the index of self.path read/write
        self.current_index = np.zeros(shape=(self.npus_count, self.npus_count), dtype=int)

    def add_send(self,
                 link: LinkId,
                 chunk: ChunkId) -> None:
        """
        Assign new send over a link.

        :param link: link to send a chunk
        :param chunk: chunk that's being sent over the link
        :return: None
        """
        # assign chunk
        index = self.current_index[link]
        self.path[link + (index,)] = chunk

        # increment to new index
        self.current_index[link] += 1

    def translate_ten_path(self,
                           ten_path: np.array) -> None:
        """
        Translate a TEN-generated numpy-format path to the OrderedPath format.

        :param ten_path: TEN-path to process, in [chunks, npus, npus, timestep] format.
        :return: None
        """
        timestep = ten_path.shape[-1]

        for src in range(self.npus_count):
            for dest in range(self.npus_count):
                if src == dest:  # not an effective send
                    continue

                if not self.topology.topology[src, dest]:  # no link exists
                    continue

                for t in range(timestep):
                    for chunk in range(self.chunks_count):
                        if ten_path[chunk, src, dest, t]:
                            # scheduled chunk found: register this
                            index = self.current_index[src, dest]
                            self.path[src, dest, index] = chunk

                            # increment index
                            self.current_index[src, dest] += 1

                            break  # only one c at given time

        # reset current_index after construction
        self.reset_index()

    def get_ordering(self,
                     link: LinkId) -> Optional[List[ChunkId]]:
        """
        Get chunk ordering over a given link.

        :param link: link to query chunk ordering
        :return: None if no chunks are assigned
                 chunk ordering in List[Chunks] format if chunks are scheduled over a link.
        """
        link_ordering = self.path[link].tolist()

        # filter trailing -1s (redundant)
        index = link_ordering.index(-1)
        link_ordering = link_ordering[:index]

        if len(link_ordering) <= 0:
            return None

        return link_ordering

    def reset_index(self) -> None:
        """
        Reset current_index

        :return: None
        """
        self.current_index = np.zeros(shape=(self.npus_count, self.npus_count), dtype=int)

    # def get_next_chunk(self,
    #                    link: LinkId) -> Optional[ChunkId]:
    #     """
    #     Quer
    #     :param link:
    #     :return:
    #     """
    #     index = self.current_index[link]
    #     chunk = self.path[link + (index,)]
    #
    #     if chunk < 0:
    #         return None
    #
    #     self.current_index[link] += 1
    #     return chunk

    def print_path(self) -> None:
        # print synthesized path
        for src in range(self.topology.npus_count):
            for dest in range(self.topology.npus_count):
                if src == dest:
                    continue

                # get the path
                chunk_order = self.path[src, dest].tolist()
                chunk_order = list(filter(lambda x: x >= 0, chunk_order))
                chunk_order = list(map(lambda x: str(x), chunk_order))

                # print the path
                if len(chunk_order) <= 0:
                    continue

                chunk_order_str = " -> ".join(chunk_order)

                print(f"Link ({src} -> {dest}): Chunks {chunk_order_str}")
