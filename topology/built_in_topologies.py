import re
import ast
import math
import random
import networkx as nx
from topology.topology import Topology

def tree_topology(degrees: list, latencies: list, bandwidths: list) -> Topology:
    tree = nx.Graph()
    height = len(degrees)
    node_id = 0
    nodes_at_current_level = [node_id]
    for level in range(height):
        next_level_nodes = []
        for parent in nodes_at_current_level:
            for _ in range(degrees[level]):
                node_id += 1
                tree.add_edge(parent, node_id, alpha=latencies[level], beta=bandwidths[level])
                next_level_nodes.append(node_id)
        nodes_at_current_level = next_level_nodes
    return Topology(G=tree.to_directed())

def get_topology(specifier: str) -> Topology:
    def parse_match(match: re.Match) -> dict:
        """Parses args named group in match: (?:__(?P<args>.*))?"""
        args_string = match.group("args")
        args = {}
        if args_string:
            for arg in args_string.split("__"):
                key, value = arg.split("=")
                args[key] = ast.literal_eval(value)
        return args
    if match := re.match(r"^nx_(?P<name>[a-zA-Z0-9_]+)(?:__(?P<args>.*))?$", specifier):
        # nx_graph_name__arg1=x__arg2=y__arg3=z
        # supports alpha, beta for homogeneous
        # supports alpha2, beta2, proportion for random heterogeneity
        generator_name = match.group("name")
        args = parse_match(match)

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
    
    # Shortcuts
    elif match := re.match(r"^fc(?:__(?P<args>.*))?$", specifier):
        # FC
        args = parse_match(match)
        G = nx.complete_graph(n=args["n"]).to_directed()
        for src, dest in G.edges:
            G.add_edge(src,dest,alpha=0.,beta=1.)
        return Topology(G=G)
    elif match := re.match(r"^grid(?:__(?P<args>.*))?$", specifier):
        # Line/Grid
        args = parse_match(match)
        G = nx.convert_node_labels_to_integers(nx.grid_graph(dim=args["dim"]).to_directed())
        for src, dest in G.edges:
            G.add_edge(src,dest,alpha=0.,beta=1.)
        if "outages" in args:
            for outage in args["outages"]:
                G.remove_node(outage)
        G = nx.convert_node_labels_to_integers(G)
        return Topology(G=G)
    elif match := re.match(r"^torus(?:__(?P<args>.*))?$", specifier):
        # Ring/Torus
        args = parse_match(match)
        G = nx.convert_node_labels_to_integers(nx.grid_graph(dim=args["dim"], periodic=True).to_directed())
        for src, dest in G.edges:
            G.add_edge(src,dest,alpha=0.,beta=1.)
        return Topology(G=G)
    elif match := re.match(r"^ring(?:__(?P<args>.*))?$", specifier):
        # Ring with bottleneck
        args = parse_match(match)
        G = nx.convert_node_labels_to_integers(nx.grid_graph(dim=args["dim"], periodic=True).to_directed())
        for i, (src, dest) in enumerate(G.edges):
            if i==0:
                G.add_edge(src,dest,alpha=0.,beta=args["slow"])
            else:
                G.add_edge(src,dest,alpha=0.,beta=1.)
        return Topology(G=G)
    elif match := re.match(r"^tree(?:__(?P<args>.*))?$", specifier):
        # Star/Tree
        args = parse_match(match)
        G = tree_topology(**args)
        # G = nx.full_rary_tree(r=args["r"], n=args["n"]).to_directed()
        # for src, dest in G.edges:
        #     G.add_edge(src,dest,alpha=0.,beta=1.)
        return Topology(G=G)
    else:
        raise ValueError(f"Cannot find or recognize: {specifier}")
