import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import configparser
import datetime
import os
from PIL import Image
import math


class Parameters:
    '''Class to store and manage parameters from modeling par file.

    Attributes:
        NSHOTSX (int): Number of shots in the x direction.
        NSHOTSY (int): Number of shots in the y direction.
        O1_SHOT (float): Source depth.
        O2_SHOT (float): Source inline coordinate (x, horizontal).
        O3_SHOT (float): Source crossline coordinate (y, vertical).
        D2_SHOT (float): Increment in x direction between shots.
        D3_SHOT (float): Increment in y direction between shots.
        NREC_STREAMER (int): Number of receivers per streamer.
        N_STREAMERS (int): Number of cables/streamers.
        O1_REC (float): Receiver depth.
        O2_REC (float): Inline coordinate (X) of the first receiver relative to the source.
        O3_REC (float): Crossline coordinate (y) of the receiver relative to the source.
        D2_REC (float): Distance in the horizontal/inline coordinate of the receivers in modeling.
        D3_REC (float): Distance in the vertical/crossline coordinate between cables in modeling.

    Args:
        parfilepath (str): Path to the parameter configuration file.

    '''

    def __init__(self, parfilepath):
        '''Initialize Parameters object by reading and parsing the configuration file.

        Args:
            parfilepath (str): Path to the parameter configuration file.

        '''
        self.NSHOTSX = 0
        self.NSHOTSY = 0
        self.O1_SHOT = 0.0
        self.O2_SHOT = 0.0
        self.O3_SHOT = 0.0
        self.D2_SHOT = 0.0
        self.D3_SHOT = 0.0
        self.NREC_STREAMER = 0
        self.N_STREAMERS = 0
        self.O1_REC = 0.0
        self.O2_REC = 0.0
        self.O3_REC = 0.0
        self.D2_REC = 0.0
        self.D3_REC = 0.0

        if parfilepath:
            self.parse_from_file(parfilepath)

    def __str__(self):
        return str(vars(self))

    def parse_from_file(self, filepath):
        config = configparser.ConfigParser()
        config.read(filepath)
        modeling_section = config['MODELING']

        self.NSHOTSX = int(modeling_section['NSHOTSX'])
        self.NSHOTSY = int(modeling_section['NSHOTSY'])
        self.O1_SHOT = float(modeling_section['O1_SHOT'])
        self.O2_SHOT = float(modeling_section['O2_SHOT'])
        self.O3_SHOT = float(modeling_section['O3_SHOT'])
        self.D2_SHOT = float(modeling_section['D2_SHOT'])
        self.D3_SHOT = float(modeling_section['D3_SHOT'])

        self.NREC_STREAMER = int(modeling_section['NREC_STREAMER'])
        self.N_STREAMERS = int(modeling_section['N_STREAMERS'])
        self.O1_REC = float(modeling_section['O1_REC'])
        self.O2_REC = float(modeling_section['O2_REC'])
        self.O3_REC = float(modeling_section['O3_REC'])
        self.D2_REC = float(modeling_section['D2_REC'])
        self.D3_REC = float(modeling_section['D3_REC'])


class Header:
    '''Class to store and manage hdr file parameters

    Attributes:
        n1 (int): Number of samples in the first dimension.
        n2 (int): Number of samples in the second dimension.
        n3 (int): Number of samples in the third dimension.
        o1 (float): Origin value in the first dimension.
        o2 (float): Origin value in the second dimension.
        o3 (float): Origin value in the third dimension.
        d1 (float): Spacing between samples in the first dimension.
        d2 (float): Spacing between samples in the second dimension.
        d3 (float): Spacing between samples in the third dimension.
        vel_filepath (str): Path to the velocity file.

    Args:
        hdr_filepath (str): Path to the header file.
    '''

    def __init__(self, hdr_filepath):
        self.n1 = 0
        self.n2 = 0
        self.n3 = 0
        self.o1 = 0.0
        self.o2 = 0.0
        self.o3 = 0.0
        self.d1 = 0.0
        self.d2 = 0.0
        self.d3 = 0.0
        self.vel_filepath = ''

        if hdr_filepath:
            self.parse_from_file(hdr_filepath)

    def __str__(self):
        return str(vars(self))

    def parse_from_file(self, filepath):
        with open(filepath, 'r') as f:
            line = f.readline()
            values = line.strip().split()
            self.n1 = int(values[0])
            self.n2 = int(values[1])
            self.n3 = int(values[2])
            self.o1 = float(values[3])
            self.o2 = float(values[4])
            self.o3 = float(values[5])
            self.d1 = float(values[6])
            self.d2 = float(values[7])
            self.d3 = float(values[8])

            line = f.readline()
            self.vel_filepath = line.strip().split()[0]



# considering the worst case: the model's diagonal wave round trip at water speed
def calculate_propagation_time(hdr: Header, speed=1500):
    l2 = (hdr.n2 - 1) * hdr.d2 + hdr.o2 # x in m
    l3 = (hdr.n3 - 1) * hdr.d3 + hdr.o3 # y in m

    x1, y1 = (0, 0)
    x2, y2 = (l2, l3)

    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2) / 2

    print('distance', distance)

    return distance/speed
        

def load_velocity_field(vel_filepath: str, header: Header):
    with open(vel_filepath, mode='rb') as f:
        vel = np.fromfile(f, dtype=np.float32)
        vel = np.reshape(vel, [header.n3, header.n2, header.n1])
    return vel


