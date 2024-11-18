import copy
from collective.collective import Collective
from helper.typing import *
from topology.topology import Topology


class Scatter(Collective):
    """
    Scatter Collective Communication pattern.
    i.e., from one source NPU to all NPUs.
    """

    def __init__(self,
                 src: NpuId,
                 npus_count: int,
                 chunk_size: ChunkSize = 1,
                 collectives_count: int = 1
                 ):
        """
        Initialize Scatter

        :param src: Src NPU Id
        :param npus_count: number of NPUs running this collective
        :param chunk_size: message size of each chunk
        :param collectives_count: number of collectives to run
                                  e.g., if this is 2, this collective defines two All-Reduce kernels
                                  (i.e., every NPU starts with 2 chunks)
        """
        super().__init__(chunk_size=chunk_size)

        chunk_id = 0
        for _ in range(collectives_count):
            for dest in range(npus_count):
                self.add(id=chunk_id, src=src, dest=dest)
                # print(f"Add: {chunk_id}, {src}, {dest}")
                chunk_id += 1

        self.update_chunk_counts()
        self.orig_precond = copy.deepcopy(self.postcondition)

    def amend_postcond_backtracking(self,
                                    topology: Topology,
                                    enable_neighbor: bool = False) -> None:
        newly_added = dict()
        orig_dest = dict()
        paths = dict()

        for chunk in range(self.chunks_count):
            src = None
            dest = None
            for npu in range(topology.npus_count):
                if (chunk, npu) in self.precondition:
                    src = npu
                if (chunk, npu) in self.postcondition:
                    dest = npu

            _, path = topology.shortest_path(src=src, dest=dest, chunk_size=self.chunk_size)

            orig_dest[chunk] = dest
            paths[chunk] = path

            for i in range(1, len(path) - 1):
                # add intermediate npu
                intermediate_npu = path[i]
                self.postcondition.add((chunk, intermediate_npu))

            if enable_neighbor:
                # add nearby npus
                for i in range(len(path)):
                    intermediate_npu = path[i]

                    # get neighbors of intermediate_npu
                    incoming_npus = topology.incoming_npus(intermediate_npu)
                    outgoing_npus = topology.outgoing_npus(intermediate_npu)

                    npus_to_add = set(incoming_npus).union(set(outgoing_npus))

                    if chunk in newly_added:
                        newly_added[chunk] = newly_added[chunk].union(npus_to_add)
                    else:
                        newly_added[chunk] = npus_to_add

                    for npu in npus_to_add:
                        self.postcondition.add((chunk, npu))

                # print(chunk, src, dest, path)

        for chunk, added in newly_added.items():
            print(f"{chunk}: {added} (orig: {orig_dest[chunk]}, path: {paths[chunk]})")

    # def add_random_postcond(self,
    #                         topology: Topology) -> None:
    #
    #
    #     for chunk in range(self.chunks_count):
    #         src = None
    #         dest = None
    #         for npu in range(topology.npus_count):
    #             if (chunk, npu) in self.precondition:
    #                 src = npu
    #             if (chunk, npu) in self.postcondition:
    #                 dest = npu
    #
    #         _, path = topology.shortest_path(src=src, dest=dest, chunk_size=self.chunk_size)
    #
    #         print(chunk, src, dest, path)
    #         orig_dest[chunk] = dest
    #
    #         for i in range(len(path)):
    #             intermediate_npu = path[i]
    #
    #
    #
    #     for chunk, added in newly_added.items():
    #         print(f"{chunk}: {added} (orig: {orig_dest[chunk]})")
