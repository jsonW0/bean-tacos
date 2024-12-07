import os
import csv
import math
from collections import defaultdict
from topology.topology import Topology
from collective.collective import Collective

def lt(a, b, rel_tol=1e-9):
    return a<b and not math.isclose(a, b, rel_tol=rel_tol)

def leq(a, b, rel_tol=1e-9):
    return a<b or math.isclose(a, b, rel_tol=rel_tol)

def verify_collective(filename: str, topology: Topology, collective: Collective, rel_tol=1e-6) -> bool:
    edge_attributes = {}
    edge_chunk_list = {}
    # Read in file
    with open(filename, mode="r", newline="") as f:
        reader = csv.reader(f)
        for i,row in enumerate(reader):
            if i==0:
                if row[0]=="NPUs Count" and int(row[1])>0:
                    npu_count = int(row[1])
                else:
                    raise ValueError(f"Expected 'NPUs Count,int' but got {row}")
            elif i==1:
                if row[0]=="Links Count" and int(row[1])>0:
                    link_count = int(row[1])
                else:
                    raise ValueError(f"Expected 'Links Count,int' but got {row}")
            elif i==2:
                if row[0]=="Chunks Count" and int(row[1])>0:
                    chunk_count = int(row[1])
                else:
                    raise ValueError(f"Expected 'Chunks Count,int' but got {row}")
            elif i==3:
                if row[0]=="Chunk Size" and float(row[1])>0:
                    chunk_size = float(row[1])
                else:
                    raise ValueError(f"Expected 'Chunk Size,float' but got {row}")
            elif i==4:
                if row[0]=="Collective Time" and float(row[1])>0 and row[2]=="ns":
                    collective_time = float(row[1])
                else:
                    raise ValueError(f"Expected 'Collective Time,float,ns' but got {row}")
            elif i==5:
                if row[0]=="Synthesis Time" and float(row[1])>0 and row[2]=="s":
                    synthesis_time = float(row[1])
                else:
                    raise ValueError(f"Expected 'Synthesis Time,float,s' but got {row}")
            elif i==6 and not (row==["SrcID","DestID","Latency (ns)","Bandwidth (GB/s)","Chunks (ID:ns:ns)"]):
                raise ValueError(f"Expected 'SrcID,DestID,Latency (ns),Bandwidth (GB/s),Chunks (ID:ns:ns)' but got {row}")
            elif i>=7:
                edge = (int(row[0]),int(row[1]))
                edge_attributes[edge] = (float(row[2]),float(row[3]))
                edge_chunk_list[edge] = []
                for i in range(4,len(row)):
                    chunk_id, send_time, rec_time = row[i].split(":")
                    chunk_id, send_time, rec_time = int(chunk_id), float(send_time), float(rec_time)
                    edge_chunk_list[edge].append((chunk_id, send_time, rec_time))
    # Header is correct
    if npu_count!=topology.num_nodes:
        raise ValueError(f"Expected {topology.num_nodes} nodes but file indicates {npu_count}")
    if link_count!=topology.num_edges:
        raise ValueError(f"Expected {topology.num_edges} edges but file indicates {link_count}")
    if set(edge_chunk_list.keys())!=set(topology.G.edges):
        raise ValueError(f"Edges do not match: {set(edge_chunk_list.keys()) ^ set(topology.G.edges)}")
    for edge in edge_chunk_list.keys():
        if not math.isclose(edge_attributes[edge][0],topology.G.get_edge_data(*edge)["alpha"],rel_tol=rel_tol) or not math.isclose(edge_attributes[edge][1],topology.G.get_edge_data(*edge)["beta"],rel_tol=rel_tol):
            raise ValueError(f"Edge information does not match: topology indicates {(topology.G.get_edge_data(*edge)['alpha'],topology.G.get_edge_data(*edge)['beta'])} but file indicates {edge_attributes[edge]}")
    if chunk_count!=collective.num_chunks:
        raise ValueError(f"Expected {collective.num_chunks} chunks but file indicates {chunk_count}")
    if not math.isclose(chunk_size,collective.chunk_size,rel_tol=rel_tol):
        raise ValueError(f"Expected {collective.chunk_size} chunk_size but file indicates {chunk_size}")
    if not math.isclose(collective_time,max([rec_time for transmissions in edge_chunk_list.values() for chunk_id,sent_time,rec_time in transmissions]),rel_tol=rel_tol):
        raise ValueError(f"Listed collective time {collective_time} does not match that indicated by transmissions {max([rec_time for transmissions in edge_chunk_list.values() for chunk_id,send_time,rec_time in transmissions])}")
    # Links are right duration
    for edge,transmissions in edge_chunk_list.items():
        for chunk_id,send_time,rec_time in transmissions:
            link_delay = edge_attributes[edge][0]+(chunk_size/(1<<30))*(1e9/edge_attributes[edge][1])
            if not math.isclose(send_time + link_delay, rec_time, rel_tol=rel_tol):
                raise ValueError(f"Edge {edge} chunk {chunk_id} should have rec-send={link_delay} but got {rec_time}-{send_time}={rec_time-send_time}")
    # Links send one chunk at a time
    for edge,transmissions in edge_chunk_list.items():
        for i in range(len(transmissions)):
            chunk_a, send_a, rec_a = transmissions[i]
            for j in range(i+1,len(transmissions)):
                chunk_b, send_b, rec_b = transmissions[j]
                if chunk_a==chunk_b:
                    raise ValueError(f"Link {edge} sent chunk {chunk_a} multiple times")
                if leq(send_a,send_b,rel_tol=rel_tol) and lt(send_b,rec_a,rel_tol):
                    raise ValueError(f"Link {edge} sent chunk {chunk_b} during {chunk_a}: {send_a}<={send_b}<{rec_a}")
                if leq(send_b,send_a,rel_tol=rel_tol) and lt(send_a,rec_b,rel_tol):
                    raise ValueError(f"Link {edge} sent chunk {chunk_a} during {chunk_b}: {send_b}<={send_a}<{rec_b}")
    precondition = defaultdict(set)
    for chunk, node in collective.precondition:
        precondition[node].add(chunk)
    # Links send chunks only if they have it or is precondition
    for edge,transmissions in edge_chunk_list.items():
        src, dest = edge
        for chunk_id,send_time,rec_time in transmissions:
            possesses = chunk_id in precondition[src]
            for edge2,transmissions2 in edge_chunk_list.items():
                src2, dest2 = edge2
                if dest2==src:
                    for chunk_id2,send_time2,rec_time2 in transmissions2:
                        if chunk_id==chunk_id2 and leq(rec_time2,send_time,rel_tol=rel_tol):
                            possesses = True
            if not possesses:
                raise ValueError(f"Link {edge} tried to send chunk {chunk_id} before possession")
    # Postcondition is satisfied at end 
    postcondition = defaultdict(set)
    for chunk, node in collective.postcondition:
        postcondition[node].add(chunk)
    
    for node in precondition.keys():
        for chunk in precondition[node]:
            if chunk in postcondition[node]:
                postcondition[node].remove(chunk)
    for edge,transmissions in edge_chunk_list.items():
        src, dest = edge
        for chunk_id,send_time,rec_time in transmissions:
            if chunk_id in postcondition[dest]:
                postcondition[dest].remove(chunk_id)
    for node in postcondition.keys():
        if len(postcondition[node])>0:
            raise ValueError(f"Postcondition error: node {node} doesn't have chunks {postcondition[node]}")

    return True