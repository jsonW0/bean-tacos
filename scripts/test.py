import os
import sys
import re
import csv
import time
import argparse
import subprocess
from contextlib import contextmanager
from typing import List, Dict, Set, Tuple, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pygwalker as pyg

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

@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--topologies", action="store", type=str, nargs='+', required=False, help="Name of topology or filepath to topology csv")
    parser.add_argument("--collectives", action="store", type=str, nargs='+', required=False, help="Name of collective pattern or filepath to collective csv")
    parser.add_argument("--synthesizers", action="store", type=str, nargs='+', required=False, help="Name of synthesis algorithm")
    parser.add_argument("--num_trials", action="store", type=int, required=False, default=30, help="Number of trials")
    parser.add_argument("--num_beams", action="store", type=int, nargs='+', required=False, default=[30], help="Beam width for beam search")
    parser.add_argument("--temperature", action="store", type=float, nargs='+', required=False, default=[0.], help="Temperature for beam search")
    parser.add_argument("--save_csv", action="store", type=str, required=False, default="results/result.csv", help="Name to save output csv")
    parser.add_argument("--save_html", action="store", type=str, required=False, default="results/result.html", help="Name to save output pyg html")
    parser.add_argument("--gen_video", action="store_true", required=False, help="Generate videos")
    parser.add_argument("--seed", action="store", type=int, required=False, default=2430, help="Random seed")
    args = parser.parse_args()
    
    header = ["Topology","Collective","Synthesizer","Num Beams","Temperature","Trial","Collective Time","Synthesizer Time"]
    write_header = True
    if os.path.isfile(args.save_csv):
        with open(args.save_csv, mode="r", newline="") as f:
            write_header = f.readline().strip() != ",".join(header)

    with open(args.save_csv, mode="a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(header)

        if args.topologies is None:
            args.topologies = ["nx_tutte_graph"]#["nx_wheel_graph__n=10"]
        if args.collectives is None:
            args.collectives = ["all_gather"]
        if args.synthesizers is None:
            args.synthesizers = ["naive", "tacos", "greedy_tacos", "multiple_tacos", "beam_chunk", "beam_shortest"]#, "ilp"]
        for collective in args.collectives:
            for topology in args.topologies:
                for synthesizer in args.synthesizers:
                    for num_beams in args.num_beams:
                        for temperature in args.temperature:
                            begin = time.perf_counter()
                            command = ["python", "-m", "runner.synthesize", 
                                "--topology", topology, 
                                "--collective", collective,
                                "--synthesizer", synthesizer,
                                "--seed", str(args.seed),
                            ]
                            if args.gen_video:
                                command.append("--gen_video")
                            if synthesizer in {"multiple_tacos", "beam"}:
                                command.extend([
                                    "--num_beams", str(num_beams),
                                    "--temperature", str(temperature),
                                ])
                            if synthesizer in {"naive", "tacos", "greedy_tacos", "multiple_tacos", "beam_chunk", "beam_shortest"}:
                                num_trials = args.num_trials
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
                                    writer.writerow([topology, collective, synthesizer, num_beams, temperature, trial, collective_time, synthesizer_time])
                                    print(f"\tColl={collective_time:.2f}_Synth={synthesizer_time:.2f}_Clock={finish-begin:.2f}")
    df = pd.read_csv(args.save_csv)
    with suppress_stdout():
        walker = pyg.walk(df)
    with open(args.save_html, mode="w", newline="") as f:
        f.write(walker.to_html())
if __name__ == "__main__":
    with TeeOutput("results/log.txt"):
        start = time.perf_counter()
        main()
        end = time.perf_counter()
        print(f"All tests took a total of {end-start:.2f} seconds")