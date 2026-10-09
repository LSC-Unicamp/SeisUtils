import numpy as np
import matplotlib
from helpers import data2numpy, clip_perc, plot_image, border_detector, blur, crop_depth, render_cineloop
from input import load_input
import os
import argparse


def input_args():
    parser = argparse.ArgumentParser(description='Renders Awave3D\'s outputs.')
    parser.add_argument('-i', '--input', help='The JSON file received as input.', required=True)
    return parser.parse_args()


def save(entry, frame, output_filename):
    """Save the depth section, and its cropped version when crop_meters > 0."""
    opts = dict(d1=entry.d1, d2=entry.d2, save=True, dpi=entry.dpi, formats=entry.formats)
    plot_image(frame, img_name=output_filename, **opts)
    if entry.crop_meters > 0:
        plot_image(crop_depth(frame, entry.crop_meters, entry.d1),
                   img_name=f'{output_filename}_crop', **opts)


def main():
    input_file = input_args().input
    entries = load_input(input_file)

    for entry in entries:
        if entry.ignore:
            print('Ignoring', entry.filepath)
            continue
        else:
            print('Rendering', entry.filepath)

        seismic = data2numpy(
            entry.filepath, entry.n1, entry.n2, entry.n3)

        print(entry)
        if entry.cineloop:
            if matplotlib.get_backend().lower() == 'agg':
                print('  cineloop needs an interactive display; skipped (non-interactive backend)')
            else:
                render_cineloop(seismic, entry.d2, entry.d1)
            continue

        # One folder per entry: ./out/<output>/
        name = entry.output or os.path.splitext(os.path.basename(entry.filepath))[0]
        out_dir = f'.{os.path.sep}out{os.path.sep}{name}{os.path.sep}'
        os.makedirs(out_dir, exist_ok=True)
        output_filename = out_dir + name

        # Section at i3 = frame: rows = depth (n1), columns = n2
        frame = seismic[entry.frame, :, :,].T.copy()
        output_filename += f'_frame-{entry.frame}'

        if entry.perc:
            frame = clip_perc(frame, entry.perc)
            output_filename += f'_perc-{entry.perc}'
        save(entry, frame, output_filename)

        # Normalize the array between 0 and 1
        min_val = np.min(frame)
        max_val = np.max(frame)
        frame = (frame - min_val) / (max_val - min_val)

        if entry.blur:
            frame = blur(frame)
            output_filename += '_blur'
            save(entry, frame, output_filename)

        if entry.border:
            frame = border_detector(frame)
            output_filename += '_border'
            save(entry, frame, output_filename)

        if entry.threshold:
            frame = np.where(frame > entry.threshold, 1, 0)
            output_filename += '_threshold'
            save(entry, frame, output_filename)

        if entry.negative:
            frame = frame * -1
            output_filename += '_negative'
            save(entry, frame, output_filename)


if __name__ == '__main__':
    main()
