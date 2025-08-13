'''
Created by Thiago Maltempi <maltempi@ic.unicamp.br> (2023)
'''
import numpy as np


def addwater(n1, n2, n3, water, infile, outfile):
    # Read the input binary file into a NumPy array
    data = np.fromfile(infile, dtype=np.float32)
    data = data.reshape((n1, n2, n3), order='F')

    # Add rows of value 1500 to the n1 dimension
    new_n1 = n1 + water
    new_data = np.zeros((new_n1, n2, n3), dtype=np.float32)
    new_data[water:, :, :] = data
    new_data[:water, :, :] = 3000.0

    # Save the modified data to the output binary file
    new_data.T.tofile(outfile)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Add water to the top (n1) of a velocity file.')
    parser.add_argument('--n1', type=int, help='n1 dim')
    parser.add_argument('--n2', type=int, help='n2 dim')
    parser.add_argument('--n3', type=int, help='n3 dim')
    parser.add_argument('--water', type=int, default=100, help='How many pixels of water to add in n1 dim')
    parser.add_argument('--input', type=str, help='Input velocity file path (.bin file)')
    parser.add_argument('--out', type=str, default='./output_addedwater.bin', help='Where the result of this script will be saved')

    args = parser.parse_args()

    addwater(args.n1, args.n2, args.n3, args.water, args.input, args.out)
