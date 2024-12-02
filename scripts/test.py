import os
import sys
import re
import csv
import time
import subprocess
from typing import List, Dict, Set, Tuple, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def run_command(command: List[str]) -> Tuple[Optional[str], Optional[str]]:
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        print(f"Command '{' '.join(command)}' failed with exit code {e.returncode}")
        print(f"Error Output: {e.stderr}")
        return None, None
    except FileNotFoundError:
        print(f"Command not found: {command[0]}")
        return None, None

def parse_csv(filename: str):
    collective_time = None
    synthesis_time = None
    with open(filename, mode="r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0].startswith("Collective Time"):
                collective_time = row[1].strip()
            elif row[0].startswith("Synthesis Time"):
                synthesis_time = row[1].strip()
    return collective_time, synthesis_time

def main():
    central_filename = "results/result.csv"
    with open(central_filename, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Topology","Collective","Synthesizer","Num Beams","Collective Time","Synthesizer Time"])

        topologies = ["grid"]
        collectives = ["all_gather"]
        synthesizers = ["naive", "tacos", "greedy_tacos", "multiple_tacos", "beam", "ilp"]
        for collective in collectives:
            for topology in topologies:
                for synthesizer in synthesizers:
                    for num_beams in [5]:
                        command = ["python", "-m", "runner.synthesize", 
                            "--topology", topology, 
                            "--collective", collective,
                            "--synthesizer", synthesizer,
                            "--num_beams", str(num_beams),
                            "--gen_video"
                        ]
                        print(f"Running: {' '.join(command)}")
                        run_command(command)
                        collective_time, synthesizer_time = parse_csv(os.path.join("results",f"t={topology}_c={collective}_s={synthesizer}","result.csv"))
                        writer.writerow([topology, collective, synthesizer, num_beams, collective_time, synthesizer_time])

if __name__ == "__main__":
    start = time.perf_counter()
    main()
    end = time.perf_counter()
    print(f"All tests took a total of {end-start:.2f} seconds")