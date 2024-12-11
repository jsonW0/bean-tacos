#!/bin/bash
clear
# Line experiment
# python scripts/test.py --topologies "grid__dim=(1,4)" "grid__dim=(1,8)" "grid__dim=(1,16)" "grid__dim=(1,32)" "grid__dim=(1,64)" "grid__dim=(1,128)"
# Ring experiment
# python scripts/test.py --topologies "ring__dim=(1,5)__slow=0.19" --synthesizer "naive" "tacos"
# Homogeneous grid experiment
# python scripts/test.py --topologies "grid__dim=(2,3)" "grid__dim=(2,4)" "grid__dim=(2,5)" "grid__dim=(3,3)" "grid__dim=(3,4)" "grid__dim=(3,5)" "grid__dim=(4,4)" "grid__dim=(4,5)" "grid__dim=(5,5)"
# Homogeneous torus experiment
# python scripts/test.py --topologies "torus__dim=(2,3)" "torus__dim=(2,4)" "torus__dim=(2,5)" "torus__dim=(3,3)" "torus__dim=(3,4)" "torus__dim=(3,5)" "torus__dim=(4,4)" "torus__dim=(4,5)" "torus__dim=(5,5)"
# Grid outage experiment
# python scripts/test.py --topologies "grid__dim=(4,4)__outages=[0]" "grid__dim=(4,4)__outages=[1]" "grid__dim=(4,4)__outages=[5]"
# python scripts/test.py --topologies "grid__dim=(4,4)__outages=[1,5]" "grid__dim=(4,4)__outages=[1,6]" "grid__dim=(4,4)__outages=[1,9]" "grid__dim=(4,4)__outages=[1,10]"
# Grid heterogeneity experiment
# python scripts/test.py --topologies "nx_grid_graph__dim=(4,4)__beta2=0.5__proportion=0.25" "nx_grid_graph__dim=(4,4)__beta2=0.5__proportion=0.5" "nx_grid_graph__dim=(4,4)__beta2=0.5__proportion=0.75" \
#                                     "nx_grid_graph__dim=(4,4)__beta2=0.25__proportion=0.25" "nx_grid_graph__dim=(4,4)__beta2=0.25__proportion=0.5" "nx_grid_graph__dim=(4,4)__beta2=0.25__proportion=0.75" \
#                                     "nx_grid_graph__dim=(4,4)__beta2=0.75__proportion=0.25" "nx_grid_graph__dim=(4,4)__beta2=0.75__proportion=0.5" "nx_grid_graph__dim=(4,4)__beta2=0.75__proportion=0.75"
# Hierarchical experiment
python scripts/test.py --topologies "tree__degrees=[2,2,2]__latencies=[0,0,0]__bandwidths=[100,10,1]" \
                                    "tree__degrees=[2,2,2]__latencies=[0,0,0]__bandwidths=[25,5,1]" \
                                    "tree__degrees=[2,2,2]__latencies=[0,0,0]__bandwidths=[4,2,1]" \
                                    "tree__degrees=[2,2,2]__latencies=[0,0,0]__bandwidths=[1,1,1]" \
                                    "tree__degrees=[2,3,3]__latencies=[0,0,0]__bandwidths=[100,10,1]" \
                                    "tree__degrees=[2,3,3]__latencies=[0,0,0]__bandwidths=[25,5,1]" \
                                    "tree__degrees=[2,3,3]__latencies=[0,0,0]__bandwidths=[4,2,1]" \
                                    "tree__degrees=[2,3,3]__latencies=[0,0,0]__bandwidths=[1,1,1]" \