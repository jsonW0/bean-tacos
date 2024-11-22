import math
import numpy as np
import pandas as pd
import networkx as nx
from helper.typing import *

class Topology:
    """
    Base class to represent target physical topologies.
    """

    def __init__(self, npus_count=None, G: nx.Graph=None, filename: str=None):
        """
        Topology class initializer
        :param npus_count: total number of NPUs of the topology
        """
        if G is not None and npus_count is None and filename is None:
            self.load_nx(G)
        elif filename is not None and npus_count is None and G is None:
            self.load_file(filename)
        elif npus_count is not None and G is None and filename is None:
            self.npus_count = 0

            # represent a topology in adjacency matrix format
            # True if link[src, dest] exists, False if not.
            self.topology = np.zeros(shape=(self.npus_count, self.npus_count), dtype=bool)

            # stores alpha (link latency) and beta (reciprocal of link BW) of each link
            # if link doesn't exist, default value: -1.
            self.alpha = np.full_like(self.topology, fill_value=-1, dtype=float)
            self.beta = np.full_like(self.topology, fill_value=-1, dtype=float)
        else:
            raise ValueError("Exactly one of 'npus_count', 'G', or 'filename' must be specified")

    def connect(self,
                src: NpuId,
                dest: NpuId,
                link_alpha_beta: LinkAlphaBeta,
                bidirectional: bool = True) -> None:
        """
        Create a link (src -> dest).

        :param src: src NPU id
        :param dest: dest NPU id
        :param link_alpha_beta: alpha and beta of the link
        :param bidirectional: if True, creates (src <-> dest) link
                              if False, creates (src -> dest) link
        :return: None
        """
        # src and dest must be within the existing NPU boundaries
        assert 0 <= src < self.npus_count
        assert 0 <= dest < self.npus_count

        # create link (src -> dest) and set alpha, beta
        self.topology[src, dest] = True
        self.alpha[src, dest] = link_alpha_beta[0]
        self.beta[src, dest] = link_alpha_beta[1]

        # if bidirectional is set, create (dest -> src) link with the same alpha/beta component
        if bidirectional:
            self.topology[dest, src] = True
            self.alpha[dest, src] = link_alpha_beta[0]
            self.beta[dest, src] = link_alpha_beta[1]
    
    def load_nx(self, G: nx.Graph) -> None:
        if len(nx.get_edge_attributes(G,"Latency (ns)"))==0 or len(nx.get_edge_attributes(G,"Bandwidth (GB/s)"))==0:
            raise ValueError("Graph must have 'Latency (ns)' and 'Bandwidth (GB/s)' edge attributes")
        self.npus_count = len(G.nodes())
        self.topology = nx.to_numpy_array(G).astype(bool)
        self.alpha = nx.to_numpy_array(G,weight="Latency (ns)")
        self.alpha[~self.topology] = -1.
        self.beta = nx.to_numpy_array(G,weight="Bandwidth (GB/s)")
        self.beta[~self.topology] = -1.

    def load_file(self, filename: str) -> None:
        df = pd.read_csv(filename,skiprows=1)
        G = nx.from_pandas_edgelist(df, source="Src", target="Dest", edge_attr=["Latency (ns)", "Bandwidth (GB/s)"])
        self.load_nx(G)

    def add_self_loop(self) -> None:
        """
        Create a self-loop (i.e., (src -> src) link)
        Used for Time-expanded-network-based Solvers (Congestionless/Congestionful)

        cf., This method just creates the link existence but doesn't set link alpha/beta.

        :return: None
        """
        for npu in range(self.npus_count):
            self.topology[npu, npu] = True

    def discretize_graph(self,
                         chunk_size: ChunkSize = 1,
                         unit_rate: Optional[float] = None) -> np.array:
        """
        Combine alpha/beta matrix and discretize it,
        resulting in a discretized network latency matrix.

        e.g., if alpha = [1 7]  and beta = [10 20]  and chunk_size = 3
                         [9 4]             [20 10]
              Then link latency (alpha + beta * chunk_size) is
                         [1 7] + [10 20] * 3   = [31 67]
                         [9 4]   [20 10]         [69 34]
              And if unit_rate is 10, then returns
                [3 6]
                [9 4]  (floors each value when discretizing)

              cf., if link doesn't exist, the value is set to 1 (desired characteristics for TEN)

        :param chunk_size: chunk size to consider when calculating network latency
        :param unit_rate: unit rate (denominator) to be used when discretizing network latency
                          if None is given, automatically selects this
                            (i.e., the minimum number inside the latency matrix)
        :return: discretized network communication latency matrix
                 (numpy array of size [npus_count x npus_count])
        """
        # calculate network latency
        network_latency = self.alpha + (self.beta * chunk_size)

        # decide unit_rate (if None is given)
        if unit_rate is None:
            # pick the minimum latency number
            # (among the positive numbers; negative number means no link exists)
            unit_rate = network_latency[network_latency > 0].min()

        # discretize graph using the unit_rate
        discretized_graph = np.ones_like(network_latency, dtype=int)
        for index, weight in np.ndenumerate(network_latency):
            discretized_graph[index] = max(math.floor(weight / unit_rate), 1)  # 1 is the minimum number

        return discretized_graph

    # def incoming_npus(self,
    #                   dest: NpuId) -> List[NpuId]:
    #     """
    #     See neighboring NPUs which has incoming links through the target NPU, and return them.

    #     :param dest: target destination NPU
    #     :return: list of NPU IDs that has an incoming links towards the target NPU.
    #     """

    #     incoming_npus = list()

    #     for src in range(self.npus_count):
    #         if self.topology[src, dest]:
    #             # has an incoming link
    #             incoming_npus.append(src)

    #     return incoming_npus

    # def outgoing_npus(self,
    #                   src: NpuId) -> List[NpuId]:
    #     outgoing_npus = list()

    #     for dest in range(self.npus_count):
    #         if self.topology[src, dest]:
    #             # has an incoming link
    #             outgoing_npus.append(dest)

    #     return outgoing_npus

    # def _get_dist(self,
    #               src: NpuId,
    #               dest: NpuId,
    #               chunk_size: ChunkSize = 1):
    #     return self.alpha[src, dest] + (self.beta[src, dest] * chunk_size)

    # def _pop_next_npu(self,
    #                   npu: List[NpuId],
    #                   dist: List[float]) -> NpuId:
    #     next_npu = min(npu, key=lambda k: dist[k])
    #     npu.remove(next_npu)
    #     return next_npu

    # def _dijkstra(self,
    #               src: NpuId,
    #               dest: NpuId,
    #               chunk_size: ChunkSize = 1) -> Tuple[Time, List[NpuId]]:
    #     # initialize
    #     dist = [math.inf for _ in range(self.npus_count)]
    #     prev_npu = [-1 for _ in range(self.npus_count)]
    #     dist[src] = 0

    #     npus_to_visit = [i for i in range(self.npus_count)]

    #     while len(npus_to_visit) > 0:
    #         current_npu = self._pop_next_npu(npu=npus_to_visit, dist=dist)
    #         if current_npu == dest:
    #             break

    #         neighboring_npus = self.outgoing_npus(src=current_npu)

    #         for neighbor in neighboring_npus:
    #             new_path_dist = dist[current_npu] + self._get_dist(src=current_npu, dest=neighbor, chunk_size=chunk_size)
    #             if new_path_dist < dist[neighbor]:
    #                 dist[neighbor] = new_path_dist
    #                 prev_npu[neighbor] = current_npu

    #     return dist[dest], prev_npu

    # def shortest_path(self,
    #                   src: NpuId,
    #                   dest: NpuId,
    #                   chunk_size: ChunkSize = 1) -> Tuple[Time, List[NpuId]]:
    #     dist, prev_npu = self._dijkstra(src=src, dest=dest, chunk_size=chunk_size)

    #     path = list()
    #     current_vertex = dest
    #     while current_vertex != src:
    #         path = [current_vertex] + path
    #         current_vertex = prev_npu[current_vertex]

    #     return dist, [src] + path
