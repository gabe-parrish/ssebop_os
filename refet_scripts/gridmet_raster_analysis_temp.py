import os
import rasterio
import copy
from rasterio import features
from rasterio.vrt import WarpedVRT
from rasterio.mask import mask
import rasterio.windows as wndows
import numpy as np
from dateutil import relativedelta
from rasterio.enums import Resampling
import matplotlib.pyplot as plt
import geopandas as gpd
from datetime import datetime as dt
from glob import glob


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


def rasterize_gdf(gdf, temp_location, meta_obj, category='DM', windowsize=3):
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

    # meta_obj['dtype'] = 'int16'

    # is writing it out strictly necessary?
    with rasterio.open(temp_location, 'w+', **meta_obj) as wfile:
        w_arr = wfile.read(1)

        # https://rasterio.readthedocs.io/en/latest/api/rasterio.features.html
        shapes = [(geom, value) for geom, value in zip(gdf.geometry, gdf[category])]
        burned_img = features.rasterize(shapes=shapes, fill=0, out=w_arr, transform=wfile.transform)
        wfile.write_band(1, burned_img)
        # return burned_img

    slicewindow = wndows.Window.from_slices(rows=(windowsize, -windowsize), cols=(windowsize, -windowsize),
                                            height=w_arr.shape[0], width=w_arr.shape[1])

    with rasterio.open(temp_location) as rfile:

        new_meta = rfile.meta.copy()
        print('new metadata \n', new_meta)
        new_transform = rfile.window_transform(slicewindow)
        print('new transform ', new_transform)
        print('old transform', rfile.transform)
        new_meta.update({
            'height': slicewindow.height,
            'width': slicewindow.width,
            'transform': new_transform})

        w = rfile.read(1, window=slicewindow)

        print('shape of windowed read', w.shape)

    return w, new_meta


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
            data = vrt.read(1)
            # # if I watnted to write the thing....
            # outwarp = os.path.join(temp_path, 'temp_warp.tif')
            # rio_shutil.copy(vrt, outwarp, driver='GTiff')
            return data


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


def get_temps_by_dt(root, dt_tuple, tmax=True):
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
        if tmax:
            gmpath = os.path.join(root, f'{today.year}', 'tmax_{}{:03d}.tif'.format(today.year, today.timetuple().tm_yday))
        else:
            gmpath = os.path.join(root, f'{today.year}', 'tmin_{}{:03d}.tif'.format(today.year, today.timetuple().tm_yday))

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

        return (lower_guess_path, upper_guess_path), (lower_checkday, upper_checkday)
        # # for testing
        # return (f'{lower_checkday.year}-{lower_checkday.timetuple().tm_yday}', f'{upper_checkday.year}-{upper_checkday.timetuple().tm_yday}')
    else:
        # return the original ndvi array.
        return (poss_ndvi_path, poss_ndvi_path), (dt_obj, dt_obj)
        # # for testing
        # return(dt_obj, dt_obj)


def interpolate_arrays(arr1, arr2, dt1, dt2, target_dt, alg='linear'):
    """"""

    if alg == 'linear':
        rise = arr2/arr1
        run = dt2 - dt1
        slope_arr = rise/float(run.days)  # m
        interp_target = target_dt - dt1  # x
        target_arr = arr1 + (slope_arr * float(interp_target.days))  # y = b + mx

    return target_arr


def filter_growing_season(gs_start, gs_end, path_tup_lst, date_tup_lst):
    """"""

    new_path_tup_lst = []
    new_date_tup_lst = []

    for p, d in zip(path_tup_lst, date_tup_lst):
        # unpack the tuples
        d_s, d_e = d
        p_s, p_e = p
        # growing season bounds
        gs_begin = dt(year=d.year, month=gs_start[0], day=gs_start[1])
        gs_finish = dt(year=d.year, month=gs_end[0], day=gs_end[1])
    return new_path_tup_lst, new_date_tup_lst


