import os
import rasterio
import copy
from rasterio import features
from rasterio.vrt import WarpedVRT
from rasterio.mask import mask
import numpy as np
from dateutil import relativedelta
from rasterio.enums import Resampling
import matplotlib.pyplot as plt
import geopandas as gpd
from datetime import datetime as dt

def droughtpath_to_dt(drought_str):

    fname = os.path.split(drought_str)[-1]
    fdate_str = fname.split('_')[-1][0:8]
    fdate = dt.strptime(fdate_str, '%Y%m%d')
    return fdate

def return_droughtrange(dpaths):

    listlen = len(dpaths)

    dpl = []
    dtl = []

    for i in range(listlen):
        if i < listlen-1:
            dp = (dpaths[i], dpaths[i+1])
            datetup = (droughtpath_to_dt(dp[0]), droughtpath_to_dt(dp[1]))
            dpl.append(dp)
            dtl.append(datetup)

    return dpl, dtl

def return_drought_intersections(study_area, df_list):
    # returns a list of tuples of the intersections of the files

    aoi = gpd.read_file(study_area)
    print('=== aoi ===\n', aoi)

    # for storing the tuples.
    new_lst = []

    for df_tup in df_list:
        # unpack
        d1, d2 = df_tup
        # read the files in
        d1_gdf = gpd.read_file(d1)
        d2_gdf = gpd.read_file(d2)
        # clip the drought shapefiles with the aoi.
        # https://geopandas.org/gallery/plot_clip.html
        d1_int = gpd.clip(d1_gdf, aoi)
        d2_int = gpd.clip(d2_gdf, aoi)
        # append a tuple
        new_lst.append((d1_int, d2_int))

    return new_lst

def rasterize_gdf(gdf, temp_location,meta_obj, category='DM'):
    """
    Takes a geodataframe, writes it to a file using sample_raster and a numerical category defined,
     and reads it back as a numpy array for analysis.
     General pattern from here:
     https://gis.stackexchange.com/questions/151339/rasterize-a-shapefile-with-geopandas-or-fiona-python/349728
    :param gdf:
    :param temp_location:
    :param sample_raster:
    :param category:
    :return:
    """
    # todo - is writing it out
    with rasterio.open(temp_location, 'w+', **meta_obj) as wfile:
        w_arr = wfile.read(1)

        # https://rasterio.readthedocs.io/en/latest/api/rasterio.features.html
        shapes = [(geom, value) for geom, value in zip(gdf.geometry, gdf[category])]
        burned_img = features.rasterize(shapes=shapes, fill=float('NaN'), out=w_arr, transform=wfile.transform)
        wfile.write_band(1, burned_img)
        return burned_img

def generate_standard_vrt(rasterpath, meta):
    """
    returns a numpy array
    :param rasterpath:
    :param meta:
    :return:
    """

    rs = Resampling.nearest

    with rasterio.open(rasterpath) as src:
        # TODO - make the default configurable.
        #                 if src.crs == None:
        #                     src.crs = CRS.from_epsg(4326)
        # create the virtual raster based on the standard rasterio attributes from the sample tiff and shapefile feature.
        with WarpedVRT(src, resampling=rs,
                       crs=meta['crs'],
                       transform=meta['transform'],
                       height=meta['height'],
                       width=meta['width']) as vrt:
            data = vrt.read()
            # # if I watnted to write the thing....
            # outwarp = os.path.join(temp_path, 'temp_warp.tif')
            # rio_shutil.copy(vrt, outwarp, driver='GTiff')
            return data
    #
    # # output each virtual file as a temporary .tif file in a temp folder somewhere in the outputs directory.
    # # for each file in the temp directory read in the raster as a numpy array and return the list of numpy arrays
    # # from this method for us in the rest of the code.
    # for ow in outputs:
    #     with rasterio.open(ow, 'r') as src:
    #         arr = src.read(1)
    #         npy_outputs.append(arr)

    pass

def get_std_transform(shapefile, sample_raster):

    shp = gpd.read_file(shapefile)

    print('shp geometry \n')
    print(shp.geometry)

    with rasterio.open(sample_raster) as rfile:
        out_img, out_transform = mask(dataset=rfile, shapes=shp.geometry, crop=True)
        meta = rfile.meta

        meta.update({'driver': 'GTiff',
                     "height": out_img.shape[1],
                     "width": out_img.shape[2],
                     "transform": out_transform})
    return meta

def get_gridmets_by_dt(root, dt_tuple, format=None):
    """
    Return a list of gridmet images comprising of a datetime interval.
    :param root:
    :param dt_tuple:
    :param format:
    :return:
    """

    gmpaths = []
    dates = []
    # start and end date
    sdate = dt_tuple[0]
    edate = dt_tuple[1]
    # interval timedelta object
    interval = edate - sdate
    for i in range(interval.days + 1):
        today = sdate + relativedelta.relativedelta(days=i)

        # construct a path to gridmet file based on the interval
        gmpath = os.path.join(root, f'{today.year}', 'eto{}{:03d}.tif'.format(today.year, today.timetuple().tm_yday))
        gmpaths.append(gmpath)
        dates.append(today)
    return gmpaths, dates

