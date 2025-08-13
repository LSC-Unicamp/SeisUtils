import re
import os

result_dir = "build_debug/"
output_dir = "build_debug/output/"
output_file = f"{output_dir}nvtx.csv"

os.makedirs(output_dir, exist_ok=True)


def formatsec(total_seconds):
    total_seconds = int(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"


def formatns(nanoseconds):
    total_seconds = nanoseconds / 1e9  # Convert nanoseconds to seconds
    return formatsec(total_seconds)


import re
import csv
import os


def extract_ranges_from_log(log_file_path):
    # Define the ranges to extract and initialize with 0
    ranges = {
        "Advance": "",
        "BACKWARD": "",
        "Takeshot": "",
        "Restore": "",
        "GPUZIP_SETUP": "",
        "GPUZIP_PREFETCH_DISPATCH": "",
        "GPUZIP_FREE": "",
        "Compression": "",  # Includes Compressor-*
        "Decompression": "",  # Includes Decompressor-*
    }

    # Regex patterns
    base_pattern = r"^\s*\d+\.\d+\s+(\d+)\s+\d+\s+.*\s\s([A-Za-z0-9_\-]+.*)$"

    with open(log_file_path, "r") as log_file:
        for line in log_file:
            match = re.match(base_pattern, line)
            if match:
                total_time = int(match.group(1))
                range_name = match.group(2).strip()
                if (range_name):
                    print(range_name)
                if range_name in ranges:
                    ranges[range_name] = formatns(total_time)
                elif "bitcomp::encoder_kernel" in range_name or "cuZFP::cudaEncode" in range_name or "SZp_compress_k" in range_name:
                    ranges["Compression"] = formatns(total_time)
                elif "bitcomp::decoder_kernel" in range_name or "cuZFP::cudaDecode" in range_name or "SZp_decompress_k" in range_name:
                    ranges["Decompression"] = formatns(total_time)

    return ranges


def process_multiple_logs(log_files, output_csv):
    # CSV header
    header = [
        "File Name",
        "Advance",
        "BACKWARD",
        "Takeshot",
        "Restore",
        "GPUZIP_SETUP",
        "GPUZIP_PREFETCH_DISPATCH",
        "GPUZIP_FREE",
        "Compression",
        "Decompression",
    ]

    with open(output_csv, mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)

        for log_file, profile in log_files:
            if os.path.isfile(log_file):
                extracted_data = extract_ranges_from_log(log_file)
                # Prepare row: filename + extracted data values
                row = [profile] + [
                    extracted_data[key] for key in header[1:]
                ]
                writer.writerow(row)


files = []

for result in os.listdir(result_dir):
    process_id = result.split("__")[-1]
    profile = result
    ds = result
    result_exp_dir = os.path.join(result_dir, result)
    for file in os.listdir(result_exp_dir):
        if file.startswith("decom-") and file.endswith(".txt"):
            files.append((os.path.join(result_exp_dir, file), profile))

process_multiple_logs(files, output_file)
