import os
import re
import argparse

from topology.topology import Topology
from collective.collective import Collective
from collective.all_gather import AllGather
from synthesizer.ilp_synthesizer import ILPSynthesizer


from helper.timer import Timer
from path_solver.congestionful_solver import CongestionfulSolver
from time_translator.simple_translator import SimpleTranslator


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
    # parser.add_argument("--num_trials", action="store", type=int, required=False, help="Number of trials")
    # Algorithm-specific arguments
    parser.add_argument("--num_beams", action="store", type=int, required=False, default=1, help="Beam width for beam search")
    
    args = parser.parse_args()

    if args.save is None:
        args.save = f"results/t={args.topology.replace('/','-').replace('.csv','')}_c={args.collective.replace('/','-').replace('.csv','')}_s={args.synthesizer}"
        if args.synthesizer=="multiple" or args.synthesizer=="":
            args.save += f"_{args.num_beams}"
    os.makedirs(args.save, exist_ok=True)
    print(f"Saving to f{args.save}")
    ####################################################################################################
    # TOPOLOGY
    ####################################################################################################
    if os.path.exists(args.topology):
        topology = Topology(filename=args.topology)
    elif args.topology=="mesh":
        raise NotImplementedError("Mesh not supported")
        # width = 3
        # bandwidth = 50  # link bandwidth, GB/s
        # alpha = 2  # link latency, us

        # beta = 1e6 / (bandwidth * 1024)  # us/MB
        # topology = Mesh(width=width, height=width, link_alpha_beta=(alpha, beta))
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
    # SOLVE
    ####################################################################################################
    if args.synthesizer=="tacos":
        raise NotImplementedError()
    elif args.synthesizer=="greedy":
        raise NotImplementedError()
    elif args.synthesizer=="multiple":
        raise NotImplementedError()
    elif args.synthesizer=="beam":
        raise NotImplementedError()
    elif args.synthesizer=="ilp":
        synthesizer = ILPSynthesizer(topology=topology,collective=collective)
        synthesizer.solve(verbose=args.verbose,filename=args.save+"/result.lp")
        synthesizer.write(args.save+"/result.sol")
        synthesizer.write_csv(args.save+"/result.csv")
    else:
        raise NotImplementedError(f"Synthesizer {args.synthesizer} not supported")
    ####################################################################################################
    # WRITE OUT
    ####################################################################################################

if __name__ == '__main__':
    main()
