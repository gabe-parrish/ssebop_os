import os
from matplotlib import pyplot as plt
import numpy as np
import rasterio as rio
from rasterio.plot import show

irr_areas_et = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\2012figs\annual_analysis\etdiff_2012_median_0115_lsIrrMaskedII.tif'

with rio.open(irr_areas_et, 'r') as src:

    arr = src.read(1)
    arr[arr == -9999] = np.nan

    # statistics for all the valid pixels (irrigated pixels)
    mean = np.nanmean(arr)
    median = np.nanmedian(arr)
    print(f'mean is {mean}, median is {median}')
    # how do i find the number of valid pixels?
    pixel_count = np.count_nonzero(~np.isnan(arr))

    print(f'valid pixel count {pixel_count}')