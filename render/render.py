import numpy as np
from helpers import data2numpy, clip_perc, plot_image, border_detector, blur, crop_depth, render_cineloop
from input import load_input
import os
import argparse

def crop(frame, meters, d2, d3, output_filename):
    if meters > 0:
        cropped = crop_depth(frame, meters, d2)
        plot_image(cropped, img_name=f'{output_filename}_crop', d2=d2, d3=d3)


def input_args():
    parser = argparse.ArgumentParser(description='Renders Awave3D\'s outputs.')
    parser.add_argument('-i', '--input', help='The JSON file received as input.', required=True)
    return parser.parse_args()


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
            render_cineloop(seismic, entry.d2, entry.d3)
            return

        # Cleanup old results and create a folder
        out_dir = entry.output
        out_dir = f'.{os.path.sep}out{os.path.sep}{out_dir}{os.path.sep}'
        os.makedirs(out_dir, exist_ok=True)
        output_filename = out_dir + entry.output

        frame = seismic[entry['frame'], :, :,].T.copy()

        if entry.get('perc'):
            perc = entry['perc']
            frame = clip_perc(frame, perc)
            output_filename += f'_perc-{perc}'
            plot_image(frame, img_name=output_filename, d2=d2, d3=d3)
            crop(frame, entry.get('crop_meters', 0), d2, d3, output_filename)
        else:
            crop(frame, entry.get('crop_meters', 0), d2, d3, output_filename)

        # Normalize the array between 0 and 1
        min_val = np.min(frame)
        max_val = np.max(frame)
        frame = (frame - min_val) / (max_val - min_val)

        if entry.get('blur'):
            frame = blur(frame)
            output_filename += '_blur'
            plot_image(frame, img_name=output_filename, d2=d2, d3=d3)
            crop(frame, entry.get('crop_meters', 0), d2, d3, output_filename)

        if entry.get('border'):
            frame = border_detector(frame)
            output_filename += '_border'
            plot_image(frame, img_name=output_filename,  d2=d2, d3=d3)
            crop(frame, entry.get('crop_meters', 0), d2, d3, output_filename)

        if entry.get('threshold'):
            frame = np.where(frame > entry['threshold'], 1, 0)
            output_filename += '_threshold'
            plot_image(frame, img_name=output_filename, d2=d2, d3=d3)
            crop(frame, entry.get('crop_meters', 0), d2, d3, output_filename)

        if entry.get('negative'):
            frame = frame * -1
            output_filename += '_negative'
            plot_image(frame, img_name=output_filename)
            crop(frame, entry.get('crop_meters', 0), d2, d3, output_filename)

        plot_image(frame, img_name=output_filename, d2=d2, d3=d3)
        crop(frame, entry.get('crop_meters', 0), d2, d3, output_filename)


if __name__ == '__main__':
    main()
