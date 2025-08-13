import numpy as np
from helpers import data2numpy, clip_perc, plot_image, border_detector, blur, crop_depth, MergeObj
import os

large_addedwater = {
    'n1': 600,
    'n2': 500,
    'n3': 500,
    'd2': 20,
    'd3': 20,
    'frame': 250,
    'perc': 90,
    'border': True,
    'blur': False,
    'negative': True,
    'threshold': 0.1,
}

salt_addedwater = {
    'n1': 310,
    'n2': 676,
    'n3': 676,
    'd2': 20,
    'd3': 20,
    'crop_meters': 200,
    'frame': 300,
    'perc': 99,
    'border': True,
    'blur': False,
    'negative': True,
    'threshold': 0.1,
}

large = {
    'n1': 500,
    'n2': 500,
    'n3': 500,
    'd2': 20,
    'd3': 20,
    'frame': 250,
    'perc': 90,
    'border': True,
    'blur': False,
    'negative': True,
    'threshold': 0.1,
}

marmousi = {
    'n1': 351,
    'n2': 901,
    'n3': 301,
    'd2': 10,
    'd3': 10,
    'frame': 150,
    'perc': 99.5,
    'border': True,
    'blur': False,
    'negative': True,
    'threshold': 0.1,
    'crop_meters': 500
}

entries = [
    MergeObj(marmousi, {
        'filepath_a': './marmousi3d-mig.592693.data',
        'filepath_b': './marmousi3d-mig.592695.data',
        'output': 'marmousi_errormap',
        'ignore': False,
    }),
]


def crop(frame, meters, d2, d3, output_filename):
    if meters > 0:
        cropped = crop_depth(frame, meters, d2)
        plot_image(cropped, img_name=f'{output_filename}_crop', d2=d2, d3=d3)


if __name__ == '__main__':
    for entry in entries:
        if entry.get('ignore'):
            print('Ignoring', entry['output'])
            continue
        else:
            print('Rendering', entry['output'])

        seismic_a = data2numpy(
            entry['filepath_a'], entry['n1'], entry['n2'], entry['n3'])
        seismic_b = data2numpy(
            entry['filepath_b'], entry['n1'], entry['n2'], entry['n3'])

        d2 = entry.get('d2', 1)
        d3 = entry.get('d3', 1)

        # Cleanup old results and create a folder
        out_dir = entry['output']
        if not out_dir:
            raise Exception('Missing output parameter')

        out_dir = f'.{os.path.sep}out{os.path.sep}{out_dir}{os.path.sep}'
        os.makedirs(out_dir, exist_ok=True)
        output_filename = out_dir + entry['output']

        frame_a = seismic_a[entry['frame'], :, :,].T.copy()
        frame_b = seismic_b[entry['frame'], :, :,].T.copy()

        diff = np.abs(frame_a - frame_b)

        # diff = np.where(diff > 0.1, 1, 0)

        plot_image(diff, d2=d2, d3=d3,
                   img_name=f'{output_filename}_abs', colorbar=True, cmap='viridis')
        
        diff_log = np.log1p(diff)
        plot_image(diff_log, d2=d2, d3=d3,
                   img_name=f'{output_filename}_log', colorbar=True, cmap='viridis')
