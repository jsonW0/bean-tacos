import csv
import os
import argparse
import random
import subprocess
import re
from typing import Optional, Tuple, Dict, List, Any, Callable
import itertools
from tqdm import tqdm
from pprint import pprint
import math
import time

random.seed(2430)
LATENCY = 500


def params_to_file_name(output_dir: str, topology, params: List[str]) -> str:
    return os.path.join(output_dir, f"{topology}_" + "_".join(params) + ".csv")


def generate_ring(
    world_size: int,
    bandwidth_ratio: int,
    slow_link_proportion: float,
    csv_writer: csv.DictWriter,
) -> None:
    csv_writer.writerow([world_size])
    csv_writer.writerow(["Src", "Dest", "Latency (ns)", "Bandwidth (GB/s)"])
    # generate edge list
    edges = []
    for i in range(world_size):
        src = i
        dest = (i + 1) % world_size
        edges.append((src, dest))
        edges.append((dest, src))

    # sample slow edges
    slow_edges = random.sample(edges, int(len(edges) * slow_link_proportion))

    # write to csv
    for edge in edges:
        src, dest = edge
        bandwidth = 1 if edge in slow_edges else bandwidth_ratio
        csv_writer.writerow([src, dest, LATENCY, bandwidth])


def generate_outin(
    world_size: int, bandwidth_ratio: int, csv_writer: csv.DictWriter
) -> None:
    csv_writer.writerow([world_size])
    csv_writer.writerow(["Src", "Dest", "Latency (ns)", "Bandwidth (GB/s)"])
    for i in range(world_size):
        for j in range(world_size):
            if i != j:
                if abs(i - j) != 1 or (i == 0 and j == world_size - 1):
                    # slow inside
                    csv_writer.writerow([i, j, LATENCY, 1])
                    csv_writer.writerow([j, i, LATENCY, 1])
                else:
                    # fast inside (consecutive)
                    csv_writer.writerow([i, j, LATENCY, bandwidth_ratio])
                    csv_writer.writerow([j, i, LATENCY, bandwidth_ratio])


def generate_grid(
    world_size: int,
    bandwidth_ratio: int,
    slow_link_proportion: float,
    csv_writer: csv.DictWriter,
) -> None:
    csv_writer.writerow([world_size])
    csv_writer.writerow(["Src", "Dest", "Latency (ns)", "Bandwidth (GB/s)"])
    # generate edge list
    edges = []
    side_length = int(math.sqrt(world_size))
    for i in range(side_length):
        for j in range(side_length):
            node = i * side_length + j
            if j < side_length - 1:
                right_node = node + 1
                edges.append((node, right_node))
                edges.append((right_node, node))
            if i < side_length - 1:
                bottom_node = node + side_length
                edges.append((node, bottom_node))
                edges.append((bottom_node, node))

    # sample slow edges
    slow_edges = random.sample(edges, int(len(edges) * slow_link_proportion))

    # write to csv
    for edge in edges:
        src, dest = edge
        bandwidth = 1 if edge in slow_edges else bandwidth_ratio
        csv_writer.writerow([src, dest, LATENCY, bandwidth])


def generate_hierarchical(
    layer_sizes: Tuple[int], bandwidth_ratio: Tuple[int], csv_writer: csv.DictWriter
) -> None:
    assert len(layer_sizes) == len(bandwidth_ratio) - 1
    # support two layer for now
    assert len(layer_sizes) == 2

    csv_writer.writerow([layer_sizes[0] + layer_sizes[1] * layer_sizes[0]])
    csv_writer.writerow(["Src", "Dest", "Latency (ns)", "Bandwidth (GB/s)"])

    # generate edges for switch layer
    for i in range(1, layer_sizes[0] + 1):
        csv_writer.writerow([0, i, LATENCY, bandwidth_ratio[0]])
        # generate cube-mesh
        cube_mesh_ids = [
            layer_sizes[0] + (i - 1) * layer_sizes[1] + j
            for j in range(1, layer_sizes[1] + 1)
        ]
        for j in cube_mesh_ids:
            csv_writer.writerow([i, j, LATENCY, bandwidth_ratio[1]])
        for src in cube_mesh_ids:
            for dest in cube_mesh_ids:
                if src != dest:
                    csv_writer.writerow([src, dest, LATENCY, bandwidth_ratio[2]])


