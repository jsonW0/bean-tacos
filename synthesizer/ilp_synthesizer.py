import csv
import gurobipy as gp
from gurobipy import GRB
from helper.typing import *
from topology.topology import Topology
from collective.collective import Collective

class ILPSynthesizer:
    def __init__(self, topology: Topology, collective: Collective, big_num: float = 1e4):
        self.topology = topology
        self.collective = collective
        self.chunk_size = collective.chunk_size

        self.nodes = self.topology.G.nodes
        self.edges = self.topology.G.edges
        self.chunks = self.collective.chunks

        self.model = gp.Model("SynthesizeCollectiveAlgorithm")
        self.big_num = big_num

        self._initialize_vars()
        self._set_objective()
        self._set_constraints()

    def _initialize_vars(self) -> None:
        self.total_time = self.model.addVar(vtype=GRB.CONTINUOUS, name="T")
        self.receive_time = self.model.addVars(self.nodes, self.chunks, vtype=GRB.CONTINUOUS, name="receive")
        self.send_time = self.model.addVars(self.edges, self.chunks, vtype=GRB.CONTINUOUS, name="send")
        self.send_bool = self.model.addVars(self.edges, self.chunks, vtype=GRB.BINARY, name="used")
        self.order_bool = self.model.addVars(self.edges, self.chunks, self.chunks, vtype=GRB.BINARY, name="order")
        self.send_bool2 = self.model.addVars(self.edges, self.chunks, self.chunks, vtype=GRB.BINARY, name="used2")
    
    def _set_objective(self) -> None:
        self.model.setObjective(self.total_time, sense=GRB.MINIMIZE)
    
    def _set_constraints(self) -> None:
        # All nodes receive precondition chunks at t=0
        self.model.addConstrs((self.receive_time[node, chunk] == 0 for chunk, node in self.collective.precondition), name="precondition")
        # All postconditions must receive chunk from one neighbor
        self.model.addConstrs((sum(self.send_bool[src, dest, chunk] for src, edge_dest in self.edges if edge_dest==dest) == 1 for chunk, dest in self.collective.postcondition if ((chunk, dest) not in self.collective.precondition)), name="postcondition")
        # Total time is when all postconditions have been marked received 
        self.model.addConstrs((self.receive_time[node, chunk] <= self.total_time for chunk, node in self.collective.postcondition), name="postcondition_time")
        
        # Given a send from i->j of chunk c, the src must have received the chunk before sending, and the arrival time must be send_time + delay
        self.model.addConstrs(((self.send_bool[src, dest, chunk] == 1) >> (self.receive_time[src, chunk] <= self.send_time[src, dest, chunk]) for src, dest in self.edges for chunk in self.chunks), name="sender_possesses")
        self.model.addConstrs(((self.send_bool[src, dest, chunk] == 1) >> (self.send_time[src, dest, chunk] + self.topology.get_delay((src,dest), self.chunk_size) == self.receive_time[dest, chunk]) for src, dest in self.edges for chunk in self.chunks), name="link_delay")
        # Otherwise, set send_time to a large number
        self.model.addConstrs(((self.send_bool[src, dest, chunk] == 0) >> (self.send_time[src, dest, chunk] == self.big_num) for src, dest in self.edges for chunk in self.chunks), name="send_default")


        # Exactly one of order_bool must be true
        self.model.addConstrs((self.order_bool[src, dest, chunk_a, chunk_b]+self.order_bool[src, dest, chunk_b, chunk_a] == 1 for src, dest in self.edges for chunk_a in self.chunks for chunk_b in self.chunks if chunk_a!=chunk_b), name="order_specified")
        # send_bool2 is and of send_bools
        self.model.addConstrs((self.send_bool2[src, dest, chunk_a, chunk_b] == gp.and_([self.send_bool[src, dest, chunk_a], self.send_bool[src, dest, chunk_b]]) for src, dest in self.edges for chunk_a in self.chunks for chunk_b in self.chunks if chunk_a!=chunk_b), name="send_conjunction")
        # Based on order, choose constraint
        self.model.addConstrs((
            (self.send_bool2[src, dest, chunk_a, chunk_b] == 1) >> (self.send_time[src, dest, chunk_a]-self.send_time[src, dest, chunk_b] >= 
            self.topology.get_delay((src,dest), self.chunk_size) - self.big_num*(1-self.order_bool[src, dest, chunk_b, chunk_a]))
            for src, dest in self.edges for chunk_a in self.chunks for chunk_b in self.chunks if chunk_a!=chunk_b
        ), name="overlap_pos")
        self.model.addConstrs((
            (self.send_bool2[src, dest, chunk_a, chunk_b] == 1) >> (self.send_time[src, dest, chunk_b]-self.send_time[src, dest, chunk_a] >= 
            self.topology.get_delay((src,dest), self.chunk_size) - self.big_num*(1-self.order_bool[src, dest, chunk_a, chunk_b]))
            for src, dest in self.edges for chunk_a in self.chunks for chunk_b in self.chunks if chunk_a!=chunk_b
        ), name="overlap_neg")

    def solve(self, time_limit: float = None, verbose: bool = False, filename: str = None) -> None:
        if time_limit is not None:
            self.model.Params.TimeLimit = time_limit
        self.model.Params.OutputFlag = verbose
        if filename is not None:
            self.model.write(filename)
        try:
            self.model.optimize()
        except:
            raise Exception("Gurobi cannot solve this ILP!")

    def write(self, filename: str) -> None:
        self.model.write(filename)
    
    @property
    def current_time(self):
        return self.model.getVarByName('T').X
    
    def write_csv(self, filename: str, synthesis_time: float) -> None:
        with open(filename, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["NPUs Count",len(self.nodes)])
            writer.writerow(["Links Count",len(self.edges)])
            writer.writerow(["Chunks Count",len(self.chunks)])
            writer.writerow(["Chunk Size",self.chunk_size])
            writer.writerow(["Collective Time",self.current_time,"ns"])
            writer.writerow(["Synthesis Time",synthesis_time,"s"])
            writer.writerow(["SrcID","DestID","Latency (ns)","Bandwidth (GB/s)","Chunks (ID:ns:ns)"])
            for src, dest in self.edges:
                chunks = []
                for chunk in self.chunks:
                    if self.model.getVarByName(f"used[{src},{dest},{chunk}]").X == 1:
                        send_time = self.model.getVarByName(f"send[{src},{dest},{chunk}]").X
                        receive_time = self.model.getVarByName(f"receive[{dest},{chunk}]").X
                        chunks.append((chunk,send_time,receive_time))
                writer.writerow([src,dest,self.edges[(src,dest)]["alpha"],self.edges[(src,dest)]["beta"]]+[":".join(str(y) for y in x) for x in chunks])