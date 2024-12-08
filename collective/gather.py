from collective.collective import Collective
from helper.typing import *


class Gather(Collective):
    """
    Gather Collective Communication pattern.
    i.e., from all NPUs to one dest NPU.
    """

    def __init__(self,
                 dest: NpuId,
                 npus_count: int,
                 chunk_size: ChunkSize = UnitChunkSize,
                 collectives_count: int = 1
                 ):
        """
        Initialize Gather

        :param dest: Dest NPU Id
        :param npus_count: number of NPUs running this collective
        :param chunk_size: message size of each chunk
        :param collectives_count: number of collectives to run
                                  e.g., if this is 2, this collective defines two All-Reduce kernels
                                  (i.e., every NPU starts with 2 chunks)
        """
        super().__init__(chunk_size=chunk_size)

        chunk_id = 0
        for _ in range(collectives_count):
            for src in range(npus_count):
                self.add(id=chunk_id, src=src, dest=dest)
                chunk_id += 1

        self.chunks_count = len(self.chunks)