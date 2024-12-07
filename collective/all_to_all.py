from collective.collective import Collective
from helper.typing import *


class AllToAll(Collective):
    """
    All-to-All Collective Communication pattern.
    """

    def __init__(self,
                 npus_count: int,
                 chunk_size: ChunkSize = 1048576 / 976562.5,
                 collectives_count: int = 1
                 ):
        """
        Initialize All-to-All

        :param npus_count: Number of NPUs running this collective
        :param chunk_size: Message size of each chunk
        :param collectives_count: Number of collectives to run
                                   e.g., if this is 2, each NPU sends and receives 2 chunks.
        """
        super().__init__(chunk_size=chunk_size)

        # Each NPU sends a chunk to every other NPU
        chunk_id = 0
        for _ in range(collectives_count):
            for src in range(npus_count):
                for dest in range(npus_count):
                    self.add(id=chunk_id, src=src, dest=dest)
                    chunk_id += 1

        self.chunks_count = len(self.chunks)
