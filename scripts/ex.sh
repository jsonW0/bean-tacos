#!/bin/bash
clear
python -m runner.synthesize --topology grid --collective all_gather --synthesizer tacos
python -m runner.synthesize --topology grid --collective all_gather --synthesizer ilp