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

class TeeOutput:
    def __init__(self, file_path, mode='w'):
        self.file_path = file_path
        self.mode = mode
        self.file = None
        self.original_stdout = None
        self.original_stderr = None

    def __enter__(self):
        self.file = open(self.file_path, self.mode, buffering=1)
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
        return self

    def write(self, data):
        if data:
            self.original_stdout.write(data)
            self.original_stdout.flush()
            self.file.write(data)
            self.file.flush()

    def flush(self):
        self.original_stdout.flush()
        self.file.flush()

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        if self.file:
            self.file.close()

def run_command(command: List[str]):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    stdout_lines = []
    stderr_lines = []
    try:
        for line in process.stdout:
            print("\t\t"+line, end="")
            stdout_lines.append(line)
        for line in process.stderr:
            print("\t\t"+line, end="", file=sys.stderr)
            stderr_lines.append(line)
        process.wait()
    except Exception as e:
        print(f"Error during execution: {e}", file=sys.stderr)
        process.terminate()    
    return process.returncode, ''.join(stdout_lines), ''.join(stderr_lines)

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
    return float(collective_time), float(synthesis_time)

def main():
    central_filename = "results/result.csv"
    with open(central_filename, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Topology","Collective","Synthesizer","Num Beams","Trial","Collective Time","Synthesizer Time"])

        topologies = ["wheel_n=10_alpha=0_beta=1"]#,"grid_w=2_h=4_alpha=0_beta=1",]
        collectives = ["all_gather"]
        # synthesizers = ["ilp"]
        synthesizers = ["naive", "tacos", "greedy_tacos", "multiple_tacos", "beam"]#, "ilp"]
        for collective in collectives:
            for topology in topologies:
                for synthesizer in synthesizers:
                    for num_beams in [5]:
                        begin = time.perf_counter()
                        command = ["python", "-m", "runner.synthesize", 
                            "--topology", topology, 
                            "--collective", collective,
                            "--synthesizer", synthesizer,
                            # "--gen_video",
                        ]
                        if synthesizer in {"multiple_tacos", "beam"}:
                            command.extend([
                                "--num_beams", str(num_beams),
                            ])
                        if synthesizer in {"naive", "tacos", "greedy_tacos", "multiple_tacos", "beam"}:
                            num_trials = 5
                            command.extend([
                                "--num_trials", str(num_trials),
                            ])
                        else:
                            num_trials = 1
                        print(f"Running: {' '.join(command)}")
                        return_code, stdout, stderr = run_command(command)
                        finish = time.perf_counter()
                        if return_code!=0:
                            print(f"\tFailed!")
                        else:
                            for trial in range(1,num_trials+1):
                                collective_time, synthesizer_time = parse_csv(os.path.join("results",f"t={topology}_c={collective}_s={synthesizer}",f"result_{trial}.csv"))
                                writer.writerow([topology, collective, synthesizer, num_beams, collective_time, synthesizer_time])
                                print(f"\tColl={collective_time:.2f}_Synth={synthesizer_time:.2f}_Clock={finish-begin:.2f}")

if __name__ == "__main__":
    with TeeOutput("results/log.txt"):
        start = time.perf_counter()
        main()
        end = time.perf_counter()
        print(f"All tests took a total of {end-start:.2f} seconds")