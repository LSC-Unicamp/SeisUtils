"""Turn Awave3D volumes (.data / .bin) into cineloop videos (MP4), without a display.

For each input volume it
  1. writes a render.py input JSON (`"cineloop": true`), so the interactive cineloop can
     still be opened later with `python render/render.py -i <json>`;
  2. renders the same cineloop as render.py (depth section at i3 = k, symmetric clip at a
     percentile, plot_image with d2/d1), one pass k = 0..n3-1, into an MP4;
  3. optionally saves a preview PNG with a few slices.

Dimensions come from, in this order: --n1/--n2/--n3, a header file (--hdr, Awave3D
`.hdr`: "n1 n2 n3 o1 o2 o3 d1 d2 d3"), or the file size when the volume is a cube.

Examples
  python render/cineloop_video.py results/baseline__1416/baseline.data --hdr large_smooth.hdr
  python render/cineloop_video.py results/*/*.data --n 500 --d 20 --preview 20 96 250 400
  python render/cineloop_video.py a.data --outdir renders --json-only

Requires numpy, matplotlib and ffmpeg on PATH (for the MP4).
"""
import argparse
import json
import os
import shutil
import sys
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import data2numpy, clip_perc, plot_image  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description='Render Awave3D volumes as cineloop MP4 videos.')
    p.add_argument('volumes', nargs='+', help='float32 volumes (.data, .bin)')
    p.add_argument('--hdr', help='Awave3D header (.hdr) with dimensions and spacings')
    p.add_argument('--n', type=int, help='n1 = n2 = n3 (cube)')
    p.add_argument('--n1', type=int); p.add_argument('--n2', type=int); p.add_argument('--n3', type=int)
    p.add_argument('--d', type=float, help='d1 = d2 = d3 (m)')
    p.add_argument('--d1', type=float); p.add_argument('--d2', type=float); p.add_argument('--d3', type=float)
    p.add_argument('--perc', type=float, default=99.5, help='clip percentile per slice (render.py: 99.5)')
    p.add_argument('--fps', type=int, default=20, help='frames per second (render.py: 50 ms = 20 fps)')
    p.add_argument('--step', type=int, default=1, help='use every N-th slice')
    p.add_argument('--dpi', type=int, default=100)
    p.add_argument('--outdir', help='output folder (default: <volume dir>/renders)')
    p.add_argument('--name', help='output name (single volume only; default: <parent dir>_<file stem>)')
    p.add_argument('--preview', type=int, nargs='*', help='slices for a preview PNG, e.g. 20 96 250 400')
    p.add_argument('--json-only', action='store_true', help='only write the render.py JSON')
    p.add_argument('--force', action='store_true', help='overwrite existing outputs')
    return p.parse_args()


def read_hdr(path):
    with open(path) as f:
        v = f.readline().split()
    n1, n2, n3 = (int(x) for x in v[:3])
    d1, d2, d3 = (float(x) for x in v[6:9])
    return dict(n1=n1, n2=n2, n3=n3, d1=d1, d2=d2, d3=d3)


def geometry(args, path):
    g = dict(n1=None, n2=None, n3=None, d1=None, d2=None, d3=None)
    if args.hdr:
        g.update(read_hdr(args.hdr))
    if args.n:
        g.update(n1=args.n, n2=args.n, n3=args.n)
    if args.d:
        g.update(d1=args.d, d2=args.d, d3=args.d)
    for k in g:
        if getattr(args, k) is not None:
            g[k] = getattr(args, k)
    nvals = os.path.getsize(path) // 4
    if None in (g['n1'], g['n2'], g['n3']):
        c = round(nvals ** (1 / 3))
        if c ** 3 != nvals:
            sys.exit(f'{path}: {nvals} values is not a cube; give --hdr or --n1/--n2/--n3')
        g.update(n1=c, n2=c, n3=c)
    if g['n1'] * g['n2'] * g['n3'] != nvals:
        sys.exit(f"{path}: size ({nvals} values) != n1*n2*n3 ({g['n1']}x{g['n2']}x{g['n3']})")
    for k in ('d1', 'd2', 'd3'):
        if g[k] is None:
            g[k] = 1.0
            print(f'  warning: {k} not given, using 1 (axes in samples/1000)')
    return g


