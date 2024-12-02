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
    elif match := re.match(r"^fc_n=(\d+)_alpha=([\d.]+)_beta=([\d.]+)$", specifier):
        n, alpha, beta = match.groups()
        G = nx.complete_graph(n=int(n)).to_directed()
        for src, dest in G.edges:
            G.add_edge(src,dest,alpha=float(alpha),beta=float(beta))
        return Topology(G=G)
    elif match := re.match(r"^wheel_n=(\d+)_alpha=([\d.]+)_beta=([\d.]+)$", specifier):
        n, alpha, beta = match.groups()
        G = nx.wheel_graph(n=int(n)).to_directed()
        for src, dest in G.edges:
            G.add_edge(src,dest,alpha=float(alpha),beta=float(beta))
        return Topology(G=G)
    elif match := re.match(r"^tree_r=(\d+)_h=(\d+)_alpha=([\d.]+)_beta=([\d.]+)$", specifier):
        r, h, alpha, beta = match.groups()
        G = nx.balanced_tree(r=int(r),h=int(h)).to_directed()
        for src, dest in G.edges:
            G.add_edge(src,dest,alpha=float(alpha),beta=float(beta))
        return Topology(G=G)
    else:
        raise ValueError(f"Cannot find or recognize: {specifier}")
