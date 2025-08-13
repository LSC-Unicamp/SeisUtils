### This was created as quick test. Please, change variables
### in order to make this work for you.
### Created by Thiago Maltempi <maltempi@ic.unicamp.br> (2023)

import os

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
_3d_dir = os.path.join(script_dir, '3D')

output_file = os.path.join(_3d_dir, './3D/c345/c345.su')
segy_dir = os.path.join(_3d_dir, './3D/c345/survey_origin/')

# Remove the output file if it already exists
if os.path.isfile(output_file):
    os.remove(output_file)

# Loop through all SEG-Y files in the directory
for segy_file in os.listdir(segy_dir):
    if segy_file.endswith('.sgy'):
        print('Converting', segy_file)
        su_command = f'''singularity exec ./ubuntu2204.sif ./segyread tape="{segy_dir}{segy_file}"  >> {output_file}'''
        os.system(su_command)

print("Conversion completed.")
