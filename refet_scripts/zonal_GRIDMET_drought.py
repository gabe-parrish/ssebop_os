"""Zonal statistics using a shapefile and comparing distributions of Gridmet during drought
conditions within comparable areas.

e.g. Illinois (growing season, all pixels with NDVI > 0.7): For the complete time-series,
 and pixels meeting the criteria within an area of interest, what is the difference
  in distribution of ETo?

Take into account: Growing season will be different for different locations,
(southern AZ growning season is year-round), and if too wide a temporal
period is defined that may also not be good, maybe just 'peak growing season' May-August/June-August?.
"""

# todo: https://corteva.github.io/rioxarray/stable/examples/dask_read_write.html
# help: https://xarray-contrib.github.io/xarray-tutorial/scipy-tutorial/06_xarray_and_dask.html#Automatic-parallelization-with-apply_ufunc-and-map_blocks
import zarr
import progressbar
import dask
from datetime import datetime, date, timedelta
from dateutil import relativedelta
import os
import geopandas as gpd
from dask.diagnostics import ProgressBar
import pandas as pd
import rioxarray as rioxa
import xarray as xr
import rasterio as rio
from glob import glob
# Windows:
# import multiprocessing.popen_spawn_win32
import threading
from dask.distributed import Client, LocalCluster, Lock
from dask.utils import SerializableLock

# print(xr.show_versions())




# todo - get this shit working... import a timelist, set a time variable and concat.
# https://stackoverflow.com/questions/46899337/convert-raster-time-series-of-multiple-geotiff-images-to-netcdf

def get_chunksize(path, cog=False):

    # todo - if a COG, then...

    print('path \n', path)
    chonks = {}
    with rioxa.open_rasterio(path) as xras:
        print(xras.dims)
        chonks['x'] = len(xras.x)
        chonks['y'] = len(xras.y)
        chonks['band'] = 1
        print(len(xras.x))
        print(len(xras.y))
    return chonks

def get_date_from_file(fpath):
    fname = os.path.split(fpath)[-1]
    dstr = fname.split('.')[0]
    try:
        return datetime.strptime(dstr, '%Y%j')
    except:
        pass
    try:
        return datetime.strptime(dstr[3:], '%Y%j')
    except:
        raise

def read_rasters(files, test=False):
    """"""
    # sort the paths and create dates from them.
    if test:
        # only do 1000
        paths = sorted(files)[-7000:]
    else:
        paths = sorted(files)
    dates = [get_date_from_file(p) for p in paths]
    # print('the dates', dates)
    time = xr.Variable('time', pd.DatetimeIndex(dates))
    print('determining chunks')
    chunks = get_chunksize(path=paths[0], cog=False)
    print('opening')
    datasets = [rioxa.open_rasterio(f, chunks=chunks) for f in paths]
    return xr.concat(datasets, dim=time)

def read_shapes(files, dim):
    """"""
    # Todo - reads in a group of geopandas shapefiles and concatenates them into a data_array object.
    #  xr.DataArray.from_series(s)
    #   http://xarray.pydata.org/en/stable/user-guide/pandas.html
    pass

# here we suppose we only care about the combined mean of each file;
# you might also use indexing operations like .sel to subset datasets

path_to_ndvi = r'Z:\Data\NDVI\USA\V006_250m'
# ndvi_glob = r'Z:\Data\NDVI\USA\V006_250m\**\*250_m_16_days_NDVI.tif'
# ndvi_files = glob(ndvi_glob, recursive=True)
# print('files', ndvi_files)
# ndvi_dset = read_rasters(ndvi_files, dim='time', parallel=True, transform_func=None)
# print('done reading in NDVI')
# print(ndvi_dset)
# print('writing to file')
# delated_obj = ndvi_dset.to_zarr(path=r'Z:\Data\NDVI\USA\V006_250m.zarr', compute=False)
# with ProgressBar():
#     results = delated_obj.compute()

path_to_gridmet = r'Z:\Data\ReferenceET\USA\Gridmet\Daily\ETo'
gridmet_glob = r'Z:\Data\ReferenceET\USA\Gridmet\Daily\ETo\**\eto*.tif'
gridmet_files = glob(gridmet_glob, recursive=True)
gridmet_dset = read_rasters(gridmet_files, test=True)
print('done reading in ETo')
print(gridmet_dset)
print('writing to file')
delayed_obj = gridmet_dset.to_netcdf(path=r'Z:\Data\ReferenceET\USA\Gridmet\Daily\gm_eto.nc', compute=False)
with ProgressBar():
    results = delayed_obj.compute()
