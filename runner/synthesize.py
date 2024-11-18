from helper.timer import Timer
from path_solver.congestionful_solver import CongestionfulSolver
from time_translator.simple_translator import SimpleTranslator

# == import topologies ==
from topology.mesh import Mesh

# == import collectives ==
from collective.all_gather import AllGather


def main():
    # == setup ==
    verbose = False

    # create topology
    width = 3
    bandwidth = 50  # link bandwidth, GB/s
    alpha = 2  # link latency, us

    beta = 1e6 / (bandwidth * 1024)  # us/MB
    topology = Mesh(width=width, height=width, link_alpha_beta=(alpha, beta))

    # create collective
    collective = AllGather(npus_count=topology.npus_count, collectives_count=1,
                           chunk_size=1)

    # time-expanded model
    # set initial time
    # FIXME: assumption: All-Gather will take at least (width - 1) * 2 timestep (for 2D Mesh)
    # FIXME: setting this to 1 is most accurate, but slow in synthesis
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
        finished, reached_count = model.solve(verbose=verbose)

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
    solver_timer.stop()

    # Time-domain translation (ordering-based)
    time_translator_timer.start()
    time_estimator = SimpleTranslator(topology=topology,
                                      collective=collective,
                                      ordered_path=path)
    collective_time = time_estimator.run()
    time_translator_timer.stop()

    # print synthesized path
    path.print_path()

    # Print result
    print()
    solver_timer.print(unit='s')
    time_translator_timer.print(unit='s')

    print()
    print(f"[Result] Collective Time: {collective_time:.2f} us")


if __name__ == '__main__':
    main()
