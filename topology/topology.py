import math
import numpy as np
import pandas as pd
import networkx as nx
from helper.typing import *

class Topology:
    """
    Base class to represent target physical topologies.
    """

    def __init__(self, num_nodes=None, G: nx.Graph=None, filename: str=None):
        """
        Topology class initializer
        :param num_nodes: total number of NPUs of the topology
        :param G: networkx graph
        :param filename: filename to load networkx graph from
        """
        if G is not None and num_nodes is None and filename is None:
            self.load_nx(G)
        elif filename is not None and num_nodes is None and G is None:
            self.load_file(filename)
        elif num_nodes is not None and G is None and filename is None:
            self.G = nx.DiGraph()
            self.G.add_nodes_from(range(num_nodes))
        else:
            raise ValueError("Exactly one of 'npus_count', 'G', or 'filename' must be specified")

    @property
    def num_nodes(self):
        return self.G.number_of_nodes()
    
    @property
    def num_edges(self):
        return self.G.number_of_edges()
    
    def get_delay(self, edge: LinkId, chunk_size: ChunkSize = UnitChunkSize) -> Time:
        return self.G.edges[edge]["alpha"]+ (chunk_size/(1 << 30))*(1e9/self.G.edges[edge]["beta"])

    def connect(self,
                src: NpuId,
                dest: NpuId,
                link_alpha_beta: LinkAlphaBeta) -> None:
        """
        Create a link (src -> dest).

        :param src: src NPU id
        :param dest: dest NPU id
        :param link_alpha_beta: alpha and beta of the link
        :return: None
        """
        self.G.add_edge(src,dest,alpha=link_alpha_beta[0],beta=link_alpha_beta[1])
    
    def load_nx(self, G: nx.Graph) -> None:
        if len(nx.get_edge_attributes(G,"alpha"))==0 or len(nx.get_edge_attributes(G,"beta"))==0:
            raise ValueError("Graph must have 'alpha' (latency in ns) and 'beta' (bandwidth in GB/s) edge attributes")
        self.G = G

    def load_file(self, filename: str) -> None:
        df = pd.read_csv(filename,skiprows=1)
        df = df.rename(columns={"Latency (ns)": "alpha", "Bandwidth (GB/s)": "beta"})
        G = nx.from_pandas_edgelist(df, source="Src", target="Dest", edge_attr=["alpha", "beta"], create_using=nx.DiGraph)
        self.load_nx(G)