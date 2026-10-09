#!/usr/bin/env python3
"""Extract 2D sections of awave3d volumes into small raw files for viewing elsewhere.

awave3d images (.data) and velocity models (.bin) are raw float32 volumes with
n1 x n2 x n3 values, n1 (depth) varying fastest. A section is written as raw float32
traces of n1 samples, which is what SeisUnix `ximage`/`xwigb` read (`n1=<n1>`):

  --i3 K : section at i3 = K, n2 traces  (rows = depth, columns = i2)
  --i2 K : section at i2 = K, n3 traces  (rows = depth, columns = i3)

With --reference NAME, also writes <run>-minus-<reference> difference sections.
--aux NAME=FILE volumes (e.g. the velocity model) are cut too, but get their own
colour scale and no difference section.
Writes show_sections.sh with one `ximage` command per section (the runs share one
clip, taken from the reference, so they are on the same grey scale) and a
manifest.txt.

Usage:
  extract_sections.py --shape 500 500 500 --spacing 20 20 20 --i3 250 --i2 250 \
      --reference baseline  baseline=/path/baseline.data  bitcomp=/path/bitcomp.data \
      --aux velocity=/path/vel_smooth.bin
"""
import argparse
import os

import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog=__doc__.split("\n", 1)[1])
    p.add_argument("runs", nargs="+", metavar="NAME=FILE", help="volumes to cut")
    p.add_argument("--shape", nargs=3, type=int, required=True, metavar=("N1", "N2", "N3"))
    p.add_argument("--spacing", nargs=3, type=float, default=(1, 1, 1), metavar=("D1", "D2", "D3"))
    p.add_argument("--i3", type=int, action="append", default=[], help="section at i3 (repeatable)")
    p.add_argument("--i2", type=int, action="append", default=[], help="section at i2 (repeatable)")
    p.add_argument("--reference", help="NAME of the run to subtract (difference sections)")
    p.add_argument("--aux", action="append", default=[], metavar="NAME=FILE",
                   help="extra volume with its own colour scale, no difference (repeatable)")
    p.add_argument("--perc", type=float, default=99.0, help="percentile of |reference| used as clip")
    p.add_argument("--outdir", default=".")
    args = p.parse_args()

    n1, n2, n3 = args.shape
    d1, d2, d3 = args.spacing
    runs = dict(r.split("=", 1) for r in args.runs)
    aux = dict(r.split("=", 1) for r in args.aux)
    if args.reference and args.reference not in runs:
        p.error(f"--reference {args.reference} is not one of {list(runs)}")
    if not args.i3 and not args.i2:
        p.error("give at least one --i3 or --i2")
    os.makedirs(args.outdir, exist_ok=True)

    def load(path):
        v = np.fromfile(path, dtype=np.float32)
        if v.size != n1 * n2 * n3:
            p.error(f"{path}: {v.size} values, expected {n1}x{n2}x{n3}")
        return v.reshape(n3, n2, n1)  # [i3, i2, i1], i1 = depth fastest

    vols = {name: load(path) for name, path in runs.items()}
    auxvols = {name: load(path) for name, path in aux.items()}

    # Sections as [trace, sample]: written in C order they are traces of n1 samples.
    cuts = [(f"i3-{k}", lambda v, k=k: v[k, :, :], d2, "i2") for k in args.i3] + \
           [(f"i2-{k}", lambda v, k=k: v[:, k, :], d3, "i3") for k in args.i2]

    lines, manifest = [], []
    for tag, cut, dx, xaxis in cuts:
        ref = cut(vols[args.reference]) if args.reference else None
        clip = float(np.percentile(np.abs(ref if ref is not None else cut(next(iter(vols.values())))),
                                   args.perc))
        diffs = {}
        for name, v in vols.items():
            sec = np.ascontiguousarray(cut(v))
            fn = f"{name}_{tag}.bin"
            sec.tofile(os.path.join(args.outdir, fn))
            manifest.append(f"{fn}  n1={n1} n2={sec.shape[0]}  min={sec.min():.4e} max={sec.max():.4e}")
            lines.append(f'ximage < {fn} n1={n1} d1={d1:g} d2={dx:g} clip={clip:.6g} '
                         f'label1="depth (m)" label2="{xaxis} (m)" title="{name} {tag}" &')
            if ref is not None and name != args.reference:
                diffs[name] = sec.astype(np.float64) - ref
        for name, v in auxvols.items():
            sec = np.ascontiguousarray(cut(v))
            fn = f"{name}_{tag}.bin"
            sec.tofile(os.path.join(args.outdir, fn))
            manifest.append(f"{fn}  n1={n1} n2={sec.shape[0]}  min={sec.min():.4e} max={sec.max():.4e}")
            lines.append(f'ximage < {fn} n1={n1} d1={d1:g} d2={dx:g} perc=100 legend=1 '
                         f'label1="depth (m)" label2="{xaxis} (m)" title="{name} {tag}" &')
        if diffs:
            dclip = max(float(np.abs(d).max()) for d in diffs.values())
            for name, d in diffs.items():
                fn = f"{name}-minus-{args.reference}_{tag}.bin"
                d.astype(np.float32).tofile(os.path.join(args.outdir, fn))
                manifest.append(f"{fn}  n1={n1} n2={d.shape[0]}  max|diff|={np.abs(d).max():.4e}")
                lines.append(f'ximage < {fn} n1={n1} d1={d1:g} d2={dx:g} clip={dclip:.6g} '
                             f'cmap=hsv2 legend=1 label1="depth (m)" label2="{xaxis} (m)" '
                             f'title="{name} - {args.reference} {tag}" &')

    with open(os.path.join(args.outdir, "show_sections.sh"), "w") as f:
        f.write("#!/bin/sh\n# Opens every section with SeisUnix ximage (needs X11: XQuartz on macOS).\n"
                "# Runs share one grey scale (clip); difference sections share another.\n"
                'cd "$(dirname "$0")"\n' + "\n".join(lines) + "\nwait\n")
    os.chmod(os.path.join(args.outdir, "show_sections.sh"), 0o755)
    with open(os.path.join(args.outdir, "manifest.txt"), "w") as f:
        f.write("\n".join(manifest) + "\n")
    print("\n".join(manifest))


if __name__ == "__main__":
    main()
