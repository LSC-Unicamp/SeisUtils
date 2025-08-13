import argparse
import sys
import numpy as np
import os
from smooth3d.smooth3d import smooth3d

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
bin_dir = os.path.join(script_dir, '..', 'bin')

print(script_path, script_dir, bin_dir)


if __name__ == "__main__":

    ap = argparse.ArgumentParser()

    ap.add_argument("-f", "--input_file", required=True,
                    help="Path to 2D model header file")
    ap.add_argument("-y", "--y_dimension", required=True,
                    help="Grid size to extend in y-dimension")
    ap.add_argument("-o", "--output_file", required=True,
                    help="Name of output file without extension")

    args = vars(ap.parse_args())
    inputFile = args["input_file"]
    n3 = int(args["y_dimension"])
    outputfile = args["output_file"]

    # loading grid data from header file:
    data = np.loadtxt(inputFile, dtype='float32', max_rows=1)
    n1 = int(data[0])
    n2 = int(data[1])
    o1 = data[2]
    o2 = data[3]
    d1 = data[4]
    d2 = data[5]
    o3 = o2
    d3 = d2

    binFile = inputFile.replace('.hdr', '')+'.bin'
    model2d = np.fromfile(binFile, dtype='float32')

    with open(outputfile+".bin", "wb") as outfile:
        for i in range(n3):
            model2d.tofile(outfile)

    speed_avg = np.mean(model2d)

    # Creating header file
    ref_stdout = sys.stdout
    with open(outputfile+".hdr", "w") as outfile:
        print(n1, n2, n3, o1, o2, o3, d1, d2, d3)
        sys.stdout = outfile
        print(n1, n2, n3, o1, o2, o3, d1, d2, d3)
        print(outputfile+".bin")
        sys.stdout = ref_stdout

    smooth3d(n1, n2, n3, f'{outputfile}.bin', f'{outputfile}_smooth.bin', 20)

    # Creating header file of smoothed model
    ref_stdout = sys.stdout
    with open(outputfile+"_smooth.hdr", "w") as outfile:
        sys.stdout = outfile
        print(n1, n2, n3, o1, o2, o3, d1, d2, d3)
        print(outputfile+"_smooth.bin")
        sys.stdout = ref_stdout

    # parameters to create parfile
    freq = 15.0  # d1 < min(v) / 4 * 2.5 * freq
    l2 = (n2-1)*d2 + o2
    l3 = (n3-1)*d3 + o3

    if d1 > 1500 / 4 * 2.5 * freq:
        print('oops, illegal freq')

    # the following paragraph describes the geometry of one shot:
    # Marmousi
    nrec_streamer = 241  # number of receiver in one streamer
    n_streamers = 20  # number of streamers
    o1_rec = 20.0  # receivers depth | profundidade dos receptores, no modelamento
    o2_rec = -100.0  # minimum offset |  coordenada inline inicial do primeiro receptor, em relação à fonte, no modelamento
    # coordenada inline inicial do primeiro receptor, em relação à fonte, no modelamento
    o3_rec = -1000.0
    d2_rec = -12.5  # -15.0 # distancia na coordenada horizontal/inline dos receptores, no modelamento
    d3_rec = 100.0  # distancia na coordenada vertical/crossline entre cabos no modelamento
    o1_shot = 20.0  # profundidade da fonte, no modelamento
    # coordenada inline/horizontal/x inicial da fonte no modelamento
    o2_shot = -((nrec_streamer+1)*d2_rec + o2_rec) + o2
    # coordenada crossline/vertical/y inicial da fonte no modelamento
    o3_shot = (n_streamers/2 + 1)*d3_rec + o3
    # 60  # increase this parameter to decrease number of shots in x | incremento na coordenada horizontal (x) da fonte, entre tiros,no modelamento
    d2_shot = 500.0
    # 60  # increase this parameter to decrease number of shots in y | incremento na coordenada vertical (y) da fonte, depois de uma sequencia de tiros inline
    d3_shot = 500.0

    print('o2', o2, 'o3', o3)
    print('o2_shot', o2_shot, 'o3_shot', o3_shot)

    nshots_x = int((l2-o2_shot)/d2_shot)
    nshots_y = int((l3-2*(o3_shot-o3))/d3_shot)
    nshots = nshots_x * nshots_y

    print('nshots=', nshots)

    print('minimum y', int(-(2*o3_rec/d3)+1))
    
    if nshots_y < 1:
        print(
            f"ERROR: input parameter y must be at least {int(-(2*o3_rec/d3)+1)}")
        exit()

    mod_par = f'''[FILES]
VELOCITY = {outputfile}.hdr
OUTPUT   = {outputfile}-mod.su

[SOURCE]
FREQ={freq}

[MODELING]
TIME_INI=0
TIME_END=3
DT=0.004

NSHOTSX={nshots_x}
NSHOTSY={nshots_y}

O1_SHOT={o1_shot}
O2_SHOT={o2_shot}
O3_SHOT={o3_shot}
D2_SHOT={d2_shot}
D3_SHOT={d3_shot}

NREC_STREAMER={nrec_streamer}
N_STREAMERS={n_streamers}
O1_REC={o1_rec}
O2_REC={o2_rec}
O3_REC={o3_rec}
D2_REC={d2_rec}
D3_REC={d3_rec}'''

    mig_par = f'''[FILES]
VELOCITY = {outputfile}_smooth.hdr
DATA     = {outputfile}-mod.su
OUTPUT   = {outputfile}-mig.data

[SOURCE]
FREQ={freq}

[MIGRATION]
INISHOT=1
ENDSHOT={nshots}
STPSHOT=1

X1BEG={d1}
X1END={(n1-2)*d1}
X2BEG={d2}
X2END={(n2-2)*d2}
X3BEG={d3}
X3END={(n3-2)*d3}'''

    # Creating parfile for modelling
    ref_stdout = sys.stdout
    with open(outputfile+"-mod.par", "w") as outfile:
        sys.stdout = outfile
        print(mod_par)
        sys.stdout = ref_stdout

    # Creating parfile for migration
    ref_stdout = sys.stdout
    with open(outputfile+"-mig.par", "w") as outfile:
        sys.stdout = outfile
        print(mig_par)
        sys.stdout = ref_stdout
