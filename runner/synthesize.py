import os
import sys
import re
import json
import random
import signal
import argparse
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from runner.animate import animate_collective
from runner.verify import verify_collective
from helper.git_hash import get_git_hash
from helper.timer import Timer
from topology.topology import Topology
from topology.built_in_topologies import get_topology
from collective.collective import Collective
from collective.all_gather import AllGather
from collective.all_to_all import AllToAll
from collective.scatter import Scatter
from collective.broadcast import Broadcast
from collective.gather import Gather
from synthesizer.naive_synthesizer import NaiveSynthesizer
from synthesizer.tacos_synthesizer import TACOSSynthesizer
from synthesizer.greedy_tacos_synthesizer import GreedyTACOSSynthesizer
from synthesizer.multiple_tacos_synthesizer import MultipleTACOSSynthesizer
from synthesizer.beam_synthesizer import BeamSynthesizer
from synthesizer.ilp_synthesizer import ILPSynthesizer
signal.signal(signal.SIGINT, signal.SIG_DFL)

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
    parser.add_argument("--gen_video", action="store_true", required=False, help="Generate video")
    parser.add_argument("--show", action="store_true", required=False, help="Show animation")
    parser.add_argument("--seed", action="store", type=int, required=False, default=2430, help="Random seed")
    parser.add_argument("--num_trials", action="store", type=int, required=False, default=1, help="Number of trials")
    # Algorithm-specific arguments
    parser.add_argument("--num_beams", action="store", type=int, required=False, default=1, help="Beam width for beam search")
    parser.add_argument("--fitness_type", action="store", type=str, required=False, default="chunk_count", help="Fitness function for beam serach")
    args = parser.parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)

    if args.save is None:
        topology_name = args.topology.replace('/','-').replace('\\','-').replace('.csv','')
        collective_name = args.collective.replace('/','-').replace('\\','-').replace('.csv','')
        args.save = os.path.join("results", f"t={topology_name}_c={collective_name}_s={args.synthesizer}")
        if args.synthesizer=="multiple" or args.synthesizer=="":
            args.save += f"_{args.num_beams}"
    os.makedirs(args.save, exist_ok=True)
    with open(os.path.join(f"{args.save}", "args.json"), "w", newline="") as f:
        json.dump(vars(args)|{"git_hash":get_git_hash()}, f, indent=4)
    print(f"Saving to {args.save}")
    ####################################################################################################
    # TOPOLOGY
    ####################################################################################################
    if os.path.exists(args.topology):
        topology = Topology(filename=args.topology)
    else:
        topology = get_topology(args.topology)
    ####################################################################################################
    # COLLECTIVE
    ####################################################################################################
    if os.path.exists(args.collective):
        collective = Collective(filename=args.collective)
    elif args.collective=="all_gather":
        collective = AllGather(npus_count=topology.num_nodes, collectives_count=1)
    elif args.collective=="all_to_all":
        collective = AllToAll(npus_count=topology.num_nodes, collectives_count=1)
        collective.write_json("all_to_all.json")
    elif match := re.match(r"^scatter_(\d+)$",args.collective):
        collective = Scatter(npus_count=topology.num_nodes, src=int(match.group(1)), collectives_count=1)
    elif match := re.match(r"^broadcast_(\d+)$",args.collective):
        collective = Broadcast(npus_count=topology.num_nodes, src=int(match.group(1)), collectives_count=1)
    elif match := re.match(r"^gather_(\d+)$",args.collective):
        collective = Gather(npus_count=topology.num_nodes, dest=int(match.group(1)), collectives_count=1)
    else:
        raise FileNotFoundError(f"Cannot find {args.collective}")
    ####################################################################################################
    # SYNTHESIZER
    ####################################################################################################
    for trial in range(1,args.num_trials+1):
        timer = Timer(name="Synthesizer")
        timer.start()
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
            synthesizer.solve(verbose=args.verbose,filename=os.path.join(args.save, f"result_{trial}.lp"),time_limit=60)
            synthesizer.write(os.path.join(args.save, f"result_{trial}.sol"))
        else:
            raise NotImplementedError(f"Synthesizer {args.synthesizer} not supported")
        timer.stop()
        print("Collective Time:",synthesizer.current_time,"ns")
        print("Synthesis Time:",timer.get_time(),"s")
        synthesizer.write_csv(os.path.join(args.save, f"result_{trial}.csv"),synthesis_time=timer.get_time())
        if not verify_collective(os.path.join(args.save, f"result_{trial}.csv"), topology=topology, collective=collective):
            os.remove(os.path.join(args.save, f"result_{trial}.csv"))
            raise ValueError(f"Synthesized algorithm is invalid!")
        if args.gen_video:
            animate_collective(os.path.join(args.save, f"result_{trial}.csv"), save_name=os.path.join(args.save, f"result_{trial}.mp4"), show=args.show)

if __name__ == '__main__':
    main()