def get_graph_generation_fn(topology: str) -> Callable:
    if topology == "ring":
        return generate_ring
    elif topology == "outin":
        return generate_outin
    elif topology == "grid":
        return generate_grid
    elif topology == "hierarchical":
        return generate_hierarchical


def create_csv_files(output_dir: str, params: Dict[str, List[Any]]) -> None:
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    print(f"CSV files will be generated in the '{output_dir}' directory.")

    assert "topology" in params
    assert params["topology"] in ["ring", "outin", "hierarchical"]

    topology = params["topology"]
    del params["topology"]

    if topology == "ring":
        assert all(
            param in params
            for param in ["world_size", "bandwidth_ratio", "slow_link_proportion"]
        )
        # ring should only have scalar bandwidth ratios
        assert all(isinstance(ratio, int) for ratio in params["bandwidth_ratio"])
        for world_size, b_ratio, slow_prop in itertools.product(
            params["world_size"],
            params["bandwidth_ratio"],
            params["slow_link_proportion"],
        ):
            csv_filename = params_to_file_name(
                output_dir, topology, map(str, [world_size, b_ratio, slow_prop])
            )
            with open(csv_filename, "w", newline="") as csvfile:
                csvwriter = csv.writer(csvfile)
                generate_ring(world_size, b_ratio, slow_prop, csvwriter)
    elif topology == "outin":
        assert all(param in params for param in ["world_size", "bandwidth_ratio"])
        # outin should only have scalar bandwidth ratios
        assert all(isinstance(ratio, int) for ratio in params["bandwidth_ratio"])
        for world_size, b_ratio in itertools.product(
            params["world_size"], params["bm"]
        ):
            csv_filename = params_to_file_name(
                output_dir, topology, [world_size, b_ratio]
            )
            with open(csv_filename, "w", newline="") as csvfile:
                csvwriter = csv.writer(csvfile)
                generate_outin(world_size, b_ratio, csvwriter)
    elif topology == "grid":
        assert all(
            param in params
            for param in ["world_size", "bandwidth_ratio", "slow_link_proportion"]
        )
        assert all(isinstance(ratio, int) for ratio in params["bandwidth_ratio"])
        for world_size, b_ratio, slow_prop in itertools.product(
            params["world_size"],
            params["bandwidth_ratio"],
            params["slow_link_proportion"],
        ):
            csv_filename = params_to_file_name(
                output_dir, topology, [world_size, b_ratio, slow_prop]
            )
            with open(csv_filename, "w", newline="") as csvfile:
                csvwriter = csv.writer(csvfile)
                generate_grid(world_size, b_ratio, slow_prop, csvwriter)
    elif topology == "hierarchical":
        assert all(
            param in params
            for param in ["layer_sizes", "bandwidth_ratio", "slow_link_proportion"]
        )
        # hierarchical should have tuple bandwidth ratios
        assert all(isinstance(ratio, tuple) for ratio in params["bandwidth_ratio"])
        for layer_sizes, b_ratio, slow_prop in itertools.product(
            params["layer_sizes"], params["bm"], params["bbp"]
        ):
            csv_filename = params_to_file_name(
                output_dir, topology, [layer_sizes, b_ratio, slow_prop], output_dir
            )
            with open(csv_filename, "w", newline="") as csvfile:
                csvwriter = csv.writer(csvfile)
                generate_hierarchical(layer_sizes, b_ratio, csvwriter)
    else:
        raise ValueError(f"Invalid topology: {topology}")


import re
from typing import Optional

