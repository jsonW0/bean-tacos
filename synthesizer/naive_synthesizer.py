import csv
import random
from collections import defaultdict
from helper.typing import *
from helper.time_expanded_network import TimeExpandedNetwork
from topology.topology import Topology
from collective.collective import Collective

class NaiveSynthesizer:
    def __init__(self, topology: Topology, collective: Collective, chunk_size: float = 1048576 / 976562.5, discretize=False):
        self.topology = topology
        self.collective = collective
        self.chunk_size = chunk_size

        self.nodes = self.topology.G.nodes
        self.edges = self.topology.G.edges
        self.chunks = self.collective.chunks

        self.TEN = TimeExpandedNetwork(topology=self.topology, collective=self.collective)

        if discretize:
            self.TEN.discretize()
    
    def solve(self, time_limit: float = None, verbose: bool = False, filename: str = None) -> None:
        while not self.TEN.satisfied():
            possible_matches = self.TEN.get_possible_link_chunk_matches()
            if len(possible_matches)==0:
                self.TEN.step()
            else:
                chosen_edge, chosen_chunk = random.choice(possible_matches)
                self.TEN.match(edge=chosen_edge, chunk=chosen_chunk)
    
    def write_csv(self, filename: str) -> None:
        edge_to_chunks = defaultdict(list)
        for edge,chunk,send_time,receive_time in self.TEN.event_history:
            edge_to_chunks[edge].append((chunk, send_time, receive_time))

        with open(filename, mode="w") as f:
            writer = csv.writer(f)
            writer.writerow(["NPUs Count",len(self.nodes)])
            writer.writerow(["Links Count",len(self.edges)])
            writer.writerow(["Chunks Count",len(self.chunks)])
            writer.writerow(["Chunk Size",self.chunk_size])
            writer.writerow(["Collective Time",self.TEN.current_time,"ns"])
            writer.writerow(["SrcID","DestID","Latency (ns)","Bandwidth (GB/s)","Chunks (ID:ns:ns)"])
            for edge in self.edges:
                src, dest = edge
                writer.writerow([src,dest,self.edges[edge]["alpha"],self.edges[edge]["beta"]]+[":".join(str(y) for y in x) for x in edge_to_chunks[edge]])
    