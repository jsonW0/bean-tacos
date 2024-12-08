import json
from collections import defaultdict
from helper.typing import *

class Collective:
    """
    Base class to represent collective communication.
    """

    def __init__(self,
                 filename: str = None,
                 chunk_size: ChunkSize = UnitChunkSize):
        """
        Initialize a collective.

        :param chunk_size: size of each collective chunk.
        """
        if filename is not None:
            self.load_json(filename)
        else:
            self.chunk_size = chunk_size  # size of each chunk

            self.chunks: Set[ChunkId] = set()  # list of ChunkIDs
            self.chunks_count = -1  # total number of unique chunks

            # precondition and postcondition
            # represented using a set of (chunkId, NpuId)
            self.precondition: Set[Tuple[ChunkId, NpuId]] = set()
            self.postcondition: Set[Tuple[ChunkId, NpuId]] = set()

            self.precondition_dict: Dict[NpuId, Set[ChunkId]] = defaultdict(set)
            self.postcondition_dict: Dict[NpuId, Set[ChunkId]] = defaultdict(set)

    @property
    def num_chunks(self):
        return len(self.chunks)

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

        self.precondition_dict[src].add(id)
        self.postcondition_dict[dest].add(id)


    def write_json(self, filename: str) -> None:
        with open(filename, mode="w", newline="") as f:
            json.dump({
                "chunk_size": self.chunk_size,
                "chunks": list(self.chunks),
                "preconditions": {key:list(value) for key,value in self.precondition_dict.items()},
                "postconditions": {key:list(value) for key,value in self.postcondition_dict.items()},
            },f,indent=4)

    def load_json(self, filename: str) -> None:
        with open(filename, mode="r", newline="") as f:
            data = json.load(f)
        self.chunk_size = data["chunk_size"]
        self.chunks = set(data["chunks"])
        self.chunks_count = len(self.chunks)
        self.precondition_dict = {key:set(value) for key,value in data["preconditions"].items()}
        self.postcondition_dict = {key:set(value) for key,value in data["postconditions"].items()}
        self.precondition = set()
        self.postcondition = set()
        for node, chunks in self.precondition_dict.items():
            for chunk in chunks:
                self.precondition.add((chunk, node))
        for node, chunks in self.postcondition_dict.items():
            for chunk in chunks:
                self.postcondition.add((chunk, node))
        