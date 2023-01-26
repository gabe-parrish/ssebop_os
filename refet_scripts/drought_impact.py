from glob import glob
import os

import numpy
import numpy as np

import rasterio

"""Get the growing season total ETo for each calendar year"""

# start of the growing season
gs_startmonth = 5
gs_startday = 1
# end of the growing season
gs_endmonth = 9
gs_endday = 30
# year interval
start_year = 2011
end_year = 2011

# study_year = 2012
monthly_raster_root = r'Z:\Data\ReferenceET\USA\Gridmet\Daily\DailyETo_sums\MonthlySums'
output_location = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\2012figs\CONUS_annual_GS_ETo'

# what are we doing here?
# - Getting an annual cumulative raster from 2011 (non drought year in IL) and comparing it to a
# cumulative annual raster from 2012 (very bad drought year in Illinois).

growseason_rasters = glob(os.path.join(monthly_raster_root, '*{:02d}.tif'.format(gsmo)), recursive=False)
# print('gsmo', gsmo)
# print('list', growseason_rasters)
# print('len ', len(growseason_rasters))

for i in growseason_rasters:
    print(i)

# purge years not within [2001, 2017] inclusive
interval = end_year - start_year
years = [start_year + i for i in range(interval+1)]
goodyears = []
for ras in growseason_rasters:
    for y in years:
        # print(type(ras))
        if str(y) in ras:
            goodyears.append(ras)

print('post filtering \n', sorted(goodyears))

# rasterio to numpy and get climo median along an axis.
for k, gy in enumerate(goodyears):
    if k == 0:
        with rasterio.open(gy, 'r') as src:
            ogmeta = src.meta
            ogband = src.read(1)

    else:
        with rasterio.open(gy, 'r') as src:
            band = src.read(1)
            ogband = np.dstack((ogband, band))

print(f'shape of stack for gsmo {gsmo}: {ogband.shape}')
monthly_climo = np.nanmedian(ogband, axis=2)
print('shape of monthly climo :', monthly_climo.shape)
# output climo median
outpath_climo = os.path.join(output_location, 'climos')
if not os.path.exists(outpath_climo):
    os.mkdir(outpath_climo)

with rasterio.open(os.path.join(outpath_climo, f'gridmet_climo_20012017_{gsmo:02}'), 'w', **ogmeta) as wfile:
    wfile.write_band(1, monthly_climo)

# create percent difference rasters...

# output maps of rasters and drought shapefiles to a path. Cartopy? Or do this in QGIS to keep it simple...