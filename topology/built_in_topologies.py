import re
import ast
import math
import random
import networkx as nx
from topology.topology import Topology

def get_topology(specifier: str) -> Topology:
    # nx_graph_name__arg1=x__arg2=y__arg3=z
    # supports alpha, beta for homogeneous
    # supports alpha2, beta2, proportion for random heterogeneity
    if match := re.match(r"^nx_(?P<name>[a-zA-Z0-9_]+)(?:__(?P<args>.*))?$", specifier):
        generator_name = match.group("name")
        args_string = match.group("args")
        args = {}
        for arg in args_string.split("__"):
            key, value = arg.split("=")
            args[key] = ast.literal_eval(value)
        alpha = args.pop("alpha") if "alpha" in args else 0.
        beta = args.pop("beta") if "beta" in args else 1.
        alpha2 = args.pop("alpha2") if "alpha" in args else 0.
        beta2 = args.pop("beta2") if "beta" in args else 0.5
        proportion = args.pop("proportion") if "proportion" in args else 0.

        graph_function = getattr(nx, generator_name)
        G = nx.convert_node_labels_to_integers(graph_function(**args)).to_directed()

        heterogeneity = [(alpha,beta) for _ in range(math.floor((1-proportion)*len(G.edges)))]+[(alpha2,beta2) for _ in range(math.ceil(proportion*len(G.edges)))]
        random.shuffle(heterogeneity)
        for (src, dest), (link_alpha, link_beta) in zip(G.edges,heterogeneity):
            G.add_edge(src,dest,alpha=link_alpha,beta=link_beta)
        return Topology(G=G)
    else:
        raise ValueError(f"Cannot find or recognize: {specifier}")
