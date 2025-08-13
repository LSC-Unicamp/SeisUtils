# This won't be useful as it is, because it was developed to parse my own application logs
# but this can inspire yours data.
# Some methods, for example, parses nsight fieles

import squarify
import re
import pandas as pd
import os
import subprocess
import csv
import re
import pandas as pd
import matplotlib.pyplot as plt


_100MB = 1e8
_32GB = 32 * 1e9
_364GB = 364 * 1e9


def formatns(nanoseconds):
    total_seconds = nanoseconds / 1e9  # Convert nanoseconds to seconds
    return formatsec(total_seconds)


def formatsec(total_seconds):
    total_seconds = int(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"


def b2gb(bytes_value):
    return bytes_value / (1024**3)


def extract_integers(s):
    return [int(x) for x in re.findall(r"\b\d+\b", s)]


def cuda_ops(qdrep_file_path, common_data):
    print("---> qdrep_file_path", qdrep_file_path)
    subprocess.run(
        [
            "nsys",
            "stats",
            "-r",
            "gpumemsizesum",
            "-r",
            "gpusum",
            "-o",
            "output",
            qdrep_file_path,
        ],
        capture_output=True,
        text=True,
    )

    stats_dir = ""
    output_gpusum_filepath = os.path.join(stats_dir, "output_gpusum.csv")
    output_gpumemsizesum_filepath = os.path.join(stats_dir, "output_gpumemsizesum.csv")

    all_kernels_spenttime = 0.0
    d2h_spenttime = 0.0
    h2d_spenttime = 0.0
    compression_kernels_spenttime = 0.0
    decompression_kernels_spenttime = 0.0
    h2d_memsize_gb = 0.0
    d2h_memsize_gb = 0.0

    # Parse the CSV files and extract required values
    with open(output_gpusum_filepath, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Category"] == "CUDA_KERNEL":
                all_kernels_spenttime += float(row["Total Time (ns)"])
            elif (
                row["Operation"] == "[CUDA memcpy Device-to-Host]"
                or row["Operation"] == "[CUDA memcpy DtoH]"
            ):
                d2h_spenttime += float(row["Total Time (ns)"])
            elif (
                row["Operation"] == "[CUDA memcpy Host-to-Device]"
                or row["Operation"] == "[CUDA memcpy HtoD]"
            ):
                h2d_spenttime += float(row["Total Time (ns)"])

            if (
                "bitcomp::encoder_kernel" in row["Operation"]
                or "cuZFP::cudaEncode" in row["Operation"]
                or "SZp_compress_k" in row["Operation"]
            ):
                compression_kernels_spenttime += float(row["Total Time (ns)"])

            if (
                "bitcomp::decoder_kernel" in row["Operation"]
                or "cuZFP::cudaDecode" in row["Operation"]
                or "SZp_decompress_k" in row["Operation"]
            ):
                decompression_kernels_spenttime += float(row["Total Time (ns)"])

    with open(output_gpumemsizesum_filepath, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Operation"] == "[CUDA memcpy DtoH]":
                d2h_memsize_gb += float(row["Total (MB)"]) / 1024
            elif row["Operation"] == "[CUDA memcpy HtoD]":
                h2d_memsize_gb += float(row["Total (MB)"]) / 1024

    os.remove(output_gpumemsizesum_filepath)
    os.remove(output_gpusum_filepath)

    return {
        "process_id": common_data["process_id"],
        "profile": common_data["profile"],
        "ds": common_data["ds"],
        #'total_time': common_data['total_time'],
        "all_kernels_spenttime": formatns(all_kernels_spenttime),
        "d2h_spenttime": formatns(d2h_spenttime),
        "h2d_spenttime": formatns(h2d_spenttime),
        "compression_kernels_spenttime": formatns(compression_kernels_spenttime),
        "decompression_kernels_spenttime": formatns(decompression_kernels_spenttime),
        "h2d_memsize_gb": h2d_memsize_gb,
        "d2h_memsize_gb": d2h_memsize_gb,
    }


def memory_data(log_string):
    pattern = re.compile(
        r"\[MEM_TRACK\]\[(?P<mem>[^\]]+)\]\[DEVICE=(?P<device>\d+)\]\[(?P<label>[^\]]+)\] (?P<size>\d+(\.\d+)?) \((?P<unit>bytes|MB|GB)\)"
    )

    matches = pattern.finditer(log_string)
    result = []
    buff_mem = 0
    host_chkpt_pool_mem = 0

    for match in matches:
        mem = match.group("mem")

        if mem == "MEMGPU_MANAGED":
            mem = "GPU"

        device = int(match.group("device"))
        label = match.group("label")
        size = float(match.group("size"))
        unit = match.group("unit")

        if unit == "GB":
            size_bytes = size * 1e9
        elif unit == "MB":
            size_bytes = size * 1e6
        elif unit == "bytes":
            size_bytes = size
        else:
            raise Exception("Unknown unit = " + unit)

        if label == 'GPUZIP__CACHE':
            buff_mem = buff_mem + size_bytes
        elif label == 'GPUZIP__CHECKPOINT_POOL':
            host_chkpt_pool_mem = host_chkpt_pool_mem + size_bytes

        result.append(
            {
                "mem": mem,
                "device": device,
                "is_gpuzip": 1 if "GPUZIP" in label else 0,
                "label": f"{label} ({size} {unit})",
                "size_bytes": size_bytes,
            }
        )

    pattern = re.compile(r"Main Data (?P<size>\d+(\.\d+)?) \(GB\)")
    matches = pattern.finditer(log_string)
    for match in matches:
        size = float(match.group("size"))
        size_bytes = size * 1e9
        label = f"MainData ({size} GB)"

        result.append(
            {
                "mem": "HOST",
                "device": 0,
                "is_gpuzip": 0,
                "label": label,
                "size_bytes": size_bytes,
            }
        )

    return result, buff_mem, host_chkpt_pool_mem


def plot_mem_usage(df, filename):
    import matplotlib.pyplot as plt
    import numpy as np

    plt.clf()

    fig = plt.gcf()
    ax = fig.add_subplot()
    fig.set_size_inches(6, 3)
    plt.axis("off")

    labels = df["label"].tolist()
    sizes = df["size_bytes"].tolist()

    squarify.plot(
        sizes=sizes, ec="black", color=plt.cm.plasma(np.linspace(0, 1, len(labels)))
    )
    plt.legend(handles=ax.containers[0], labels=labels)
    plt.savefig(filename, bbox_inches="tight", format="png")


def threshold_memory_allocations(df, threshold, total_mem):
    small_allocations_df = df[df["size_bytes"] < threshold]
    small_allocations = small_allocations_df.sum()["size_bytes"]
    big_allocations_df = df[df["size_bytes"] >= threshold]
    total_allocated_mem = df.sum()["size_bytes"]
    free_mem = total_mem - total_allocated_mem
    return (
        big_allocations_df,
        small_allocations_df,
        small_allocations,
        total_allocated_mem,
        free_mem,
    )


def process_gpu_mem(df, output_dir, threshold=_100MB, total_gpumem=_32GB):
    gpus_logs_df = df[df["mem"] == "GPU"]
    devices = sorted(gpus_logs_df["device"].unique())
    for device in devices:
        gpu_logs_df = gpus_logs_df[df["device"] == device]
        big_df, small_df, small_alloc_size, total_alloc_size, free_mem = (
            threshold_memory_allocations(gpu_logs_df, threshold, total_gpumem)
        )

        df_to_plot = pd.concat(
            [
                big_df,
                pd.DataFrame(
                    [
                        {
                            "mem": "GPU",
                            "device": device,
                            "is_gpuzip": 0,
                            "label": f"OTHER ({str(round(small_alloc_size / 1e6, 2))} MB)",
                            "size_bytes": small_alloc_size,
                        },
                        {
                            "mem": "GPU",
                            "device": device,
                            "is_gpuzip": 0,
                            "label": f"FREE MEM ({str(round(free_mem / 1e9, 2))} GB)",
                            "size_bytes": free_mem,
                        },
                    ]
                ),
            ]
        )

        df_to_plot.to_csv(os.path.join(output_dir, f"gpu_mem_{device}.csv"))
        plot_mem_usage(df_to_plot, os.path.join(output_dir, f"gpu_mem_{device}.png"))


def process_host_mem(df, output_dir, threshold=_100MB, total_hostmem=_364GB):
    logs_df = df[df["mem"] == "HOST"]
    big_df, small_df, small_alloc_size, total_alloc_size, free_mem = (
        threshold_memory_allocations(logs_df, threshold, total_hostmem)
    )

    df_to_plot = pd.concat(
        [
            big_df,
            pd.DataFrame(
                [
                    {
                        "mem": "HOST",
                        "device": 0,
                        "is_gpuzip": 0,
                        "label": f"OTHER ({str(round(small_alloc_size / 1e6, 2))} MB)",
                        "size_bytes": small_alloc_size,
                    },
                    {
                        "mem": "HOST",
                        "device": 0,
                        "is_gpuzip": 0,
                        "label": f"FREE MEM ({str(round(free_mem / 1e9, 2))} GB)",
                        "size_bytes": free_mem,
                    },
                ]
            ),
        ]
    )

    df_to_plot = df_to_plot[df_to_plot["size_bytes"] > 0]
    df_to_plot.to_csv(os.path.join(output_dir, "host_mem.csv"))
    plot_mem_usage(df_to_plot, os.path.join(output_dir, "host_mem.png"))


def cr_metrics(log: str, out_dir: str):
    csv_path = os.path.join(out_dir, "cr.csv")
    with open(csv_path, "w", newline="") as outfile:
        writer = csv.writer(outfile)

        header = [
            "timestep",
            "is_prev",
            "uncompressed_size",
            "compressed_size",
            "ratio",
        ]
        writer.writerow(header)

        for line in log.splitlines():
            if line.startswith("[CR],"):
                row = line[len("[CR],") :].split(",")
                writer.writerow(row)

    return pd.read_csv(csv_path)["ratio"].mean()


def prefetch_metrics(log: str, common_data):
    buffer_misses = 0
    buffer_hits = 0
    prefetches = 0
    pav_len = 0
    buffer_size = 0
    max_field_len = 0
    chkpt_pool_size = 0

    for log_line in log.splitlines():
        # Extract GPUZIP PREFETCH REPORT Data
        match = re.search(r"Number of hits \(prefetch\+hits\): (?P<hits>\d+)", log_line)
        if match:
            buffer_hits += int(match.group("hits"))
        
        match = re.search(r"Number of unavoidable misses: (?P<misses>\d+)", log_line)
        if match:
            buffer_misses += int(match.group("misses"))
        
        match = re.search(r"Number of prefetched checkpoints: (?P<prefetches>\d+)", log_line)
        if match:
            prefetches += int(match.group("prefetches"))

        pattern = re.compile(r"PAV Len = (?P<pav_len>\d+)")
        match = pattern.search(log_line)
        if match:
            pav_len = match.group("pav_len")

        pattern = re.compile(r"GPU Buffer Size = (?P<buffer_size>\d+) positions")
        match = pattern.search(log_line)
        if match:
            buffer_size = match.group("buffer_size")

        pattern = re.compile(r"Checkpoint Pool Size: (?P<chkpt_pool_size>\d+)")
        match = pattern.search(log_line)
        if match:
            chkpt_pool_size = match.group("chkpt_pool_size")

        pattern = re.compile(r"Field max len: (?P<max_field_len>\d+) \(MB\)")
        match = pattern.search(log_line)
        if match:
            max_field_len = match.group("max_field_len")

    return {
        "process_id": common_data["process_id"],
        "profile": common_data["profile"],
        "ds": common_data["ds"],
        "cache_hits": buffer_hits,
        "prefetches": prefetches,
        "real_hits": buffer_hits - prefetches,
        "unavoidable_misses": buffer_misses,
        "potential_misses": buffer_misses + prefetches,
        "pav_len": pav_len,
        "buffer_size": buffer_size,
        "max_field_len": max_field_len,
        "chkpt_pool_size": chkpt_pool_size,
    }


result_dir = "./results"
output_dir = "./output"
os.makedirs(output_dir, exist_ok=True)

log_files = []
nsight_files = []
for result in os.listdir(result_dir):
    process_id = result.split("__")[-1]
    profile = result
    ds = result

    result_exp_dir = os.path.join(result_dir, result)
    for file in os.listdir(result_exp_dir):
        if file.startswith("decom-") and file.endswith(".txt"):
            log_files.append(
                {
                    "filepath": os.path.join(result_exp_dir, file),
                    "process_id": process_id,
                    "profile": profile,
                    "ds": ds,
                }
            )

        if file.endswith(".qdrep"):
            nsight_files.append(
                {
                    "filepath": os.path.join(result_exp_dir, file),
                    "process_id": process_id,
                    "profile": profile,
                    "ds": ds,
                }
            )


def MergeObj(dict_1, dict_2, dict_3={}):
    result = dict_1 | dict_2 | dict_3
    return result


def spent_time(log):
    # Extract the number from the specified line
    match = re.search(r"Spent time \(seconds\): (\d+)", log)
    if not match:
        return None

    seconds = int(match.group(1))

    # Convert seconds to hh:mm:ss format
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60

    return {
        "spent_time_s": seconds,
        "spent_time": f"{hours:02}:{minutes:02}:{remaining_seconds:02}",
    }

def count_snaps(log):
    # Extract the number from the specified line
    match = re.search(r"snapshots used: (\d+)", log)
    if not match:
        return 0

    return match.group(0)


cuda_ops_result = []
for nsight_file in nsight_files:
    print("processing", nsight_file["filepath"])
    cuda_ops_result.append(cuda_ops(nsight_file["filepath"], nsight_file))
pd.DataFrame(cuda_ops_result).to_csv(os.path.join(output_dir, "nsight_result.csv"))

prefetch_result = []
for log_file in log_files:
    print("processing", log_file["filepath"])
    with open(log_file["filepath"], "r") as f:
        log = f.read()

    exp_outputdir = os.path.join(os.path.dirname(log_file["filepath"]), "result")
    os.makedirs(exp_outputdir, exist_ok=True)
    mem, buff, pool  = memory_data(log)
    mem_df = pd.DataFrame(mem)
    mem_df.to_csv(os.path.join(exp_outputdir, "mem_details.csv"))
    process_gpu_mem(mem_df, exp_outputdir)
    process_host_mem(mem_df, exp_outputdir)

    cr = cr_metrics(log, exp_outputdir)

    _prefetch_metrics = prefetch_metrics(log, log_file)
    _spent_time_metrics = spent_time(log)
    _snaps = count_snaps(log)

    prefetch_result.append(MergeObj(_prefetch_metrics, _spent_time_metrics, {"cr": cr}))

    spent_time(log)


pd.DataFrame(prefetch_result).to_csv(os.path.join(output_dir, "prefetch_result.csv"))
