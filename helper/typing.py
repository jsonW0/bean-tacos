from typing import List, Optional, Tuple, Dict, Set
from enum import Enum, auto

# Event Queue
Time = float  # e.g., 2.5 us

# Topology
NpuId = int
LinkId = Tuple[NpuId, NpuId]  # Link: (src, dest)
LinkWeight = float  # e.g., Latency: 2.5 us, BW: 3.7 us / MB
LinkAlphaBeta = Tuple[LinkWeight, LinkWeight]  # (alpha, beta)

# Collective
ChunkId = int
ChunkSize = float  # e.g., 2.7 MB

# Time-expanded Network (TEN)
Event = Tuple[LinkId, ChunkId, Time, Time]
TenTimestep = int  # TEN uses discretized Timestep
TenLinkId = int
TenLinkData = Tuple[TenTimestep, NpuId, NpuId]  # (start timestep, src, dest)
TenLinkDataFull = Tuple[TenTimestep, TenTimestep, NpuId, NpuId]  # (start timestep, finish timestep, src, dest)


# Backtracking
class ChunkStatus(Enum):
    Ready = auto(),
    InTransmission = auto()


ChunkRequest = Tuple[ChunkId, ChunkStatus]


# Chunk Arbitration (ordering)
class OrderingHeuristic(Enum):
    ShortestPathUntilNowFirst = auto(),
    LongestPathFromNowFirst = auto()
