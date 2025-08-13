# Created by Thiago Maltempi <maltempi@ic.unicamp.br> (2023)
# Dependencies: singularity

import os

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
bin_dir = os.path.join(script_dir, '..', 'bin')


def smooth3d(n1, n2, n3, inputfile, outputfile, r=20):
    if (not os.path.exists(f'{bin_dir}/seisunix_latest.sif')):
        print(f'No ubuntu image has found in {bin_dir}. Pulling it, this may take a few minutes...')
        os.system(
            f'''singularity pull {bin_dir}/seisunix_latest.sif docker://ubuntu:22.04'''
        )

    cmd = f'''singularity exec {bin_dir}/seisunix_latest.sif {bin_dir}/smooth3d < {inputfile} > {outputfile} n1={n1} n2={n2} n3={n3} r1={r} r2={r} r3={r}'''

    os.system(cmd)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Smooths a velocity file')
    parser.add_argument('--n1', type=int, help='n1 dim')
    parser.add_argument('--n2', type=int, help='n2 dim')
    parser.add_argument('--n3', type=int, help='n3 dim')
    parser.add_argument('--input', type=str,
                        help='Input velocity file path (.bin file)')
    parser.add_argument('--output', type=str,
                        default='./output_smooth.bin', help='Result filepath')
    parser.add_argument('-r', type=int, default=20, help='Smooth parameter')

    args = parser.parse_args()

    print('Starting smoothing...')
    smooth3d(args.n1, args.n2, args.n3, args.input, args.output, args.r)
    print('Smoothed!')
