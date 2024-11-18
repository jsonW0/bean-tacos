from helper.typing import *


class Npu:
    """
    Simulate NPU when running time domain translation
    Main job is to track the chunks each NPU has already received
    """

    def __init__(self,
                 npu_id: NpuId):
        """
        Initializer

        :param npu_id: NPU's id
        """
        self.npu_id = npu_id
        self.received_chunks: Set[ChunkId] = set()

    def receive(self,
                chunk: ChunkId) -> None:
        """
        Receive a chunk.

        :param chunk: chunk id to receive
        :return: None
        """
        self.received_chunks.add(chunk)

    def already_received(self,
                         chunk: ChunkId) -> bool:
        """
        Check whether or not the NPU has already received a chunk

        :param chunk: chunk id to test
        :return: True if chunk has already been received, False if not
        """
        return chunk in self.received_chunks
