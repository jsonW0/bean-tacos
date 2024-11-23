#!/bin/bash
clear; python -m runner.synthesize --topology tests/biangle.csv --collective all_gather --synthesizer tacos
python visualize_collective.py --filename results/t=tests-biangle_c=all_gather_s=tacos/result.csv

clear; python -m runner.synthesize --topology tests/triangle.csv --collective all_gather --synthesizer tacos
python visualize_collective.py --filename results/t=tests-triangle_c=all_gather_s=tacos/result.csv

clear; python -m runner.synthesize --topology tests/quadangle.csv --collective all_gather --synthesizer tacos
python visualize_collective.py --filename results/t=tests-quadangle_c=all_gather_s=tacos/result.csv

clear; python -m runner.synthesize --topology tests/bidirectional_ring.csv --collective all_gather --synthesizer tacos
python visualize_collective.py --filename results/t=tests-bidirectional_ring_c=all_gather_s=tacos/result.csv

clear; python -m runner.synthesize --topology tests/bidirectional_ring_slow.csv --collective all_gather --synthesizer tacos
python visualize_collective.py --filename results/t=tests-bidirectional_ring_slow_c=all_gather_s=tacos/result.csv

clear; python -m runner.synthesize --topology tests/heterogeneous.csv --collective all_gather --synthesizer tacos
python visualize_collective.py --filename results/t=tests-heterogeneous_c=all_gather_s=tacos/result.csv

clear; python -m runner.synthesize --topology grid --collective all_gather --synthesizer tacos --verbose
python visualize_collective.py --filename results/t=grid_c=all_gather_s=tacos/result.csv