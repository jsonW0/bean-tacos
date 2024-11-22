import numpy as np
from collections import defaultdict
from helper.typing import *
from helper.event_queue import EventQueue
from topology.topology import Topology
from collective.collective import Collective

class TimeExpandedNetwork:
    """
    Time-expanded Network (TEN). Represents the current state 
    """

    def __init__(self, topology: Topology, collective: Collective, chunk_size: float = 1048576 / 976562.5):
        """
        :param topology: network topology
        :param collective: network collective
        :param chunk_size: chunk size
        """
        # parameters
        self.topology = topology
        self.collective = collective
        self.chunk_size = chunk_size

        self.current_time = 0
        self.event_history: List[Event] = []
        self.event_queue = EventQueue()

        self.link_busy_until = {edge:0 for edge in self.topology.G.edges}
        self.chunk_arrival_at_node = {node:defaultdict(lambda:float('inf')) for node in self.topology.G.nodes}
        for chunk, node in self.collective.precondition:
            self.chunk_arrival_at_node[node][chunk] = 0
    
    def satisfied(self) -> bool:
        for chunk, node in self.collective.postcondition:
            if self.chunk_arrival_at_node[node][chunk]>self.current_time:
                return False
        return True

    def get_available_links(self) -> List[LinkId]:
        return [edge for edge,busy_until in self.link_busy_until.items() if busy_until<=self.current_time]

    def get_chunks_at_node(self, node: NpuId) -> List[ChunkId]:
        return [chunk for chunk, arrival_time in self.chunk_arrival_at_node[node].items() if arrival_time<=self.current_time]

    def is_productive_link_chunk_match(self, edge: LinkId, chunk: ChunkId) -> bool:
        src, dest = edge
        return (
            self.link_busy_until[edge]<=self.current_time and # available
            self.chunk_arrival_at_node[src][chunk]<=self.current_time and # chunk is available at source
            self.chunk_arrival_at_node[dest][chunk]==float('inf') and # dest does not have it AND not enroute
            (chunk, dest) in self.collective.postcondition # chunk is needed at dest
        )

    def get_possible_link_chunk_matches(self) -> List[Tuple[LinkId,ChunkId]]:
        matches = []
        available_links = self.get_available_links()
        for src, dest in available_links:
            for chunk in self.get_chunks_at_node(src):
                if self.is_productive_link_chunk_match(edge=(src, dest), chunk=chunk):
                    matches.append(((src, dest), chunk))
        return matches

    def match(self, edge: LinkId, chunk: ChunkId) -> None:
        src, dest = edge
        if not self.is_productive_link_chunk_match(edge=edge, chunk=chunk):
            raise ValueError(f"Attempted invalid link chunk match: {edge}, {chunk}")
        send_time = self.current_time
        receive_time = self.current_time + self.topology.get_delay(edge=edge, chunk_size=self.chunk_size)
        self.event_history.append((edge,chunk,send_time,receive_time))
        self.link_busy_until[edge] = receive_time
        self.chunk_arrival_at_node[dest][chunk] = receive_time
        self.event_queue.push((edge,chunk,send_time,receive_time))

    def step(self) -> None:
        next_time, events = self.event_queue.pop()
        # for edge,chunk,send_time,receive_time in events:
        self.current_time = next_time

    def discretize(self) -> None:
        pass

    def write_ten(self, filename: str) -> None:
        pass