def extract_synthesis_time(output: str) -> Optional[float]:
    """
    Extracts the synthesis time in seconds from the output string

    Args:
        output (str): The output from the command.

    Returns:
        Optional[float]: The extracted synthesis time in seconds, or None if not found.
    """
    match = re.search(r"Synthesis Time:\s*([\d\.eE+-]+)\s*s", output)
    if match:
        return match.group(1)
    else:
        return None


def run_command(
    command: List[str], cwd: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Executes a shell command and captures its standard output and standard error.

    Args:
        command (List[str]): The command and its arguments as a list.
        cwd (Optional[str]): Directory to run the command in.

    Returns:
        Tuple[Optional[str], Optional[str]]: A tuple containing stdout and stderr, or (None, None) if an error occurs.
    """
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        print(f"Command '{' '.join(command)}' failed with exit code {e.returncode}")
        print(f"Error Output: {e.stderr}")
        return None, None
    except FileNotFoundError:
        print(f"Command not found: {command[0]}")
        return None, None



def parse_list(value: str):
    """
    Converts a string containing a list-like value into a list of the appropriate types.

    Args:
        value (str): The string to parse (e.g., "10, 20.5, hello").

    Returns:
        list: A list of integers, floats, or strings, as appropriate.
    """
    import ast
    def convert_element(element):
        element = element.strip()
        try:
            return ast.literal_eval(element)
        except (ValueError, SyntaxError):
            return element  # Fallback to string if no valid conversion
    
    return [convert_element(x) for x in value.split(",")]

def get_file_parameters(filepath: str):
    """
    Extracts labeled parameters enclosed in brackets [] from a filepath string.

    Args:
        filepath (str): The path of the file.

    Returns:
        Dict[str, str]: A dictionary of parameter labels and their extracted values.
    """
    filepath = filepath.replace("\\", "/")
    filepath = filepath[filepath.find("_") + 1: filepath.rfind("/")]
    
    # Regex pattern to extract both parameter names and values
    label_pattern = r"_?(\w+)\[(.*?)\]"
    matches = re.findall(label_pattern, filepath)
    
    # Convert matches into a dictionary
    parameters = {label: parse_list(value) for label, value in matches}
    return parameters

import os
import time
import csv
from typing import List

def run_synthesis_commands(
    params_list: List[str], input_dir: str, synthesis_times_csv: str = "synthesis_times.csv"
) -> None:
    """
    Executes synthesize.py commands for each CSV file in the input directory, extracts synthesis times,
    and writes the results to an output CSV file.

    Args:
        params_list (List[str]): List of parameter names to include in the CSV.
        input_dir (str): Directory containing input CSV files.
        output_csv (str): Path to the output results CSV file.
    """
    params_list.append("Algorithm")
    params_list.append("Synthesis Time (s)")
    algorithms = [
        {"name": "naive", "args": ["--synthesizer", "naive"]},
        {"name": "tacos", "args": ["--synthesizer", "tacos"]},
        {"name": "greedy_tacos", "args": ["--synthesizer", "greedy_tacos"]},
        {"name": "multiple_tacos", "args": ["--synthesizer", "multiple_tacos", "--num_beams", "5"]},
        {"name": "beam", "args": ["--synthesizer", "beam", "--num_beams", "5"]},
        {"name": "ilp", "args": ["--synthesizer", "ilp"]},
    ]


    with open(synthesis_times_csv, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(params_list)
        print(sorted(os.listdir(input_dir)))
        print("input_dir: ", input_dir)
        for filename in sorted(os.listdir(input_dir)):
            if not filename.endswith(".csv") or filename == "synthesis_results.csv" or filename == "collective_results.csv":
                continue

            filepath = os.path.join(input_dir, filename)
            print("file path is"    , filepath)
            file_params = get_file_parameters(filepath)

            for algo in algorithms:
                algo_name = algo["name"]
                algo_args = algo["args"]

                command = [
                    "python",
                    "-m",
                    "runner.synthesize",
                    "--topology",
                    filepath,
                    "--collective",
                    "all_gather",
                ] + algo_args
                print(f"  Running '{algo_name}'")
                stdout, stderr = run_command(command)

                if stdout is None:
                    print(
                        f"    Failed to execute '{algo_name}' on '{filename}'. Skipping.\n"
                    )
                    continue

                synthesis_time = extract_synthesis_time(stdout)
                if synthesis_time is not None:
                    row = []
                    for key in file_params:
                        row.append(file_params[key])
                    row.append(algo_name)
                    row.append(synthesis_time)
                    csvwriter.writerow(row)
                    print(
                        f"    Extracted Synthesis Time for '{algo_name}': {synthesis_time} s\n"
                    )
                else:
                    print(
                        f"    Synthesis time not found in output for '{algo_name}' on '{filename}'.\n"
                    )

    print("All commands executed and results recorded.\n")


def get_used_args(args):
    return {arg: value for arg, value in vars(args).items() if value is not None}


def main(params: Dict[str, List[Any]]) -> None:
    """
    Main function to generate CSV files and process them with tacos.sh commands.
    """
    directory = os.path.join("csvs", f"{params['topology']}")
    for key, value in params.items():
        if key != "topology":
            directory += f"_{key}{value}"
    output_csv = os.path.join(directory, "synthesis_times.csv")
    create_csv_files(directory, params)
    # run_tacos_commands(directory, f"ring_results_g{group_sizes}_b{bad_bandwidth_proportions}_m{bad_magnitudes}.csv")
    run_synthesis_commands(list(params.keys()), directory, output_csv)
    print("Directory", directory)

    # directory = f"ringcsvs_g{gss}_b{bbps}_m{bms}"
    # create_csv_files(gss, bbps, bms, directory)
    # run_tacos_commands(directory, f"ring_results_g{gss}_b{bbps}_m{bms}.csv")


def parse_int_or_tuple(value):
    try:
        # Check if the value is a single integer
        return int(value)
    except ValueError:
        try:
            # Attempt to parse it as a tuple of integers
            value = value.strip("()")  # Remove surrounding parentheses
            return tuple(map(int, value.split(",")))
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"Invalid value: {value}. Must be an int or a tuple of ints (e.g., 3 or 1,2,3)"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "This script generates ring topology CSV files based on given group sizes and proportions "
            "of bad bandwidth nodes. It then executes the 'tacos.sh' script with various algorithms on "
            "each CSV file, extracts the synthesized collective time, and compiles the results into "
            "'ring_results.csv'."
        )
    )
    # Key for params: IMPT DO NOT INCLUDE _ (underscores) in param names
    # gs = group sizes
    # bm = bad magnitudes
    # bbp = bad bandwidth proportions
    # ls = layer sizes e.g. [1,4,16] means Layer 0 has 1 node, Layer 1 has 4 nodes,
    #       and Layer 2 has 16 nodes
    parser.add_argument(
        "--topology",
        type=str,
        default="ring",
        help="The topology to generate CSV files for (e.g., 'ring')",
    )
    parser.add_argument(
        "--world_size", type=int, nargs="+", help="The number of nodes in the topology"
    )
    parser.add_argument(
        "--bandwidth_ratio",
        type=parse_int_or_tuple,
        nargs="+",
        help="Ratio of best to worst bandwidth. Can be a single value (e.g. 50) or a tuple for hierarchical topologies (e.g. 50,10)",
    )
    parser.add_argument(
        "--slow_link_proportion",
        type=float,
        nargs="+",
        help="The proportions of bad bandwidth nodes (e.g., 0.1 0.2 0.3)",
    )
    parser.add_argument(
        "--layer_sizes",
        type=parse_int_or_tuple,
        nargs="+",
        help="The number of nodes in each layer (e.g., 1,4,8)",
    )
    # NOTE: can add more arguments in a similar format as above as needed

    args = parser.parse_args()
    used_args = get_used_args(args)
    main(used_args)
