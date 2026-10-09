# SeisUtils

A collection of utilities for seismic data processing, visualization, and analysis. This repository provides various tools for working with seismic data files, velocity models, and integrates with SeisUnix.

## Repository Overview

SeisUtils consists of several modules for different seismic processing tasks:

### 2d23d
Tool for converting 2D seismic models to 3D models.

- **Main Features:**
  - Converts 2D model header files to 3D
  - Handles binary velocity files
  - Creates smoothed versions of the 3D model
  - Automatically generates parameter files for modeling and migration

```bash
python -m 2d23d.2d23d -f input_file.hdr -y y_dimension -o output_file
```

### log_analyzer
Not a generic tool at all! It was written to be a useful for the context of my research, but it can bring good insights for future researchers interested in automate their nsight and logs data extraction.


### addwater
Tool for adding a water layer to the top of a velocity model.

- **Main Features:**
  - Adds a water layer with specified velocity to seismic velocity models
  - Preserves original data dimensions
  - Configurable water layer thickness

```bash
python -m addwater.addwater --n1 n1_dim --n2 n2_dim --n3 n3_dim --water water_thickness --input input_file.bin --out output_file.bin
```

### bin
Contains binary executables for various seismic processing tasks:
- `binary` - Generic binary file handler
- `header` - Header file processor
- `seg2segy` - Converts SEG-2 format to SEG-Y
- `segbread` - Reads SEG-B format
- `segdread` - Reads SEG-D format
- `segyclean` - Cleans SEG-Y files
- `segyhdrmod` - Modifies SEG-Y headers
- `segyhdrs` - Extracts SEG-Y headers
- `segyread` - Reads SEG-Y files
- `segyscan` - Scans SEG-Y files
- `segywrite` - Writes SEG-Y files
- `smooth3d` - Applies 3D smoothing
- `surange` - Analyzes SU file ranges

### geometry
Tool for visualizing and verifying seismic acquisition geometries.

- **Main Features:**
  - Plots acquisition geometry from parameter files
  - Visualizes source and receiver positions
  - Creates top-down views of the acquisition setup
  - Generates animations of shot progressions

**Requirements:**
```bash
pip install -r geometry/requirements.txt
```

**Usage:**
```bash
python -m geometry.geometry --par parfile.par --vel velocity.bin --hdr header.hdr --out output_directory
```

### render
Visualization tools for Awave3D outputs.

- **Main Features:**
  - Renders seismic data from binary files
  - Applies various image processing operations (cropping, thresholding, etc.)
  - Creates cineloops for visualization
  - JSON-based configuration for rendering settings

**Requirements:** `numpy`, `matplotlib`, and `opencv-python-headless` for `border`/`blur`.

**Usage** (run from the folder where `out/` should be created; `MPLBACKEND=Agg` on machines without a display):
```bash
MPLBACKEND=Agg python render/render.py -i render/inputs/sample.json
```

The input is a JSON list; each entry renders the depth section at `i3 = frame` of a float32
volume with `n1 x n2 x n3` values (`n1` = depth, fastest axis). Main keys: `filepath`, `n1`,
`n2`, `n3`, `d1` (depth spacing; defaults to `d3`), `d2`, `frame`, `perc` (symmetric clip at
this percentile), `crop_meters`, `border`, `blur`, `threshold`, `negative`, `output` (defaults
to the file name), `dpi` (200), `formats` (`["png"]`), `cineloop` (interactive only), `ignore`.
Each processing step writes `out/<output>/<output>_frame-<f>_<steps>.<fmt>`.

`render/error_map.py -i <json>` renders the absolute difference |a - b| of the same section of
two volumes (e.g. a compressed run against the uncompressed baseline), plus `log(1 + |a - b|)`.
Entries take `filepath_a`, `filepath_b`, `n1`, `n2`, `n3`, `d1`/`d2`/`d3`, `frame`,
`crop_meters`, `output`, `dpi`, `formats`, `ignore`, `log` (default true) and `vmax`: give the
same `vmax` to several entries to plot them on a common colour scale. It also prints the max and
mean |a - b|. Example: `render/inputs/errormap_sample.json`.

### sections
Cuts 2D sections of Awave3D volumes (migrated images `.data`, velocity `.bin`) into small raw
files, so they can be viewed interactively on another machine (e.g. a laptop with SeisUnix)
without copying the whole volumes.

