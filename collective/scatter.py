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
                 chunk_size: ChunkSize = 1048576 / 976562.5,
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

        self.chunks_count = len(self.chunks)