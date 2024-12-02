import re
import networkx as nx
from topology.topology import Topology

def get_topology(specifier: str) -> Topology:
    if match := re.match(r"^grid_w=(\d+)_h=(\d+)_alpha=([\d.]+)_beta=([\d.]+)$", specifier):
        w, h, alpha, beta = match.groups()
        G = nx.convert_node_labels_to_integers(nx.grid_graph(dim=(int(w),int(h))).to_directed())
        for src, dest in G.edges:
            G.add_edge(src,dest,alpha=float(alpha),beta=float(beta))
        return Topology(G=G)
    else:
        raise ValueError(f"Cannot find or recognize: {specifier}")
