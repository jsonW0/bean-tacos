from helper.typing import *


class Collective:
    """
    Base class to represent collective communication.
    """

    def __init__(self,
                 chunk_size: ChunkSize):
        """
        Initialize a collective.

        :param chunk_size: size of each collective chunk.
        """
        self.chunk_size = chunk_size  # size of each chunk

        self.chunks: Set[ChunkId] = set()  # list of ChunkIDs
        self.chunks_count = -1  # total number of unique chunks

        # precondition and postcondition
        # represented using a set of (chunkId, NpuId)
        self.precondition: Set[Tuple[ChunkId, NpuId]] = set()
        self.postcondition: Set[Tuple[ChunkId, NpuId]] = set()
        self.orig_precond = set()

        self.dests_count: Dict[ChunkId, int] = dict()  # number of dests of each chunk

        self.rename_dict = dict()
        self.recovery_dict = dict()

    def add(self,
            id: ChunkId,
            src: NpuId,
            dest: NpuId) -> None:
        """
        Schedule a chunk with a given id,
        Starting from src and destined towards dest
        :param id: id of the chunk
        :param src: src NPU id
        :param dest: dest NPU id
        :return: None
        """
        if (id, src) in self.precondition and (id, dest) in self.postcondition:
            # duplicate, no need to add
            return

        self.chunks.add(id)  # set data structure automatically removes duplicate

        # update precondition and postcondition
        self.precondition.add((id, src))
        self.postcondition.add((id, dest))

        # increment dests_count
        if id in self.dests_count:
            self.dests_count[id] += 1
        else:
            self.dests_count[id] = 1

    # todo: debug renaming scheme
    def add_rename(self, old_id: ChunkId, new_id: ChunkId, src: NpuId, dest: NpuId) -> None:
        self.rename_dict[old_id] = new_id
        self.recovery_dict[new_id] = old_id

        self.add(id=new_id, src=src, dest=dest)

    def update_chunk_counts(self) -> None:
        self.chunks_count = len(self.chunks)

    def rename(self) -> None:
        current_id = 0

        for chunk in self.chunks:
            self.rename_dict[chunk] = current_id
            self.recovery_dict[current_id] = chunk
            current_id += 1

        self.chunks = set(range(current_id))
        self.precondition = set(map(lambda x: (self.rename_dict[x[0]], x[1]), self.precondition))
        self.postcondition = set(map(lambda x: (self.rename_dict[x[0]], x[1]), self.postcondition))