def make_filepath(output_dir: str, file_prefix: str, vel_filename: str, ext: str = 'png'):
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    ds_name = os.path.splitext(os.path.basename(vel_filename))[0]
    return f'''{output_dir}/{file_prefix}.{ds_name}.{current_datetime}.{ext}'''


def plot_velocity_slice(vel: np.ndarray, par: Parameters, hdr: Header, output_dir: str, slice: int = 0):

    frames = []

    for shot in range(par.NSHOTSX):
        plt.imshow(vel[slice, :, :].T * -1, cmap=plt.cm.gray)

        border_rect = patches.Rectangle(
            (0, 0), vel.shape[1], vel.shape[2], linewidth=1, edgecolor='black', facecolor='none')
        plt.gca().add_patch(border_rect)

        shot_pos_x = par.O2_SHOT + (par.D2_SHOT * shot)
        plt.scatter(x=[shot_pos_x / hdr.d2],
                    y=[par.O1_SHOT / hdr.d1], c='r', s=40)

        rec_origin = shot_pos_x + par.O2_REC
        for rec in range(par.NREC_STREAMER):
            rec_pos = rec_origin + par.D2_REC * (rec + 1)
            if rec_pos < 0:
                break
            plt.scatter(x=[rec_pos / hdr.d2],
                        y=[par.O1_REC / hdr.d1], c='g', s=20)

        plt.title(f'Shot {shot}')

        # plt.savefig(make_filepath(
        #     output_dir, f'geometry_vel_slice_s{shot}', hdr.vel_filepath))

        fig = plt.gcf()
        fig.canvas.draw()

        frame = Image.frombytes(
            'RGB', fig.canvas.get_width_height(), fig.canvas.tostring_rgb())
        frames.append(frame)

        plt.clf()
        plt.close()

    path = make_filepath(output_dir, f'geometry_vel_slice',
                         hdr.vel_filepath, 'gif')
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   optimize=False, duration=500, loop=1)


def plot_top_down_view(par: Parameters, hdr: Header, output_dir: str):
    sources_y = []
    sources_x = []
    receivers_y = []
    receivers_x = []

    for shot_y in range(par.NSHOTSY):
        for shot_x in range(par.NSHOTSX):
            src_x = par.D2_SHOT * shot_x + par.O2_SHOT
            src_y = par.D3_SHOT * shot_y + par.O3_SHOT
            sources_x.append(src_x)
            sources_y.append(src_y)

            for rec in range(par.NREC_STREAMER):
                for streamer in range(par.N_STREAMERS):
                    origin_x = src_x + par.O2_REC
                    rec_x = origin_x + par.D2_REC * rec
                    origin_y = src_y + par.O3_REC
                    rec_y = origin_y + par.D3_REC * streamer
                    receivers_x.append(rec_x)
                    receivers_y.append(rec_y)

    fig, ax = plt.subplots()
    ax.scatter(receivers_x, receivers_y, s=1, color='blue', marker='o')
    ax.scatter(sources_x, sources_y, s=1, color='red', marker='*')

    ax.scatter(receivers_x[0], receivers_y[0], s=1, color='green', marker='o')
    ax.scatter(sources_x[0], sources_y[0], s=1, color='green', marker='*')

    l1 = (hdr.n1 - 1) * hdr.d1 + hdr.o1
    l2 = (hdr.n2 - 1) * hdr.d2 + hdr.o2
    l3 = (hdr.n3 - 1) * hdr.d3 + hdr.o3

    print('l1', l1, 'l2', l2, 'l3', l3)

    rect = patches.Rectangle((hdr.o2, hdr.o3), l2, l3,
                             linewidth=1, edgecolor='r', facecolor='none')
    ax.add_patch(rect)
    ax.set_aspect('equal', 'box')
    fig.tight_layout()

    plt.savefig(make_filepath(
        output_dir, 'geometry_topdown', hdr.vel_filepath))


def render_geometry(par_filepath: str, vel_filepath: str, hdr_filepath: str, output_folder: str = './', slice: int = 0):
    par = Parameters(par_filepath)
    hdr = Header(hdr_filepath)
    hdr.vel_filepath = vel_filepath

    vel = load_velocity_field(hdr.vel_filepath, hdr)
    plot_velocity_slice(vel, par, hdr, output_folder, slice)
    plot_top_down_view(par, hdr, output_folder)

    speed_mean = np.mean(vel)
    print('Recommended TIME_END:', calculate_propagation_time(hdr, speed_mean))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Renders geometry for the given par and hdr files.')
    parser.add_argument('--par', type=str, help='path to the *-mod.par file')
    parser.add_argument('--vel', type=str,
                        help='path to the velocity file (.bin)')
    parser.add_argument('--hdr', type=str, help='path to the hdr file')
    parser.add_argument('--out', type=str, default='./output',
                        help='output folder path')
    parser.add_argument('-c', action='store_true',
                        default=False, help='Cleanup --out dir before start')
    parser.add_argument('--slice', type=int, default=0,
                        help='output folder path')
    args = parser.parse_args()

    if args.c:
        import shutil
        shutil.rmtree(args.out)

    os.makedirs(args.out, exist_ok=True)

    render_geometry(par_filepath=args.par, vel_filepath=args.vel,
                    hdr_filepath=args.hdr, output_folder=args.out, slice=args.slice)
