import csv
import random
import numpy as np
from copy import deepcopy
from collections import defaultdict
from helper.typing import *
from helper.event_queue import EventQueue
from topology.topology import Topology
from collective.collective import Collective
from synthesizer.tacos_synthesizer import TACOSSynthesizer

class BeamSynthesizer:
    def __init__(self, topology: Topology, collective: Collective, chunk_size: float = 1048576 / 976562.5, discretize=False, num_beams=1):
        self.num_beams = num_beams
        self.instances = [
            TACOSSynthesizer(topology=topology, collective=collective, chunk_size=chunk_size, discretize=discretize) for _ in range(self.num_beams)
        ]

    def compute_fitness(self, instance: TACOSSynthesizer) -> float:
        # A: total number of chunks each has
        # B: sum of shortest path distances of precondition to postcondition
        return 

    def solve(self, time_limit: float = None, verbose: bool = False, filename: str = None) -> None:
        while not all(instance.satisfied() for instance in self.instances):
            population = []
            for instance in self.instances:
                if instance.satisfied():
                    population.append(instance)
                else:
                    for _ in range(self.num_beams):
                        instance_copy = deepcopy(instance)
                        while not instance_copy.satisfied():
                            possible_matches = instance_copy.get_possible_link_chunk_matches()
                            if len(possible_matches)==0:
                                instance_copy.step()
                                break
                            else:
                                chosen_edge, chosen_chunk = random.choice(possible_matches)
                                instance_copy.match(edge=chosen_edge, chunk=chosen_chunk)
                        population.append(instance_copy)
            population_fitnesses = [self.compute_fitness(instance) for instance in population]
            self.instances = population[np.argpartition(population_fitnesses,-self.num_beams)[-self.num_beams:]]
    
    def write_csv(self, filename: str, synthesis_time: float) -> None:
        solve_times = [instance.current_time for instance in self.instances]
        print(solve_times)
        best_instance = self.instances[np.argmin(solve_times)]

        edge_to_chunks = defaultdict(list)
        for edge,chunk,send_time,receive_time in best_instance.event_history:
            edge_to_chunks[edge].append((chunk, send_time, receive_time))

        with open(filename, mode="w") as f:
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
    