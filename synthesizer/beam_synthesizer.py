import csv
import random
import numpy as np
from copy import deepcopy
from collections import defaultdict
import networkx as nx
from helper.typing import *
from topology.topology import Topology
from collective.collective import Collective
from synthesizer.tacos_synthesizer import TACOSSynthesizer

def softmax(x, temperature=1.0):
    x = np.asarray(x, dtype=np.float64) / temperature  
    x -= np.max(x)
    x = np.exp(x)      
    return x / np.sum(x)

class BeamSynthesizer:
    def __init__(self, topology: Topology, collective: Collective, discretize=False, num_beams=1, fitness_type="chunk_count", temperature=0., seed=None):
        self.rng = np.random.default_rng(seed)
        self.num_beams = num_beams
        seeds = [self.rng.integers(0,2**32-1) for _ in range(self.num_beams)]
        self.instances = [
            TACOSSynthesizer(topology=topology, collective=collective, discretize=discretize, seed=seeds[i]) for i in range(self.num_beams)
        ]
        self.fitness_type = fitness_type
        self.temperature = temperature
        self.shortest_paths = None

    def compute_fitness(self, instance: TACOSSynthesizer) -> float:
        # A: total number of chunks each has
        # B: link utilization
        # C: weighting by degree
        # D: max of shortest path distances of precondition to postcondition
        if self.fitness_type=="chunk_count":
            return sum(len(instance.get_chunks_at_node(node,instance.current_time)) for node in instance.nodes)
        elif self.fitness_type=="shortest_path":
            if self.shortest_paths is None:
                # Uses Floyd-Warshall, but could change to use Dijkstra, Bellman-Ford, or Johnson
                G = instance.topology.G
                for src, dest in G.edges:
                    G.add_edge(src, dest, link_delay=instance.topology.get_delay(edge=(src,dest)))
                self.shortest_paths = nx.floyd_warshall_numpy(G, weight="link_delay")
            # For each postcondition, get the shortest distance to the nearest chunk
            preconditions = defaultdict(list)
            for node, chunks in {node:set(instance.get_chunks_at_node(node,instance.current_time)) for node in instance.nodes}.items():
                for chunk in chunks:
                    preconditions[chunk].append(node)
            distances = []
            for chunk, node in instance.collective.postcondition:
                distances.append(min(self.shortest_paths[node,candidate_node] for candidate_node in preconditions[chunk]))
            return -max(distances)
        else:
            raise ValueError(f"Fitness function not supported: {self.fitness_type}")

    def solve(self) -> None:
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
                                chosen_edge, chosen_chunk = instance_copy.rng.choice(possible_matches)
                                instance_copy.match(edge=chosen_edge, chunk=chosen_chunk)
                        population.append(instance_copy)
            population_fitnesses = [self.compute_fitness(instance) for instance in population]
            if self.temperature==0:
                self.instances = [population[i] for i in np.argpartition(population_fitnesses,-self.num_beams)[-self.num_beams:]]
            else:
                self.instances = self.rng.choice(population,p=softmax(population_fitnesses,temperature=self.temperature),replace=False,size=self.num_beams)
    
    @property
    def current_time(self):
        return np.min([instance.current_time for instance in self.instances])

    def write_csv(self, filename: str, synthesis_time: float) -> None:
        solve_times = [instance.current_time for instance in self.instances]
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
    