#
# #### geopandas timeseries.
# drought_path = r'Z:\Users\Gabe\refET\Drought\full_ts'
# drought_glob = r'Z:\Users\Gabe\refET\Drought\full_ts\**\*.shp'
# gridmet_files = r'gridmet'
# # todo - fully develope read_shapes into something useful.
# print('done reading in Shapefiles')


if __name__ == "__main__":
    growing_season = (6, 8)
    ndvi_thresh = 0.7

    # start_date = datetime(year=)




#### ============================

# def read_rasters(files, dim, parallel=False, transform_func=None):
#
#     # todo - do we need to pass a date coordinate?
#     #  Is the best way to do that to pass a list of the dates along with 'files'?
#     def process_one_path(path):
#         # use a context manager, to ensure the file gets closed after use
#         with rioxa.open_rasterio(path) as ds:
#
#             # transform_func should do some sort of selection or
#             # aggregation
#             if transform_func is not None:
#                 ds = transform_func(ds)
#
#             # load all data from the transformed dataset, to ensure we can
#             # use it after closing each original file
#             ds.load()
#             return ds
#
#     paths = sorted(files)
#     print(f'len ofhs {len(paths)} \n {paths}')
#     # todo - set a datetime coordinate
#     # todo - trying to emulate what open_mfdataset does pat
#     open_kwargs = dict(decode_cf=True, decode_times=False)
#     # 'Reading and Writing Files' on xarray documentation page, under 'User Guide'.
#     if not parallel:
#         datasets = [process_one_path(p) for p in paths]
#         combined = xr.concat(datasets, dim)
#     elif parallel:
#         print('paralelizing')
#         open_kwargs = dict(decode_cf=True, decode_times=False)
#         open_task_lst = [dask.delayed(rioxa.open_rasterio)(f) for f in files]
#         for ot in open_task_lst:
#             print('type: ', type(ot))
#             print('the ot\n', ot, '\n====')
#         # if transform_func is not None:
#         #     tasks = [dask.delayed(transform_func)(task) for task in open_task_lst]
#         #     datasets = dask.compute(tasks)  # get a list of xarray.Datasets
#         # else:
#         #     datasets = dask.compute(open_task_lst)
#         # combined = xr.combine_nested(datasets)  # or some combination of concat, merge
#         datasets = dask.compute(open_task_lst)
#         print(type(datasets))
#         print('datasets\n', datasets[0])
#         print('=====')
#         print(type(datasets[0]))
#         combined = xr.combine_nested(datasets, dim)  # or some combination of concat, merge
#     return combined
#
#
# def read_shapes(files, dim):
#     """"""
#     # Todo - reads in a group of geopandas shapefiles and concatenates them into a data_array object.
#     #  xr.DataArray.from_series(s)
#     #   http://xarray.pydata.org/en/stable/user-guide/pandas.html
#     pass
#
# # here we suppose we only care about the combined mean of each file;
# # you might also use indexing operations like .sel to subset datasets
#
#
# path_to_ndvi = r'Z:\Data\NDVI\USA\V006_250m'
# ndvi_glob = r'Z:\Data\NDVI\USA\V006_250m\**\*250_m_16_days_NDVI.tif'
# ndvi_files = glob(ndvi_glob, recursive=True)
# # just the last 20 for testing.
# ndvi_files = sorted(ndvi_files)[-3:]
# ndvi_dset = read_rasters(ndvi_files, dim='time', parallel=True, transform_func=None)
# # todo - write to a netcdf!
# #   delete the dataset to save memory
# print('done reading in NDVI')
# # path_to_gridmet = r'Z:\Data\ReferenceET\USA\Gridmet\Daily\ETo'
# # gridmet_glob = r'Z:\Data\ReferenceET\USA\Gridmet\Daily\ETo\**\eto*.tif'
# # gridmet_files = glob(gridmet_glob, recursive=True)
# # gridmet_dset = read_rasters(gridmet_files, dim='time',
# #                          transform_func=None)
# # print('done reading in ETo')
# # #### geopandas timeseries.
# # drought_path = r'Z:\Users\Gabe\refET\Drought\full_ts'
# # drought_glob = r'Z:\Users\Gabe\refET\Drought\full_ts\**\*.shp'
# # gridmet_files = r'gridmet'
# # # todo - fully develope read_shapes into something useful.
# # print('done reading in Shapefiles')
#
#
# if __name__ == "__main__":
#     growing_season = (6, 8)
#     ndvi_thresh = 0.7
#
#     # start_date = datetime(year=)