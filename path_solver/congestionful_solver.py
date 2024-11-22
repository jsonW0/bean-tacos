import numpy as np
import gurobipy as gp
from gurobipy import GRB
from helper.typing import *
from collective.collective import Collective
from topology.topology import Topology
from path_solver.ordered_path import OrderedPath
from path_solver.time_expanded_network import TimeExpandedNetwork
import copy
import os


class CongestionfulSolver:
    def __init__(self,
                 collective: Collective,
                 topology: Topology,
                 time: int,
                 unit_rate: Optional[Time] = None,
                 search_time_limit: Optional[Time] = None):
        # model
        self.model = gp.Model("ExpandedGraphMultiWeight")

        if search_time_limit is not None:
            self.model.Params.TimeLimit = search_time_limit

        # hyperparameters
        self.M = 1e6

        # parameters
        self.collective = collective
        self.topology = topology
        self.ten = TimeExpandedNetwork(topology=topology,
                                       chunk_size=collective.chunk_size,
                                       timesteps_count=time,
                                       unit_rate=unit_rate)

        # common variables
        self.precondition = self.collective.precondition
        self.postcondition = self.collective.postcondition

        self.npus_count = self.topology.npus_count
        self.chunks_count = collective.chunks_count
        self.links_count = self.ten.links_count

        # model variable
        self.time = time

        # method
        self._initialize_vars(model=self.model)
        self._set_objective(model=self.model)
        self._set_constraints(model=self.model)

    def _initialize_vars(self, model: gp.Model) -> None:
        self.contains = model.addVars(self.chunks_count, self.npus_count, (self.time + 1),
                                      vtype=GRB.BINARY, name='contains')
        self.sent = model.addVars(self.chunks_count, self.links_count,
                                  vtype=GRB.BINARY, name='sent')

    def _set_objective(self, model: gp.Model) -> None:
        self.objective = model.addVar(vtype=GRB.INTEGER, lb=0, name='objective')
        model.addLConstr(
            self.objective == gp.quicksum((self.contains[c, dest, self.time] for (c, dest) in self.postcondition)))

        model.setObjective(self.objective, sense=GRB.MAXIMIZE)

    def _set_constraints(self, model: gp.Model) -> None:
        for c in range(self.chunks_count):
            for src in range(self.npus_count):
                if (c, src) in self.precondition:
                    model.addLConstr(self.contains[c, src, 0] == 1)
                else:
                    model.addLConstr(self.contains[c, src, 0] == 0)

        for c in range(self.chunks_count):
            for e in range(self.links_count):
                t_src, t_dest, src, dest = self.ten.unroll_link_id(e)
                large_if_not_sent = (1 - self.sent[c, e])

                model.addLConstr(self.contains[c, src, t_src] >= 1 - large_if_not_sent)
                model.addLConstr(self.contains[c, dest, t_dest] >= 1 - large_if_not_sent)

        for c in range(self.chunks_count):
            for n in range(self.npus_count):
                for t in range(1, self.time + 1):
                    large_if_not_contains = (1 - self.contains[c, n, t]) * self.M

                    incoming_edges = self.ten.incoming_links(timestep=t, dest=n)
                    flows = gp.quicksum(self.sent[c, e] for e in incoming_edges)
                    model.addLConstr(flows >= 1 - large_if_not_contains)

        # for e in self.ten.conflict_edges():
        #     flows = gp.quicksum(self.sent[c, e] for c in range(self.chunks_count))
        #     model.addLConstr(flows <= 1)

        for e in range(self.links_count):
            conflicts = self.ten.conflicting_links(link_id=e)

            if len(conflicts) > 0:
                flows = gp.quicksum(self.sent[c, ee] for ee in conflicts for c in range(self.chunks_count))
                model.addLConstr(flows <= 1)


        # for c in range(self.chunks_count):
        #     for src in range(self.npus_count):
        #         for dest in range(self.npus_count):
        #             for time in range(self.time):
        #                 large_if_not_sent = (1 - self.sent[c, src, dest, time]) * self.M
        #
        #                 weight = self.graph_weights[src, dest]
        #                 time_end = min(time + weight, self.time)
        #                 model.addLConstr(gp.quicksum((self.sent[c1, src, dest, t] for t in range(time + 1, time_end)
        #                                               for c1 in range(self.chunks_count))) <= large_if_not_sent)

    def _add_self_loop(self):
        graph = copy.deepcopy(self.topology.topology)
        for i in range(self.npus_count):
            graph[i, i] = True
        return graph

    def solve(self, verbose: bool = True) -> Tuple[bool, int]:
        self.model.Params.OutputFlag = verbose
        self.model.optimize()

        chunks_arrived = int(round(self.objective.X, ndigits=0))
        finished = chunks_arrived >= len(self.postcondition)

        return finished, chunks_arrived

    def update_time(self, new_time: int) -> None:
        self.time = new_time

        self._initialize_vars(model=self.model)
        self._set_objective(model=self.model)
        self._set_constraints(model=self.model)

    # def get_path(self) -> np.array:
    #     flow = self.model.getAttr('x', self.sent.values())
    #     flow = np.array(flow).reshape((self.chunks_count, self.links_count))
    #
    #     path_numpy = np.zeros(shape=(self.chunks_count, self.npus_count, self.npus_count, self.time), dtype=bool)
    #     for (c, e), sent in np.ndenumerate(flow):
    #         t, _, src, dest = self.ten.unroll_link_id(link_id=e)
    #
    #         if sent >= 1:
    #             path_numpy[c, src, dest, t] = True
    #             if src == 0 and dest != 0:
    #                 print(c, dest, t)
    #         else:
    #             path_numpy[c, src, dest, t] = False
    #
    #     return path_numpy

    def get_path(self) -> OrderedPath:
        flow = self.model.getAttr('x', self.sent.values())
        flow = np.array(flow).reshape((self.chunks_count, self.links_count))

        path_numpy = np.zeros(shape=(self.chunks_count, self.npus_count, self.npus_count, self.time), dtype=bool)
        for (c, e), sent in np.ndenumerate(flow):
            t, _, src, dest = self.ten.unroll_link_id(link_id=e)

            if sent >= 1:
                path_numpy[c, src, dest, t] = True
            else:
                path_numpy[c, src, dest, t] = False

        path = OrderedPath(topology=self.topology,
                           chunks_count=self.chunks_count)
        path.translate_ten_path(ten_path=path_numpy)

        return path

    def get_path_numpy(self) -> OrderedPath:
        flow = self.model.getAttr('x', self.sent.values())
        flow = np.array(flow).reshape((self.chunks_count, self.links_count))

        path_numpy = np.zeros(shape=(self.chunks_count, self.npus_count, self.npus_count, self.time), dtype=bool)
        for (c, e), sent in np.ndenumerate(flow):
            t, _, src, dest = self.ten.unroll_link_id(link_id=e)

            if sent >= 1:
                path_numpy[c, src, dest, t] = True
            else:
                path_numpy[c, src, dest, t] = False

        return path_numpy

    def get_contains(self) -> np.array:
        contains = self.model.getAttr('x', self.contains.values())
        contains = np.array(contains, dtype=bool).reshape((self.chunks_count, self.npus_count, (self.time + 1)))
        return contains

    def _save_temp_result(self, dir: str) -> None:
        sent_file = os.path.join(dir, 'sent.npy')
        contains_file = os.path.join(dir, 'contains.npy')
        np.save(sent_file, self.sent_numpy())
        np.save(contains_file, self.contains_numpy())

    def _load_result(self, dir: str) -> None:
        self.model.NumStart = 1

        sent_file = os.path.join(dir, 'sent.npy')
        contains_file = os.path.join(dir, 'contains.npy')

        sent = np.load(sent_file)
        contains = np.load(contains_file)

        for index, var in np.ndenumerate(sent):
            self.sent[index].start = var

        for index, var in np.ndenumerate(contains):
            self.contains[index].start = var
