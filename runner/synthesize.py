import os
import re
import argparse
import networkx as nx
import matplotlib.pyplot as plt
from runner.animate import animate_collective
from helper.timer import Timer
from topology.topology import Topology
from collective.collective import Collective
from collective.all_gather import AllGather
from synthesizer.naive_synthesizer import NaiveSynthesizer
from synthesizer.tacos_synthesizer import TACOSSynthesizer
from synthesizer.greedy_tacos_synthesizer import GreedyTACOSSynthesizer
from synthesizer.multiple_tacos_synthesizer import MultipleTACOSSynthesizer
from synthesizer.beam_synthesizer import BeamSynthesizer
from synthesizer.ilp_synthesizer import ILPSynthesizer


def main():
    ####################################################################################################
    # ARGPARSE
    ####################################################################################################
    parser = argparse.ArgumentParser()
    # General arguments
    parser.add_argument("--topology", action="store", type=str, required=True, help="Name of topology or filepath to topology csv")
    parser.add_argument("--collective", action="store", type=str, required=True, help="Name of collective pattern or filepath to collective csv")
    parser.add_argument("--synthesizer", action="store", type=str, required=True, help="Name of synthesis algorithm")
    parser.add_argument("--save", action="store", type=str, required=False, help="Name to save output csv")
    parser.add_argument("--verbose", action="store_true", required=False, help="Verbose")
    parser.add_argument("--show", action="store_true", required=False, help="Show animation")
    # parser.add_argument("--num_trials", action="store", type=int, required=False, help="Number of trials")
    # Algorithm-specific arguments
    parser.add_argument("--num_beams", action="store", type=int, required=False, default=1, help="Beam width for beam search")
    
    args = parser.parse_args()

    if args.save is None:
        args.save = f"results/t={args.topology.replace('/','-').replace('.csv','')}_c={args.collective.replace('/','-').replace('.csv','')}_s={args.synthesizer}"
        if args.synthesizer=="multiple" or args.synthesizer=="":
            args.save += f"_{args.num_beams}"
    os.makedirs(args.save, exist_ok=True)
    print(f"Saving to {args.save}")
    ####################################################################################################
    # TOPOLOGY
    ####################################################################################################
    if os.path.exists(args.topology):
        topology = Topology(filename=args.topology)
    elif args.topology=="grid":
        G = nx.convert_node_labels_to_integers(nx.grid_graph(dim=(3,3)).to_directed())
        for src, dest in G.edges:
            G.add_edge(src,dest,alpha=0,beta=1)
        topology = Topology(G=G)
    else:
        raise FileNotFoundError(f"Cannot find {args.topology}")
    ####################################################################################################
    # COLLECTIVE
    ####################################################################################################
    if os.path.exists(args.collective):
        raise NotImplementedError(f"Does not yet support collective from file path")
        collective = Collective(filename=args.collective)
    elif args.collective=="all_gather":
        collective = AllGather(npus_count=topology.num_nodes, collectives_count=1, chunk_size=1)
    else:
        raise FileNotFoundError(f"Cannot find {args.collective}")
    ####################################################################################################
    # SYNTHESIZER
    ####################################################################################################
    if args.synthesizer=="naive":
        synthesizer = NaiveSynthesizer(topology=topology,collective=collective)
        synthesizer.solve()
    elif args.synthesizer=="tacos":
        synthesizer = TACOSSynthesizer(topology=topology,collective=collective)
        synthesizer.solve()
    elif args.synthesizer=="greedy_tacos":
        synthesizer = GreedyTACOSSynthesizer(topology=topology,collective=collective)
        synthesizer.solve()
    elif args.synthesizer=="multiple_tacos":
        synthesizer = MultipleTACOSSynthesizer(topology=topology,collective=collective, num_beams=args.num_beams)
        synthesizer.solve()
    elif args.synthesizer=="beam":
        synthesizer = BeamSynthesizer(topology=topology,collective=collective, num_beams=args.num_beams)
        synthesizer.solve()
    elif args.synthesizer=="ilp":
        synthesizer = ILPSynthesizer(topology=topology,collective=collective)
        synthesizer.solve(verbose=args.verbose,filename=args.save+"/result.lp",time_limit=60)
        synthesizer.write(args.save+"/result.sol")
    else:
        raise NotImplementedError(f"Synthesizer {args.synthesizer} not supported")
    synthesizer.write_csv(args.save+"/result.csv")
    animate_collective(args.save+"/result.csv", save_name=args.save+"/result.mp4", show=args.show)

if __name__ == '__main__':
    main()
