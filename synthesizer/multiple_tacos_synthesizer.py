import csv
import random
import numpy as np
from collections import defaultdict
from joblib import Parallel, delayed
from helper.typing import *
from topology.topology import Topology
from collective.collective import Collective
from synthesizer.tacos_synthesizer import TACOSSynthesizer

class MultipleTACOSSynthesizer:
    def __init__(self, topology: Topology, collective: Collective, discretize=False, num_beams=1, seed=None):
        self.rng = random.Random(seed)
        seeds = [self.rng.randint(0,2**32-1) for _ in range(num_beams)]
        self.instances = [
            TACOSSynthesizer(topology=topology, collective=collective, discretize=discretize, seed=seeds[i]) for i in range(num_beams)
        ]
    
    def solve(self) -> None:
        # Parallel(n_jobs=-1)(delayed(instance.solve)() for instance in self.instances)
        for i in range(len(self.instances)):
            self.instances[i].solve()

    @property
    def current_time(self):
        return np.min([instance.current_time for instance in self.instances])
    
    def write_csv(self, filename: str, synthesis_time: float) -> None:
        solve_times = [instance.current_time for instance in self.instances]
        print(solve_times)
        best_instance = self.instances[np.argmin(solve_times)]

        edge_to_chunks = defaultdict(list)
        for edge,chunk,send_time,receive_time in best_instance.event_history:
            edge_to_chunks[edge].append((chunk, send_time, receive_time))

        with open(filename, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["NPUs Count",len(best_instance.nodes)])
            writer.writerow(["Links Count",len(best_instance.edges)])
            writer.writerow(["Chunks Count",len(best_instance.chunks)])
            writer.writerow(["Chunk Size",best_instance.chunk_size])
            writer.writerow(["Collective Time",best_instance.current_time,"ns"])
            writer.writerow(["Synthesis Time",synthesis_time,"s"])
            writer.writerow(["SrcID","DestID","Latency (ns)","Bandwidth (GB/s)","Chunks (ID:ns:ns)"])
            for edge in best_instance.edges:
                src, dest = edge
                writer.writerow([src,dest,best_instance.edges[edge]["alpha"],best_instance.edges[edge]["beta"]]+[":".join(str(y) for y in x) for x in edge_to_chunks[edge]])
    