- **Main Features:**
  - Sections at fixed `i3` and/or `i2` (`--i3`, `--i2`, repeatable), written as float32 traces of
    `n1` samples, readable by SeisUnix `ximage`/`xwigb` with `n1=<n1>` (no SU headers)
  - Difference sections against a reference run (`--reference`)
  - Extra volumes with their own colour scale and no difference, e.g. the velocity (`--aux`)
  - Writes `show_sections.sh` (one `ximage` per section; runs share one clip, differences
    another) and `manifest.txt`

**Requirements:** `numpy`.

**Usage:**
```bash
python sections/extract_sections.py --shape 500 500 500 --spacing 20 20 20 --i3 250 --i2 250 \
    --reference baseline --outdir out_sections \
    baseline=baseline.data bitcomp=bitcomp.data --aux velocity=vel_smooth.bin
# copy out_sections/ to the viewing machine, then:
sh out_sections/show_sections.sh
```

### segy2su
Utility to convert SEG-Y files to SU (Seismic Unix) format.

```bash
python -m segy2su.segy2su
```

### smooth3d
Tool for applying 3D smoothing to velocity models.

- **Main Features:**
  - Uses SeisUnix's smooth3d utility via Singularity container
  - Configurable smoothing radius
  - Command-line interface for easy integration

```bash
python -m smooth3d.smooth3d --n1 n1_dim --n2 n2_dim --n3 n3_dim --input input.bin --output output_smooth.bin -r 20
```

### su2bin
Utility to extract binary data from SU files.

```bash
python -m su2bin.su2bin
```

### SeisUnixDocker
Docker container for SeisUnix with graphical interface via Remote Desktop.

- **Main Features:**
  - Complete SeisUnix installation in a Docker container
  - Remote Desktop (RDP) access for GUI applications
  - Volume mounting for data exchange with host
  - Cross-platform support (Windows, Linux, macOS)

**Usage:**
```bash
docker run -it --rm -p 3393:3389 -v ${PWD}:/home/ubuntu/data maltempi/seisunix:latest
```

Connect via RDP to `localhost:3393` with username: `ubuntu` and password: `ubuntu`.

## Requirements

Each module may have specific requirements. General requirements include:

- Python 3.x
- NumPy
- Matplotlib
- Docker (for SeisUnixDocker)
- Singularity (for smooth3d)

## Contributing

Contributions are welcome! Please feel free to submit pull requests or create issues for bugs and feature requests.

## Cite

> Maltempi T, Rigo S, Pereira M, et al. Checkpointing fine-tuning for accelerating seismic applications in GPUs. The International Journal of High Performance Computing Applications. 2025;0(0). doi:10.1177/10943420251340794

```text
@article{gpuzip2,
    author = {Thiago Maltempi and Sandro Rigo and Marcio Pereira and Hervé Yviquel and Gustavo Leite and Orlando Lee and Jessé Costa and Guido Araujo},
    title ={Checkpointing fine-tuning for accelerating seismic applications in GPUs},
    journal = {The International Journal of High Performance Computing Applications},
    volume = {0},
    number = {0},
    pages = {15},
    year = {0},
    doi = {10.1177/10943420251340794},
    URL = {https://doi.org/10.1177/10943420251340794},
    eprint = {https://doi.org/10.1177/10943420251340794},
    abstract = { High-performance computing (HPC) systems are essential to handle computationally intensive tasks in fields such as physics, climate modeling, and seismic analysis. Reverse Time Migration (RTM), a widely used seismic imaging technique for oil reservoir exploration, exemplifies these challenges, requiring vast amounts of memory and extended computation times. RTM relies on checkpointing to store data during forward wave propagation for reuse in the backward phase. However, traditional checkpoint methods are constrained by costly host-GPU data transfers, which limits performance. GPUZIP v2.0 addresses these bottlenecks with several enhancements over its predecessor: (1) A GPU Checkpoint Cache with a least recently used (LRU) policy enables flexible checkpoint storage configurations and efficient prefetching; (2) A redesigned prefetch algorithm further increases cache hit ratios; and (3) The integration of three distinct checkpointing algorithms provides adaptability for diverse application profiles. These advancements allow fine-tuning of RTM and similar applications, significantly improving performance. The experimental results show that GPUZIP v2.0 achieves speedups of up to 5.12×, surpassing the 3.9× achieved by its previous version. GPUZIP v2.0 provides an effective solution for accelerating memory-intensive HPC applications by reducing data transfer overhead and offering customized checkpoint strategies. GPUZIP is publicly available via GitHub. }
}
```