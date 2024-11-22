import os
import re
import argparse
from helper.timer import Timer
from path_solver.congestionful_solver import CongestionfulSolver
from time_translator.simple_translator import SimpleTranslator
from topology.topology import Topology
from topology.mesh import Mesh
from collective.collective import Collective
from collective.all_gather import AllGather


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
        args.save = f"results/{args.topology.replace('/','-')}_{args.collective.replace('/','-')}_{args.synthesizer}"
        if args.synthesizer=="multiple" or args.synthesizer=="":
            args.save += f"_{args.num_beams}"
    print(args.save)
    ####################################################################################################
    # TOPOLOGY
    ####################################################################################################
    if os.path.exists(args.topology):
        topology = Topology(filename=args.topology)
    elif args.topology=="mesh":
        width = 3
        bandwidth = 50  # link bandwidth, GB/s
        alpha = 2  # link latency, us

        beta = 1e6 / (bandwidth * 1024)  # us/MB
        topology = Mesh(width=width, height=width, link_alpha_beta=(alpha, beta))
    else:
        raise FileNotFoundError(f"Cannot find {args.topology}")
    ####################################################################################################
    # COLLECTIVE
    ####################################################################################################
    if os.path.exists(args.collective):
        raise NotImplementedError(f"Does not yet support collective from file path")
        collective = Collective(filename=args.collective)
    elif args.collective=="all_gather":
        collective = AllGather(npus_count=topology.npus_count, collectives_count=1, chunk_size=1)
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
        # time-expanded model
        # set initial time
        # FIXME: assumption: All-Gather will take at least (width - 1) * 2 timestep (for 2D Mesh)
        # FIXME: setting this to 1 is most accurate, but slow in synthesis
        width = 3
        time = (width - 1) * 2
        # time = 1

        # timer
        solver_timer = Timer(name="PathSolver")
        solver_step_timer = Timer(name="StepTimer")
        time_translator_timer = Timer(name="TimeTranslator")

        # model
        model = None

        # Run congestionful solver
        solver_timer.start()
        while True:
            print(f"[Evaluating t = {time}]")
            solver_step_timer.start()

            # create model and run
            model = CongestionfulSolver(collective=collective,
                                        topology=topology,
                                        time=time,
                                        unit_rate=None,
                                        search_time_limit=None)
            finished, reached_count = model.solve(verbose=args.verbose)

            solver_step_timer.stop()

            solver_step_timer.print(unit='s')
            solver_step_timer.reset()

            if finished:
                # all chunks arrived the dest
                break
            else:
                # should expand TEN and continue
                time += 1

        path = model.get_path()
        print("HERE",model.get_path_numpy())
        solver_timer.stop()

        # Time-domain translation (ordering-based)
        # time_translator_timer.start()
        # time_estimator = SimpleTranslator(topology=topology,
        #                                 collective=collective,
        #                                 ordered_path=path)
        # collective_time = time_estimator.run()
        # time_translator_timer.stop()

        # print synthesized path
        path.print_path()

        # Print result
        print()
        solver_timer.print(unit='s')
        # time_translator_timer.print(unit='s')

        # print()
        # print(f"[Result] Collective Time: {collective_time:.2f} us")
    else:
        raise NotImplementedError(f"Synthesizer {args.synthesizer} not supported")
    ####################################################################################################
    # WRITE OUT
    ####################################################################################################

if __name__ == '__main__':
    main()
