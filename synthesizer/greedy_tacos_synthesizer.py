import csv
import random
import numpy as np
from collections import defaultdict
from helper.typing import *
from topology.topology import Topology
from collective.collective import Collective

class GreedyTACOSSynthesizer:
    def __init__(self, topology: Topology, collective: Collective, discretize=False):
        self.topology = topology
        self.collective = collective
        self.chunk_size = collective.chunk_size

        self.nodes = self.topology.G.nodes
        self.edges = self.topology.G.edges
        self.chunks = self.collective.chunks

        if discretize:
            self.discretize()

        self.current_time = 0
        self.event_history: List[Event] = []

        self.link_available_from = {edge:0 for edge in self.topology.G.edges}
        self.chunk_arrival_at_node = {node:defaultdict(lambda:float('inf')) for node in self.topology.G.nodes}
        for chunk, node in self.collective.precondition:
            self.chunk_arrival_at_node[node][chunk] = 0
    
    def satisfied(self) -> bool:
        for chunk, node in self.collective.postcondition:
            if self.chunk_arrival_at_node[node][chunk]>self.current_time:
                return False
        return True

    def get_available_links(self) -> List[LinkId]:
        return [edge for edge,available_from in self.link_available_from.items() if available_from<=self.current_time-self.topology.get_delay(edge,self.chunk_size)]

    def get_chunks_at_node(self, node: NpuId, at_time: Time) -> List[ChunkId]:
        return [chunk for chunk, arrival_time in self.chunk_arrival_at_node[node].items() if arrival_time<=at_time]

    def is_productive_link_chunk_match(self, edge: LinkId, chunk: ChunkId) -> bool:
        src, dest = edge
        return (
            self.link_available_from[edge]<=self.current_time-self.topology.get_delay(edge,self.chunk_size) and # available
            self.chunk_arrival_at_node[src][chunk]<=self.current_time-self.topology.get_delay(edge,self.chunk_size) and # chunk is available at source
            self.chunk_arrival_at_node[dest][chunk]==float('inf') and # dest does not have it AND not enroute
            (chunk, dest) in self.collective.postcondition # chunk is needed at dest
        )

    def get_possible_link_chunk_matches(self) -> List[Tuple[LinkId,ChunkId]]:
        matches = []
        available_links = self.get_available_links()
        for src, dest in available_links:
            for chunk in self.get_chunks_at_node(src, self.current_time-self.topology.get_delay((src,dest),self.chunk_size)):
                if self.is_productive_link_chunk_match(edge=(src, dest), chunk=chunk):
                    matches.append(((src, dest), chunk))
        return matches

    def match(self, edge: LinkId, chunk: ChunkId) -> None:
        src, dest = edge
        if not self.is_productive_link_chunk_match(edge=edge, chunk=chunk):
            raise ValueError(f"Attempted invalid link chunk match: {edge}, {chunk}")
        send_time = self.current_time - self.topology.get_delay(edge=edge, chunk_size=self.chunk_size)
        receive_time = self.current_time
        self.event_history.append((edge,chunk,send_time,receive_time))
        self.link_available_from[edge] = receive_time
        self.chunk_arrival_at_node[dest][chunk] = receive_time

    def step(self) -> None:
        link_available_from_plus_delay = [self.link_available_from[edge]+self.topology.get_delay(edge=edge, chunk_size=self.chunk_size) for edge in self.link_available_from.keys()]
        next_time = min(t for t in link_available_from_plus_delay if t>self.current_time)
        self.current_time = next_time

    def discretize(self) -> None:
        pass

    def write_ten(self, filename: str) -> None:
        pass
    
    def solve(self) -> None:
        while not self.satisfied():
            possible_matches = self.get_possible_link_chunk_matches()
            if len(possible_matches)==0:
                self.step()
            else:
                edge_delays = [self.topology.get_delay(edge,self.chunk_size) for edge,_ in possible_matches]
                chosen_edge, chosen_chunk = possible_matches[np.argmin(edge_delays)]
                self.match(edge=chosen_edge, chunk=chosen_chunk)
    
    def write_csv(self, filename: str, synthesis_time: float) -> None:
        edge_to_chunks = defaultdict(list)
        for edge,chunk,send_time,receive_time in self.event_history:
            edge_to_chunks[edge].append((chunk, send_time, receive_time))

        with open(filename, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["NPUs Count",len(self.nodes)])
            writer.writerow(["Links Count",len(self.edges)])
            writer.writerow(["Chunks Count",len(self.chunks)])
            writer.writerow(["Chunk Size",self.chunk_size])
            writer.writerow(["Collective Time",self.current_time,"ns"])
            writer.writerow(["Synthesis Time",synthesis_time,"s"])
            writer.writerow(["SrcID","DestID","Latency (ns)","Bandwidth (GB/s)","Chunks (ID:ns:ns)"])
            for edge in self.edges:
                src, dest = edge
                writer.writerow([src,dest,self.edges[edge]["alpha"],self.edges[edge]["beta"]]+[":".join(str(y) for y in x) for x in edge_to_chunks[edge]])
    