def default_name(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    parent = os.path.basename(os.path.dirname(os.path.abspath(path)))
    return f'{parent}_{stem}' if parent else stem


def write_json(path, g, name, json_path):
    entry = dict(n1=g['n1'], n2=g['n2'], n3=g['n3'], d1=g['d1'], d2=g['d2'], d3=g['d3'],
                 filepath=os.path.relpath(os.path.abspath(path), os.path.dirname(os.path.abspath(json_path))),
                 output=name, cineloop=True)
    with open(json_path, 'w') as f:
        json.dump([entry], f, indent=1)
    print('  wrote', json_path, '(run from its folder: python <SeisUtils>/render/render.py -i',
          os.path.basename(json_path) + ')')


def section(vol, k, perc):
    return clip_perc(vol[k, :, :].T, perc)


def write_video(vol, g, name, mp4, args):
    from matplotlib.animation import FFMpegWriter
    fig = plt.figure(figsize=(6.4, 5.6))
    writer = FFMpegWriter(fps=args.fps, codec='libx264', extra_args=['-pix_fmt', 'yuv420p'])
    t0 = time.time()
    with writer.saving(fig, mp4, dpi=args.dpi):
        for k in range(0, vol.shape[0], args.step):
            plt.clf()
            plot_image(section(vol, k, args.perc), g['d2'], d1=g['d1'], ax=plt.gca())
            plt.title(f"{name}  —  i3 = {k}/{vol.shape[0]}  ({k * g['d3'] / 1000:.2f} km)")
            writer.grab_frame()
            if k % 100 == 0:
                print(f'    slice {k}/{vol.shape[0]} ({time.time() - t0:.0f} s)', flush=True)
    plt.close(fig)
    print('  wrote', mp4)


def write_preview(vol, g, name, png, slices, perc):
    slices = [k for k in slices if 0 <= k < vol.shape[0]]
    ncol = min(len(slices), 2) or 1
    nrow = -(-len(slices) // ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(6.4 * ncol, 5.6 * nrow), squeeze=False)
    for ax, k in zip(axes.flat, slices):
        plot_image(section(vol, k, perc), g['d2'], d1=g['d1'], ax=ax)
        ax.set_title(f"i3 = {k} ({k * g['d3'] / 1000:.2f} km)")
    for ax in list(axes.flat)[len(slices):]:
        ax.axis('off')
    fig.suptitle(name)
    fig.savefig(png, bbox_inches='tight', dpi=100)
    plt.close(fig)
    print('  wrote', png)


def main():
    args = parse_args()
    if args.name and len(args.volumes) > 1:
        sys.exit('--name only works with a single volume')
    if not args.json_only and shutil.which('ffmpeg') is None:
        sys.exit('ffmpeg not found on PATH (needed for the MP4); use --json-only or install ffmpeg')

    for path in args.volumes:
        print('Volume', path)
        g = geometry(args, path)
        name = args.name or default_name(path)
        outdir = args.outdir or os.path.join(os.path.dirname(os.path.abspath(path)), 'renders')
        os.makedirs(outdir, exist_ok=True)
        base = os.path.join(outdir, name)
        mp4 = base + '_cineloop.mp4'
        if os.path.exists(mp4) and not args.force and not args.json_only:
            print('  skipped (exists, use --force):', mp4)
            continue

        write_json(path, g, name, base + '_cineloop.json')
        if args.json_only:
            continue

        vol = data2numpy(path, g['n1'], g['n2'], g['n3'])
        if not np.isfinite(vol).all():
            print('  warning: volume has NaN/Inf values')
        write_video(vol, g, name, mp4, args)
        if args.preview:
            tag = '-'.join(str(k) for k in args.preview)
            write_preview(vol, g, name, f'{base}_preview_i3-{tag}.png', args.preview, args.perc)


if __name__ == '__main__':
    main()
