# from helper.typing import *
# from topology.topology import Topology


# class Mesh(Topology):
#     """
#     Simple Mesh topology with (width x height) size and homogeneous latency/BW.
#     """

#     def __init__(self,
#                  width: int,
#                  height: int,
#                  link_alpha_beta: LinkAlphaBeta):
#         """
#         Mesh topology initializer.

#         :param width:
#         :param height:
#         :param link_alpha_beta:
#         """
#         # superclass initialize
#         npus_count = width * height
#         super().__init__(npus_count=npus_count)

#         # create horizontal (width-wise) links
#         for row in range(height):
#             for col in range(width - 1):
#                 src = (row * width) + col
#                 dest = src + 1
#                 self.connect(src=src, dest=dest, link_alpha_beta=link_alpha_beta)

#         # create vertical (height-wise) links
#         for row in range(height - 1):
#             for col in range(width):
#                 src = (row * width) + col
#                 dest = src + width
#                 self.connect(src=src, dest=dest, link_alpha_beta=link_alpha_beta)