def find_ndvi_paths(root, dt_obj, fmat=None):
    """"""
    julian_day = dt_obj.timetuple().tm_yday

    def check_for_valid_file(ndvi_root, testday, string_format):
        jday = testday.timetuple().tm_yday
        check_ndvi_path = os.path.join(ndvi_root, f'{testday.year}',
                                      string_format.format(testday.year, jday))
        if not os.path.exists(check_ndvi_path):
            return False, check_ndvi_path
        else:
            return True, check_ndvi_path

    if fmat is None:
        string_fmt = '{}{:03}.250_m_16_days_NDVI.tif'

    poss_ndvi_path = os.path.join(root, f'{dt_obj.year}',
                                  string_fmt.format(dt_obj.year, julian_day))
    if not os.path.exists(poss_ndvi_path):
        # todo - find the upper and lower time end...
        upper = False
        lower = False
        upper_checkday = copy.copy(dt_obj)
        lower_checkday = copy.copy(dt_obj)
        while not upper:
            upper_checkday += relativedelta.relativedelta(days=1)
            upper, upper_guess_path = check_for_valid_file(ndvi_root=root, testday=upper_checkday, string_format=string_fmt)
        while not lower:
            lower_checkday -= relativedelta.relativedelta(days=1)
            lower, lower_guess_path = check_for_valid_file(ndvi_root=root, testday=lower_checkday, string_format=string_fmt)

        return (lower_guess_path, upper_guess_path)
        # # for testing
        # return (f'{lower_checkday.year}-{lower_checkday.timetuple().tm_yday}', f'{upper_checkday.year}-{upper_checkday.timetuple().tm_yday}')
    else:
        # return the original ndvi array.
        # return(poss_ndvi_path, poss_ndvi_path)
        # for testing
        return(dt_obj, dt_obj)

# for the study area:
shape = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\preprocessing\state_boundaries\lil_il_aoi.shp'

# for testing
drought_files = ['USDM_20120703.shp', 'USDM_20120710.shp', 'USDM_20120717.shp',
                 'USDM_20120724.shp', 'USDM_20120731.shp']
drought_root = r'Z:\Users\Gabe\refET\Drought\full_ts'
# paths to the drought files
dpaths = [os.path.join(drought_root, i) for i in drought_files]

# a location for rasterizing drought files
temp_location = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\preprocessing\temp'
stack_sample_file = r'Z:\Data\NDVI\USA\V006_250m\2001\2001001.250_m_16_days_NDVI.tif'

stack_meta = get_std_transform(shapefile=shape, sample_raster=stack_sample_file)

# get the drought ranges
# return two lists of tuples, the first with the paths representing endmembers of a drought period. The second
drought_period_lst, drought_interval_lst = return_droughtrange(dpaths)
print('drought period list \n', drought_period_lst, '\n drought interval list \n', drought_interval_lst)
# get intersection of study area and droughts,
drought_aois = return_drought_intersections(study_area=shape, df_list=drought_period_lst)

# rasterize the droughts in the intersection to match NDVI resolution
for dtup, dt_tup in zip(drought_aois, drought_interval_lst):

    d_start_aoi = dtup[0]
    d_end_aoi = dtup[1]
    d1_aoi_arr = rasterize_gdf(gdf=d_start_aoi, temp_location=os.path.join(temp_location, 'temp.tif'),
                               meta_obj=stack_meta, category='DM')
    d2_aoi_arr = rasterize_gdf(gdf=d_end_aoi, temp_location=os.path.join(temp_location, 'temp.tif'),
                               meta_obj=stack_meta, category='DM')
    print('two shapes: ', d1_aoi_arr.shape, d2_aoi_arr.shape)
    # find areas that remain under drought conditions continuously between two images.
    # instantiate a null array
    c_drought_arr = np.zeros(d1_aoi_arr.shape)
    # if the pixel is a drought on either end of the drought period
    constantarr_bool = ((d1_aoi_arr >= 1) & (d2_aoi_arr >= 1))
    # set it to one
    # now you have a numpy mask of pixels under consistent drought
    c_drought_arr[constantarr_bool] = 1

    # get the gridmet image paths for the drought interval, put em together in a list
    gm_images, gm_dates = get_gridmets_by_dt(root=r'Z:\Data\ReferenceET\USA\Gridmet\Daily\ETo', dt_tuple=dt_tup, format=None)

    # for each gridmet image:
    for gm_img, gm_date in zip(gm_images, gm_dates):
        # virtual warp out the gridmet for the study area and resample to the ndvi resolution.
        gm_arr = generate_standard_vrt(rasterpath=gm_img, meta=stack_meta)
        # For each gridmet image, search for the matching NDVI image, or the two nearest ndvi images.
        print(f'GM date: {gm_date.year}-{gm_date.timetuple().tm_yday}')
        ndvi_tup = find_ndvi_paths(root=r'Z:\Data\NDVI\USA\V006_250m', dt_obj=gm_date, fmat=None)
        print('NDVI tuple: ', ndvi_tup)




