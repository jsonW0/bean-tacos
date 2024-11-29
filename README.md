# BEAN TACOS

Project Group: Emma Yang, Jason Wang, Edward Kang

Large-scale machine learning model training on distributed GPU clusters relies on collective communication to synchronize gradients and activations across accelerators. TACOS is a topology-aware approach to synthesizing the underlying algorithms for executing these collectives. However, while TACOS has provable gains in communication latency in many topologies, the greedy algorithm TACOS relies on presents unique challenges for finding near-optimal communication patterns in topologies with heterogeneous link bandwidths.

Inspired by state-of-the-art approaches in LLM decoding, our project aims to develop an enhanced algorithm, based on the beam search heuristic algorithm, that better incorporates the bandwidths of links across a topology in synthesizing a collective communication pattern. We would also like to evaluate and improve upon TACOS' robustness to bandwidth variance during the course of the execution of a collective and failures in the network.

### Setup
```
git clone https://github.com/jsonW0/tacos-ilp.git
cd tacos-ilp
conda env create -f environment.yml
conda activate tacos
```
The ILP formulation requires `gurobi`. Follow the [directions](https://www.gurobi.com/features/academic-named-user-license/) to get a free academic named user license. Ultimately, you should run `grbgetkey (some-key-id)` (after installing via conda).

### Specifying a Topology

You can specify an arbitrary analytical graph topology (switches need to be unrolled) with a `.csv` format. The first row is the number of nodes, the second row is an explanatory header, and the remaining rows are an edge list of source node index, destination node index, the latency in nanoseconds, and the bandwidth in GB/s.

E.g., this is a bidirectional ring of 5 nodes with one pair being bandwidth-constrained:
```
5
Src,Dest,Latency (ns),Bandwidth (GB/s)
0,1,500,50
1,0,500,50
1,2,500,50
2,1,500,50
2,3,500,50
3,2,500,50
3,4,500,50
4,3,500,50
4,0,500,1
0,4,500,1
```
Note that GB/s $\approx$ B/ns.

### Synthesizing an Algorithm

We can run the synthesis algorithm by invoking `runner.synthesize` as a Python module.

```
python -m runner.synthesize --topology tests/ring.csv --collective all_gather --synthesizer greedy --save results.csv
```

Learn more about the arguments with the `--help` flag.

### Understanding Output

The output will be a `.csv` file with the name given by the `--save` flag.

Here is an example output. You can see that the first few lines contains information about the collective algorithm, and the remaining lines describe each edge and the packets that go through (the chunk id, start transmission time, and end transmission time).
```
NPUs Count,5
Links Count,8
Chunks Count,5
Chunk Size,1048576,B
Collective Time,3906248,ns
Synthesis Time,3.14,s
SrcID,DestID,Latency (ns),Bandwidth (GB/s),Chunks (ID:ps)
0,1,0,1000,0:976562:0,4:1953124:976562
0,2,0,2000,0:488281:0,4:1464843:976562
1,2,0,1000,1:976562:0,3:1953124:976562
1,4,0,2000,1:488281:0,0:1464843:976562
2,3,0,1000,2:976562:0,0:1953124:976562,4:2929686:1953124,1:3906248:2929686
3,1,0,2000,3:488281:0,2:1464843:976562
3,4,0,1000,3:976562:0,2:1953124:976562
4,0,0,1000,4:976562:0,1:1953124:976562,2:2929686:1953124,3:3906248:2929686
```

You can visualize the collective algorithm by running `python visualize_collective.py --filename result.csv` which will display an interactive animation.