shppath = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\preprocessing\state_boundaries'
outroot = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\preprocessing_III'

# =========================================================================================
# # todo - FILL out
# for the study area:
tmax = False
shape = os.path.join(shppath, 'AZ_aoi.shp')
processed_out = os.path.join(outroot, 'AZ_LVL1_ndvi55_rasters_tmin')
if not os.path.exists(processed_out):
    os.mkdir(processed_out)
drought_lvl = 1
# for all sites 2001-2017 inclusive - overlap of GRIDMET (1980-2017), NDVI (2001-2018),
# and Drought Monitor(2000-2020) Shapefiles
study_years = [f'{i}' for i in range(2001, 2018)]
ndvi_thresh = 0.55
# set to True if you want the ndvi higher than the threshold
thresh_high = True
# if True, NDVI will be ignored
ignore_ndvi = False
# =========================================================================================

for study_year in study_years:

    dpaths = sorted(glob(r'Z:\Users\Gabe\refET\Drought\full_ts\USDM_{}*.shp'.format(study_year)))
    print([os.path.split(p)[-1] for p in dpaths])

    # a location for rasterizing drought files
    temp_location = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\preprocessing_III\temp'
    if not os.path.exists(temp_location):
        os.mkdir(temp_location)

    # # old -deadbeef
    # stack_sample_file = r'Z:\Data\NDVI\USA\V006_250m\2001\2001001.250_m_16_days_NDVI.tif'
    # new - livebeef
    stack_sample_file = r'Z:\Data\ReferenceET\USA\Gridmet\Daily\ETo\2012\eto2012001.tif'

    stack_meta = get_std_transform(shapefile=shape, sample_raster=stack_sample_file)
    print('STACK META \n', stack_meta)
    # set the data type to float 32
    stack_meta['dtype'] = 'float32'
    # get the drought ranges
    # return two lists of tuples, the first with the paths representing endmembers of a drought period. The second
    drought_period_lst, drought_interval_lst = return_droughtrange(dpaths)

    print('drought period list \n', drought_period_lst, '\n drought interval list \n', drought_interval_lst)
    # get intersection of study area and droughts,
    drought_aois = return_drought_intersections(study_area=shape, df_list=drought_period_lst)

    # rasterize the droughts in the intersection to match NDVI resolution
    for dtup, dt_tup in zip(drought_aois, drought_interval_lst):

        if not(dtup[0].empty) and not(dtup[1].empty):
            print('ALL GOOD')
            d_start_aoi = dtup[0]
            d_end_aoi = dtup[1]
            d1_aoi_arr, d1_meta = rasterize_gdf(gdf=d_start_aoi, temp_location=os.path.join(temp_location, 'temp.tif'),
                                                meta_obj=stack_meta, category='DM')
            d2_aoi_arr, d2_meta = rasterize_gdf(gdf=d_end_aoi, temp_location=os.path.join(temp_location, 'temp.tif'),
                                                meta_obj=stack_meta, category='DM')

            print('two drought shapes: ', d1_aoi_arr.shape, d2_aoi_arr.shape)
            # find areas that remain under drought conditions continuously between two images.
            # instantiate a null array
            c_drought_arr = np.zeros(d1_aoi_arr.shape)
            # if the pixel is a non drought on either end of the drought period
            constantarr_bool = ((d1_aoi_arr >= drought_lvl) & (d2_aoi_arr >= drought_lvl))
            # # make sure that nan is also eliminated later on...
            nan_bool = ((d1_aoi_arr == 32767) | (d2_aoi_arr == 32767))
            # nan_bool

            # get the gridmet image paths for the drought interval, put em together in a list
            if tmax:
                gm_images, gm_dates = get_temps_by_dt(root=r'Z:\Data\Temperature\USA\Gridmet\tmax_gridmet\tmax_gridmet_tiffs_C',
                                                      dt_tuple=dt_tup, tmax=tmax)
            else:
                gm_images, gm_dates = get_temps_by_dt(root=r'Z:\Data\Temperature\USA\Gridmet\tmin_gridmet\tmin_gridmet_tiffs_C',
                                                      dt_tuple=dt_tup, tmax=tmax)
            drought_interval_arr = np.array([np.nan])

            # for each gridmet image:
            for gm_img, gm_date in zip(gm_images, gm_dates):
                # virtual warp out the gridmet for the study area and resample to the ndvi resolution.
                gm_arr = generate_standard_vrt(rasterpath=gm_img, meta=d1_meta)
                print('gridmet dtype')
                print(gm_arr.dtype)
                gm_arr = gm_arr.astype('float32')
                # For each gridmet image, search for the matching NDVI image, or the two nearest ndvi images.
                print(f'GM date: {gm_date.year}-{gm_date.timetuple().tm_yday}')

                # if ignore_ndvi is set to False, we interpolate modis NDVI and filter according to NDVI thresholds.
                if not ignore_ndvi:
                    print('doing NDVI filter')
                    ndvi_tup, ndvi_dt_tup = find_ndvi_paths(root=r'Z:\Data\NDVI\USA\V006_250m', dt_obj=gm_date, fmat=None)
                    print('NDVI tuple: ', ndvi_tup)

                    # resample ndvi, and if necessary, interpolate
                    # if the ndvi files are the same, that means that the gridmet falls ON an NDVI image date, so we don't need to interpolate
                    if ndvi_tup[0] == ndvi_tup[1]:
                        ndvi_arr = generate_standard_vrt(rasterpath=ndvi_tup[0], meta=d1_meta)  # meta=stack_meta
                    else:
                        # we need to interpolate, so unpack the two nearest dates and do a linear interpolation
                        ndvi_start, ndvi_end = ndvi_dt_tup
                        arr1 = generate_standard_vrt(rasterpath=ndvi_tup[0], meta=d1_meta)  # meta=stack_meta
                        arr2 = generate_standard_vrt(rasterpath=ndvi_tup[1], meta=d1_meta)  # meta=stack_meta

                        ndvi_arr = interpolate_arrays(arr1=arr1, arr2=arr2,
                                                      dt1=ndvi_start, dt2=ndvi_end,
                                                      target_dt=gm_date, alg='linear')

                    print(f'ndvi arr is shape {ndvi_arr.shape}')
                    print('ndvi dtype', ndvi_arr.dtype)
                    # fix the data type
                    ndvi_arr = ndvi_arr.astype('float32')
                    # convert units
                    ndvi_arr *= (1/10000.0)

                    if thresh_high:
                        # make a boolean array (dont be fooled, it's counter intuitive bc we set the lower ndvis to NAN lower down)
                        ndvi_bool = (ndvi_arr < ndvi_thresh)
                    else:
                        ndvi_bool = (ndvi_arr > ndvi_thresh)

                    # filter the gridmet,
                    # you want to turn where values are not good into NaN
                    # set low ndvi
                    gm_arr[ndvi_bool] = np.nan
                else:
                    print('IGNORING NDVI')

                gm_arr[~constantarr_bool] = np.nan
                gm_arr[nan_bool] = np.nan

                # If the array is all NAN, don't output it.
                check_arr = np.nan_to_num(gm_arr, copy=True, nan=0.0)


                if np.sum(check_arr) != 0:

                    # output gm arr
                    if tmax:
                        fmatstr = 'tmax_{}{:03d}.tif'
                    else:
                        fmatstr = 'tmin_{}{:03d}.tif'
                    with rasterio.open(os.path.join(processed_out,
                                                    fmatstr.format(gm_date.year, gm_date.timetuple().tm_yday)),
                                       'w', **d1_meta) as wfile:
                        wfile.write_band(1, gm_arr)
                else:
                    print(f'gm_arr for date {gm_date.year}-{gm_date.month}-{gm_date.day} is all NANs, so we skip it ')
                    pass

        else:
            print("no valid geometry intersections, so we're passing")
            pass



