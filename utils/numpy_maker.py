import numpy as np
import os
from SEEBop_os.raster_utils import convert_raster_to_array

var_name = 'TMAX'
in_dir = os.path.join(r'C:\WaterSmart\Projects\CloudVegET\DATA\TEMP', var_name)
root_path = r'C:\WaterSmart\Projects\CloudVegET\DATA\numpy'
output_dir = os.path.join(root_path, var_name)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

walk_obj = os.walk(in_dir)
for path, subdir, files in walk_obj:
    for file in files:
        if file.endswith('.tif'):
            n_arr = convert_raster_to_array(input_raster_path=in_dir, raster=file)
            print(n_arr)
            print(n_arr.shape)
            n_arr[n_arr == -3.402823e+38] = np.nan
            header = file.split('.')[0] + '.' + file.split('.')[1]
            newfilename = "{}{}".format(header, "_gw.tif")
            np.save(os.path.join(output_dir, header + '.npy'), n_arr)


