### This was created as quick test. Please, change variables
### in order to make this work for you.
### Created by Thiago Maltempi <maltempi@ic.unicamp.br> (2023)

import numpy as np

def extract_binary_data(file_path):
    # Read the .su file
    with open(file_path, 'rb') as file:
        # Skip the file header (3200 bytes)
        file.seek(3200)
        
        # Read the binary data
        binary_data = np.fromfile(file, dtype=np.float32)
        
    return binary_data

# Example usage
file_path = './2D/sigbee2b/sigsbee2b_nfs.su'
output_path = './sigsbee2b_3d.bin'

binary_data = extract_binary_data(file_path)
binary_data.tofile(output_path)