from collective.collective import Collective
from helper.typing import *
import copy


class Broadcast(Collective):
    """
    All-Gather Collective Communication pattern.
    """

    def __init__(self,
                 npus_count: int,
                 src: NpuId,
                 chunk_size: ChunkSize = 1,
                 collectives_count: int = 1
                 ):
        """
        Initialize All-Gather

        :param npus_count: number of NPUs running this collective
        :param chunk_size: message size of each chunk
        :param collectives_count: number of collectives to run
                                  e.g., if this is 2, this collective defines two All-Reduce kernels
                                  (i.e., every NPU starts with 2 chunks)
        """
        super().__init__(chunk_size=chunk_size)

        # for every src, create a new chunk and send it to every NPUs.
        # repeat this collectives_count number of times.
        chunk_id = 0
        for _ in range(collectives_count):
            for dest in range(npus_count):
                self.add(id=chunk_id, src=src, dest=dest)

            # chunk_id increments at src-level
            chunk_id += 1

        self.update_chunk_counts()
        self.orig_precond = copy.deepcopy(self.postcondition)
