import numpy as np
from helpers import data2numpy, plot_image, crop_depth, cropped_top
import argparse
import json
import os


DEFAULTS = {
    'd1': None,      # depth spacing; defaults to d3 (older inputs used d3 for depth)
    'd2': 1,
    'd3': 1,
    'frame': 0,
    'crop_meters': 0,
    'vmax': None,    # fixed colour scale (same scale across entries); default: max of the map
    'log': True,     # also write log(1 + |a - b|)
    'output': '',
    'ignore': False,
    'dpi': 200,
    'formats': ['png'],
}


def input_args():
    parser = argparse.ArgumentParser(
        description='Renders the absolute difference |a - b| between two Awave3D outputs.')
    parser.add_argument('-i', '--input', help='The JSON file received as input.', required=True)
    return parser.parse_args()


def load_entries(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
    entries = []
    for item in data:
        for key in ('n1', 'n2', 'n3', 'filepath_a', 'filepath_b'):
            if key not in item:
                raise ValueError(f'entry without "{key}": {item}')
        entry = {**DEFAULTS, **item}
        if entry['d1'] is None:
            entry['d1'] = entry['d3']
        entries.append(entry)
    return entries


def save(entry, frame, output_filename, **kwargs):
    opts = dict(d1=entry['d1'], d2=entry['d2'], save=True, dpi=entry['dpi'],
                formats=tuple(entry['formats']), colorbar=True, cmap='viridis', vmin=0)
    opts.update(kwargs)
    plot_image(frame, img_name=output_filename, **opts)
    if entry['crop_meters'] > 0:
        opts['top'] = cropped_top(entry['crop_meters'], entry['d1'])
        plot_image(crop_depth(frame, entry['crop_meters'], entry['d1']),
                   img_name=f'{output_filename}_crop', **opts)


def main():
    entries = load_entries(input_args().input)

    for entry in entries:
        name = entry['output'] or (
            os.path.splitext(os.path.basename(entry['filepath_a']))[0] + '_vs_' +
            os.path.splitext(os.path.basename(entry['filepath_b']))[0])
        if entry['ignore']:
            print('Ignoring', name)
            continue
        print('Rendering', name)

        seismic_a = data2numpy(entry['filepath_a'], entry['n1'], entry['n2'], entry['n3'])
        seismic_b = data2numpy(entry['filepath_b'], entry['n1'], entry['n2'], entry['n3'])

        # One folder per entry: ./out/<output>/
        out_dir = f'.{os.path.sep}out{os.path.sep}{name}{os.path.sep}'
        os.makedirs(out_dir, exist_ok=True)
        output_filename = out_dir + name + f'_frame-{entry["frame"]}'

        # Section at i3 = frame: rows = depth (n1), columns = n2
        frame_a = seismic_a[entry['frame'], :, :].T.astype(np.float64)
        frame_b = seismic_b[entry['frame'], :, :].T.astype(np.float64)

        diff = np.abs(frame_a - frame_b)
        amp = float(np.percentile(np.abs(frame_b), 99))
        print(f'  max |a - b| = {diff.max():.4e}, mean = {diff.mean():.4e}, '
              f'99th percentile of |b| = {amp:.4e}')

        vmax = entry['vmax'] if entry['vmax'] is not None else float(diff.max())
        save(entry, diff, f'{output_filename}_abs', vmax=vmax)

        if entry['log']:
            save(entry, np.log1p(diff), f'{output_filename}_log', vmax=float(np.log1p(vmax)))


if __name__ == '__main__':
    main()
