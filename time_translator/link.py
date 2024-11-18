from helper.typing import *
from time_translator.npu import Npu
from time_translator.time_translator_queue import TimeTranslatorQueue


class Link:
    queue: TimeTranslatorQueue  # common time translator queue

    def __init__(self,
                 chunk_ordering: List[ChunkId],
                 src: Npu,
                 dest: Npu,
                 link_alpha_beta: LinkAlphaBeta,
                 chunk_size: ChunkSize):
        """
        Initializer of Link
        :param chunk_ordering: Ordering of chunks of this link
        :param src: Src NPU (not NPU Id)
        :param dest: dest NPU
        :param link_alpha_beta:
        :param chunk_size:
        :param time_translator_queue: common time_translator_queue
        """
        # pararmeters
        self.remaining_chunks = chunk_ordering
        self.src = src
        self.dest = dest
        self.alpha, self.beta = link_alpha_beta
        self.chunk_size = chunk_size

        # simulation value
        self.link_time = 0  # link_time (i.e., until when link is transmitting a chunk

    def wakeup(self) -> None:
        """
        Check the status of the link and do appropriate work.

        - If link has nothing to do (i.e., no chunks remaining), remain idle.
        - If link is already busy, keep transmitting chunk (do nothing)
        - If link is free and has some job to do, process that chunk.
        :return:
        """
        if len(self.remaining_chunks) <= 0:  # nothing to process
            return

        if self.link_time > Link.queue.current_time:  # link is busy
            return

        # find next chunk to send (i.e., src contains but dest not contains)
        next_chunk = self.remaining_chunks[0]
        while self.src.already_received(chunk=next_chunk) and self.dest.already_received(chunk=next_chunk):
            del self.remaining_chunks[0]

            if len(self.remaining_chunks) <= 0:
                # nothing to process, do nothing
                return

            next_chunk = self.remaining_chunks[0]

        # if src not contains, cannot send
        if not self.src.already_received(chunk=next_chunk):
            return

        # src contains but dest is not: can send
        # next chunk found, send this chunk
        # calculate arrival time
        link_time = self.alpha + (self.beta * self.chunk_size)
        arrival_time = Link.queue.current_time + link_time

        # assign event
        self.link_time = arrival_time
        link = (self.src.npu_id, self.dest.npu_id)
        Link.queue.schedule(time=arrival_time, link=link)

    def pop_current_chunk(self) -> ChunkId:
        """
        Return current processing Chunk ID, and remove that chunk from the list.

        :return: chunkID that's currently being processed
        """
        assert len(self.remaining_chunks) >= 1

        current_chunk = self.remaining_chunks[0]
        del self.remaining_chunks[0]

        return current_chunk
