#--------------------------------
# Name:         cimis_daily_cron_asset_upload.py
# Purpose:      Ingest CIMIS multi-band images into Earth Engine
#--------------------------------

import argparse
import datetime
import logging
import os
import re
import shutil
import subprocess
import sys
from time import sleep

import ee
import numpy as np
from osgeo import gdal, osr
import refet
import requests
from scipy import ndimage


def main(workspace, start_dt, end_dt, variables, overwrite_flag=False,
         cron_flag=False, composite_flag=True, upload_flag=True,
         ingest_flag=True, reverse_flag=False, key=None):
    """Ingest CIMIS data into Earth Engine

    Parameters
    ----------
    workspace : str
        Root folder of CIMIS data.
    start_dt : datetime
        Start date.
    end_dt : datetime
        End date (inclusive).
    variables : str
        Variables to process.
        Choices are: 'Tdew', 'Tx', 'Tn', 'Rnl', 'Rs', 'Rso', 'K', 'U2',
                     'ETo', 'ETo_ASCE', 'ETr_ASCE'.
    overwrite_flag : bool, optional
        If True, overwrite existing files (the default is False).
    cron_flag : bool, optional
        If True, remove any previous files intermediate files
        (the default is false).
    composite_flag : bool, optional
        If True, build multi-band composite images (the default is True).
    upload_flag : bool, optional
        If True, upload images to Cloud Storage bucket (the default is True).
    ingest_flag : bool, optional
        If True, ingest images into Earth Engine (the default is True).
    reverse_flag : bool, optional
        If True, process dates from latest to earliest.
    key : str, optional
        File path to an Earth Engine json key file (the default is None).

    Returns
    -------
    None

    Notes
    -----
    http://cimis.casil.ucdavis.edu/cimis/
    CIMIS ETo data starts: 2003-03-20
    Full parameters start: 2003-10-01 (water year 2004)

    """
    logging.info('\nIngesting CIMIS multi-band images into Earth Engine')

    # Define which CIMIS variables are needed for each user variable
    # ASCE ETo/ETr are computed from the components
    gz_vars = {
        'ETo_ASCE': ['Rs', 'Tdew', 'Tn', 'Tx', 'U2'],
        'ETr_ASCE': ['Rs', 'Tdew', 'Tn', 'Tx', 'U2'],
        'ETo': ['ETo'],
        'K': ['K'],
        'Rnl': ['Rnl'],
        'Rs': ['Rs'],
        'Rso': ['Rso'],
        'Tdew': ['Tdew'],
        'Tn': ['Tn'],
        'Tx': ['Tx'],
        'U2': ['U2']
    }
    # Define mapping of CIMIS variables to output file names
    # For now, these need to be identical to the user variable names
    gz_remap = {
        'ETo': 'ETo',
        'K': 'K',
        'Rnl': 'Rnl',
        'Rs': 'Rs',
        'Rso': 'Rso',
        'Tdew': 'Tdew',
        'Tn': 'Tn',
        'Tx': 'Tx',
        'U2': 'U2'
    }
    gz_fmt = '{variable}.asc.gz'
    tif_fmt = '{date}.tif'
    tif_dt_fmt = '%Y%m%d'

    # Bucket parameters
    # project_name = 'steel-melody-531'
    bucket_name = 'gs://climate-engine'
    bucket_folder = 'cimis'

    # Asset parameters
    asset_coll = 'projects/climate-engine/cimis/daily'
    asset_id_fmt = '{date}'
    asset_dt_fmt = '%Y%m%d'
    asset_id_re = re.compile('{}/(?P<date>\d{{8}})'.format(asset_coll))

    site_url = 'http://cimis.casil.ucdavis.edu/cimis'

    if os.name == 'posix':
        shell_flag = False
    else:
        shell_flag = True

    # There is only partial CIMIS data before 2003-10-01
    if start_dt < datetime.datetime(2003, 10, 1):
        start_dt = datetime.datetime(2003, 10, 1)
        logging.info('Adjusting start date to: {}'.format(
            start_dt.strftime('%Y-%m-%d')))
    if end_dt > datetime.datetime.today():
        end_dt = datetime.datetime.today()
        logging.info('Adjusting end date to:   {}\n'.format(
            end_dt.strftime('%Y-%m-%d')))

    # Check that user defined variables are valid and in CIMIS
    gz_variables = {}
    for v in variables:
        try:
            gz_variables[v] = gz_vars[v]
        except:
            logging.error('Unsupported variable: {}'.format(v))

    # CIMIS grid
    asset_shape = (560, 510)
    asset_extent = (-410000.0, -660000.0, 610000.0, 460000.0)
    # asset_shape = (552, 500)
    # asset_extent = (-400000.0, -650000.0, 600000.0, 454000.0)
    asset_cs = 2000.0
    asset_geo = (asset_extent[0], asset_cs, 0., asset_extent[3], 0., -asset_cs)

    # Spatial reference parameters
    asset_proj4 = (
        "+proj=aea +lat_1=34 +lat_2=40.5 +lat_0=0 +lon_0=-120 " +
        "+x_0=0 +y_0=-4000000 +ellps=GRS80 +datum=NAD83 +units=m +no_defs")
    asset_osr = osr.SpatialReference()
    asset_osr.ImportFromProj4(asset_proj4)
    # asset_epsg = 3310  # NAD_1983_California_Teale_Albers
    # asset_osr = gdc.epsg_osr(cimis_epsg)
    # asset_osr.MorphToESRI()
    asset_proj = asset_osr.ExportToWkt()

    # Assume the ancillary data was prepped separately
    ancillary_ws = os.path.join(workspace, 'ancillary')
    mask_raster = os.path.join(ancillary_ws, 'cimis_mask.tif')
    elev_raster = os.path.join(ancillary_ws, 'cimis_elev.tif')
    lat_raster = os.path.join(ancillary_ws, 'cimis_lat.tif')
    # lon_raster = os.path.join(ancillary_ws, 'cimis_lon.tif')
    mask_array = raster_to_array(mask_raster)

    if 'ETo_ASCE' in variables or 'ETr_ASCE' in variables:
        elev_array = raster_to_array(elev_raster)
        lat_array = raster_to_array(lat_raster)

    # In cron mode, remove all files from the bucket
    if cron_flag:
        logging.info('\nClearing all files from bucket folder')
        args = ['gsutil', '-m', 'rm',
                '{}/{}/*.tif'.format(bucket_name, bucket_folder)]
        # if not logging.getLogger().isEnabledFor(logging.DEBUG):
        #     args.insert(1, '-q')
        subprocess.run(args, shell=shell_flag)

    # Initialize Earth Engine
    logging.info('\nInitializing Earth Engine')
    if key:
        logging.info('  Using service account key file: {}'.format(key))
        # The "EE_ACCOUNT" parameter is not used if the key file is valid
        ee.Initialize(ee.ServiceAccountCredentials('deadbeef', key_file=key))
    else:
        ee.Initialize()
    ee.Number(1).getInfo()

    logging.debug('Image Collection: {}'.format(asset_coll))

    # Start with a list of dates to check
    logging.debug('\nBulding Date List')
    test_dt_list = list(date_range(start_dt, end_dt))
    if not test_dt_list:
        logging.info('  No test dates, exiting')
        return True
    logging.debug('\nTest dates: {}'.format(
        ', '.join(map(lambda x: x.strftime('%Y-%m-%d'), test_dt_list))))

    # Get a list of assets currently being ingested
    # Check task list before checking asset list in case a task switches
    #   from running to done before the asset list is retrieved.
    task_id_list = [
        desc.replace('\nAsset ingestion: ', '')
        for desc in get_ee_tasks(states=['RUNNING', 'READY']).keys()]
    task_dt_list = [
        datetime.datetime.strptime(match.group('date'), asset_dt_fmt)
        for asset_id in task_id_list
        for match in [asset_id_re.search(asset_id)] if match]

    # Switch date list to be dates that are missing
    # If overwrite_flag, keep all dates
    test_dt_list = [
        dt for dt in test_dt_list if dt not in task_dt_list or overwrite_flag]
    if not test_dt_list:
        logging.info('  No missing asset dates, exiting')
        return True
    else:
        logging.debug('\nMissing asset dates: {}'.format(', '.join(
            map(lambda x: x.strftime('%Y-%m-%d'), test_dt_list))))

    # Get a list of assets that are already ingested
    asset_id_list = get_ee_assets(asset_coll, shell_flag)
    asset_dt_list = [
        datetime.datetime.strptime(match.group('date'), asset_dt_fmt)
        for asset_id in asset_id_list
        for match in [asset_id_re.search(asset_id)] if match]

    # Switch date list to be dates that are missing
    # If overwrite_flag, keep all dates
    test_dt_list = [
        dt for dt in test_dt_list if dt not in asset_dt_list or overwrite_flag]
    if not test_dt_list:
        logging.info('  No missing asset dates, exiting')
        return False
    else:
        logging.debug('\nMissing asset dates: {}'.format(', '.join(
            map(lambda x: x.strftime('%Y-%m-%d'), test_dt_list))))

    logging.info('\nProcessing dates')
    for upload_dt in sorted(test_dt_list, reverse=reverse_flag):
        logging.info('{}'.format(upload_dt.date()))

        year_ws = os.path.join(workspace, upload_dt.strftime('%Y'))
        date_ws = os.path.join(year_ws, upload_dt.strftime('%Y-%m-%d'))
        upload_path = os.path.join(
            year_ws, tif_fmt.format(date=upload_dt.strftime(tif_dt_fmt)))
        bucket_path = '{}/{}/{}'.format(
            bucket_name, bucket_folder,
            upload_dt.strftime(asset_dt_fmt) + '.tif')
        asset_id = '{}/{}'.format(
            asset_coll,
            asset_id_fmt.format(date=upload_dt.strftime(asset_dt_fmt)))
        logging.debug('  {}'.format(upload_path))
        logging.debug('  {}'.format(bucket_path))
        logging.debug('  {}'.format(asset_id))

        # In cron mode, remove all local files before starting
        if cron_flag and os.path.isdir(date_ws):
            shutil.rmtree(date_ws)

        # The overwrite_flag check may be redundant
        if overwrite_flag and upload_dt in asset_dt_list:
            logging.info('  Removing existing asset')
            ee.data.deleteAsset(asset_id)
            # try:
            #     subprocess.check_output(
            #         ['earthengine', 'rm', asset_id], shell=shell_flag)
            # except Exception as e:
            #     logging.exception('  Exception: {}'.format(e))
        # if upload_dt in task_dt_list:
        #     # Eventually stop the export task

        # Always overwrite composite if asset doesn't exist
        # if overwrite_flag and os.path.isfile(upload_path):
        if os.path.isfile(upload_path):
            logging.debug('  Removing existing composite GeoTIFF')
            os.remove(upload_path)
        # if overwrite_flag and os.path.isdir(date_ws):
        #     shutil.rmtree(date_ws)
        if not os.path.isdir(date_ws):
            try:
                os.makedirs(date_ws)
            except Exception as e:
                logging.exception(str(e))
                continue


        # Computed products can have multiple inputs
        logging.debug('  Downloading component images')
        gz_var_list = sorted(list(set([
            gz_var for v in variables for gz_var in gz_variables[v]])))
        logging.debug('    GZ Variables: {}'.format(gz_var_list))

        for gz_var in gz_var_list:
            gz_file = gz_fmt.format(variable=gz_var)
            tif_file = '{}.tif'.format(gz_remap[gz_var])

            gz_url = '{}/{}/{}'.format(
                site_url, upload_dt.strftime('%Y/%m/%d'), gz_file)
            gz_path = os.path.join(date_ws, gz_file)
            asc_path = gz_path.replace('.gz', '')
            tif_path = os.path.join(date_ws, tif_file)
            # logging.debug('  {}'.format(gz_url))
            # logging.debug('  {}'.format(gz_path))
            # logging.debug('  {}'.format(asc_path))
            # logging.debug('  {}'.format(tif_out))

            # DEADBEEF - The files are named ".gz" but are not zipped
            if (not os.path.isfile(asc_path) and
                    not os.path.isfile(tif_path)):
                logging.debug('  Downloading ASC GZ file')
                url_download(gz_url, asc_path)

            # DEADBEEF - It might be better/easier to catch the HTTP error above
            if not os.path.isfile(asc_path):
                continue

            logging.debug('  Reading ASCII')
            output_array, output_geo = ascii_to_array(asc_path)
            output_shape = tuple(map(int, output_array.shape))

            # In the UC Davis data some arrays have a 500m cell size
            if output_geo[1] == 500.0 and output_geo[5] == -500.0:
                logging.info('  Rescaling input {} array'.format(gz_var))
                logging.debug('    Input Shape: {}'.format(output_shape))
                logging.debug('    Input Geo: {}'.format(output_geo))
                output_array = ndimage.zoom(output_array, 0.25, order=1)
                output_geo = (
                    output_geo[0], 2000.0, 0.0, output_geo[3], 0.0, -2000.0)
                output_shape = tuple(map(int, output_array.shape))
                logging.debug('    Output Shape: {}'.format(output_array.shape))
                logging.debug('    Output Geo: {}'.format(output_geo))

            # In the UC Davis data some arrays have a slightly smaller extent
            if (output_geo == (-400000.0, 2000.0, 0.0, 454000.0, 0.0, -2000.0) or
                    output_geo == (-400000.0, 2000.0, 0.0, 450000.0, 0.0, -2000.0)):
                logging.info('  Padding input {} array extent'.format(gz_var))
                logging.debug('    Shape: {}'.format(output_shape))
                logging.debug('    Geo: {}'.format(output_geo))
                # Assume input extent is entirely within default CIMIS extent
                int_xi, int_yi = array_geo_offsets(
                    asset_geo, output_geo, asset_cs)
                pad_width = (
                    (int_yi, asset_shape[0] - output_shape[0] - int_yi),
                    (int_xi, asset_shape[1] - output_shape[1] - int_xi))
                logging.debug('    Pad: {}'.format(pad_width))
                output_array = np.lib.pad(
                    output_array, pad_width, 'constant', constant_values=-9999.0)
            elif output_geo != asset_geo:
                logging.info('  Unexpected input {} array extent'.format(gz_var))
                logging.info('    Shape: {}'.format(output_shape))
                logging.info('    Geo: {}'.format(output_geo))
                # input('ENTER')
                continue

            # Mask out nodata areas from all arrays (Rs, K, and ETo)
            output_array[mask_array == 0] = -9999

            logging.debug('  Writing GeoTIFF')
            array_to_geotiff(
                output_array, tif_path, output_geo=asset_geo,
                output_proj=asset_proj, output_nodata=-9999)
            del output_array
            os.remove(asc_path)

        # Build computed RefET GeoTIFFs
        for variable in variables:
            tif_path = os.path.join(date_ws, '{}.tif'.format(variable))
            if variable not in ['ETo_ASCE', 'ETr_ASCE']:
                continue
            elif os.path.isfile(tif_path):
                continue
            logging.debug('  {}'.format(tif_path))

            # Read in RefET component variable arrays
            refet_vars = set(['Rs', 'Tdew', 'Tx', 'Tn', 'U2'])
            input_vars = set([os.path.splitext(f)[0] for f in os.listdir(date_ws)])
            if not refet_vars.issubset(input_vars):
                logging.warning(
                    '  Missing input variable(s) for computing ASCE ETo/ETr, '
                    'skipping date\n    {}'.format(
                        ', '.join(list(refet_vars - input_vars))))
                continue
            tmax_array = raster_to_array(os.path.join(date_ws, 'Tx.tif'))
            tmin_array = raster_to_array(os.path.join(date_ws, 'Tn.tif'))
            tdew_array = raster_to_array(os.path.join(date_ws, 'Tdew.tif'))
            rs_array = raster_to_array(os.path.join(date_ws, 'Rs.tif'))
            u2_array = raster_to_array(os.path.join(date_ws, 'U2.tif'))
            # mask_array = np.isfinite(tmax_array)

            # Compute Ea from Tdew
            ea_array = refet.calcs._sat_vapor_pressure(tdew_array)
            # ea_array = 0.6108 * np.exp(17.27 * tdew_array / (tdew_array + 237.3))

            # Compute ETo/ETr and save
            refet_obj = refet.Daily(
                tmin=tmin_array, tmax=tmax_array, ea=ea_array, rs=rs_array,
                uz=u2_array, zw=2, elev=elev_array, lat=lat_array,
                doy=int(upload_dt.strftime('%j')), method='asce',
                input_units={'tmax': 'C', 'tmin': 'C', 'ea': 'kPa',
                             'rs': 'MJ m-2 d-1', 'uz': 'm s-1', 'lat': 'deg'})
            output_array = refet_obj.etsz(variable.split('_')[0].lower())
            
            # Assume that if temp, tdew and wind are all zero 
            #   the ETr/ETo should also be zero.
            # This could also be handled using the fixed ancillary mask
            # mask_array = (
            #     (tmin_array == 0) & (tmax_array == 0) &
            #     (u2_array == 0) & (tdew_array == 0))
            output_array[mask_array == 0] = -9999
            
            # Set nodata to -9999 and save to GeoTIFF
            output_array[np.isnan(output_array)] = -9999
            
            array_to_geotiff(
                output_array, tif_path, output_geo=asset_geo,
                output_proj=asset_proj, output_nodata=-9999)

            del output_array, ea_array
            del tmax_array, tmin_array, tdew_array, rs_array, u2_array
            del refet_obj

        # Build composite image
        # We could also write the arrays directly to the composite image above
        # if composite_flag and not os.path.isfile(upload_path):
        if composite_flag:
            logging.debug('  Building composite image')
            # Only build the composite if all the input images are available
            input_vars = set(
                [os.path.splitext(f)[0] for f in os.listdir(date_ws)])
            if set(variables).issubset(input_vars):
                # Force output files to be 32-bit float GeoTIFFs
                output_driver = gdal.GetDriverByName('GTiff')
                output_rows, output_cols = asset_shape
                output_ds = output_driver.Create(
                    upload_path, output_cols, output_rows, len(variables),
                    gdal.GDT_Float32, ['COMPRESS=LZW', 'TILED=YES'])
                output_ds.SetProjection(asset_proj)
                output_ds.SetGeoTransform(asset_geo)
                for band_i, variable in enumerate(variables):
                    data_array = raster_to_array(
                        os.path.join(date_ws, '{}.tif'.format(variable)))
                    data_array[np.isnan(data_array)] = -9999
                    output_band = output_ds.GetRasterBand(band_i + 1)
                    output_band.WriteArray(data_array)
                    output_band.FlushCache()
                    output_band.SetNoDataValue(-9999)
                    del data_array, output_band
                output_ds = None
                del output_ds
            else:
                logging.warning(
                    '  Missing input images for composite\n  '
                    '  {}'.format(', '.join(list(set(variables) - input_vars))))


        # DEADBEEF - Having this check here makes it impossible to only ingest
        # assets that are already in the bucket.  Moving the file check to the
        # conditionals below doesn't work though because then the ingest call
        # can be made even if the file was never made.
        if not os.path.isfile(upload_path):
            continue

        if upload_flag:
            logging.info('  Uploading to bucket')
            args = ['gsutil', 'cp', upload_path, bucket_path]
            if not logging.getLogger().isEnabledFor(logging.DEBUG):
                args.insert(1, '-q')
            try:
                subprocess.check_output(args, shell=shell_flag)
                os.remove(upload_path)
            except Exception as e:
                logging.exception(
                    '    Exception: {}\n    Skipping date'.format(e))
                continue

        if ingest_flag:
            logging.info('  Ingesting into Earth Engine')
            # DEADBEEF - For now, assume the file is in the bucket
            args = [
                'earthengine', 'upload', 'image',
                '--bands', ','.join(variables),
                '--asset_id', asset_id,
                '--time_start', upload_dt.strftime('%Y-%m-%d'),
                # '--nodata_value', nodata_value,
                '--property', '(string)DATE_INGESTED={}'.format(
                    datetime.datetime.today().strftime('%Y-%m-%d')),
            ]
            # Add RefET version property if necessary
            if 'ETo_ASCE' in variables or 'ETr_ASCE' in variables:
                args.extend([
                    '--property',
                    '(string)REFET_VERSION={}'.format(refet.__version__)])
            # Add the image path last
            args.append(bucket_path)
            logging.debug('  Args: {}'.format(' '.join(args)))

            try:
                subprocess.check_output(args, shell=shell_flag)
            except Exception as e:
                logging.exception('    Exception: {}'.format(e))

        # # In cron mode, remove all local files after ingesting
        # if cron_flag and os.path.isdir(date_ws):
        #     shutil.rmtree(date_ws)

    # In cron mode, remove all local files after ingesting
    if cron_flag:
        logging.info('Removing folders')
        for year in list(set([str(test_dt.year) for test_dt in test_dt_list])):
            year_ws = os.path.join(workspace, year)
            logging.info('  {}'.format(year_ws))
            try:
                shutil.rmtree(year_ws)
            except Exception as e:
                logging.exception(str(e))
                continue


def raster_to_array(input_raster, band=1):
    """Return a NumPy array from a raster

    Parameters
    ----------
    input_raster : str
        File path to the raster for array creation.
    band : int
        Band to convert to array in the input raster.

    Returns
    -------
    output_array: The array of the raster values

    """
    input_raster_ds = gdal.Open(input_raster, 0)
    input_band = input_raster_ds.GetRasterBand(band)
    # input_type = input_band.DataType
    input_nodata = input_band.GetNoDataValue()
    output_array = input_band.ReadAsArray(
        0, 0, input_raster_ds.RasterXSize, input_raster_ds.RasterYSize)
    # For float types, set nodata values to nan
    if (output_array.dtype == np.float32 or
            output_array.dtype == np.float64):
        if input_nodata is not None:
            output_array[output_array == input_nodata] = np.nan
    input_raster_ds = None
    return output_array


def ascii_to_array(input_ascii, input_type=np.float32):
    """Convert an ASCII raster to a different file format

    """
    with open(input_ascii, 'r') as input_f:
        input_header = input_f.readlines()[:6]
    input_cols = float(input_header[0].strip().split()[-1])
    input_rows = float(input_header[1].strip().split()[-1])
    # DEADBEEF - I need to check cell corner vs. cell center here
    input_xmin = float(input_header[2].strip().split()[-1])
    input_ymin = float(input_header[3].strip().split()[-1])
    input_cs = float(input_header[4].strip().split()[-1])
    input_nodata = float(input_header[5].strip().split()[-1])
    input_geo = (
        input_xmin, input_cs, 0.,
        input_ymin + input_cs * input_rows, 0., -input_cs)

    output_array = np.genfromtxt(
        input_ascii, dtype=input_type, skip_header=6)
    output_array[output_array == input_nodata] = -9999
    # output_array[output_array == input_nodata] = np.nan

    return output_array, input_geo


def array_to_geotiff(output_array, output_path, output_geo, output_proj,
                     output_nodata=None, output_gtype=gdal.GDT_Float32):
    """Save NumPy array as a geotiff

    Parameters
    ----------
    output_array : np.array
    output_path : str
        GeoTIFF file path.
    output_geo : tuple or list of floats
        Geo-transform (xmin, cs, 0, ymax, 0, -cs).
    output_proj : str
        Projection Well Known Text (WKT) string.
    output_nodata : float, optional
        GeoTIFF nodata value (the default is None).
    output_gtype : int
        GDAL data type (the default is GDT_Float32).
        http://www.gdal.org/gdal_8h.html

    Returns
    -------
    None

    Notes
    -----
    There is no checking of the output_path file extension or that the
    output_array is 2d (1 band).

    """
    output_driver = gdal.GetDriverByName('GTiff')
    output_rows, output_cols = output_array.shape
    output_ds = output_driver.Create(
        output_path, output_cols, output_rows, 1, output_gtype,
        ['COMPRESS=LZW', 'TILED=YES'])
    output_ds.SetProjection(output_proj)
    output_ds.SetGeoTransform(output_geo)
    output_band = output_ds.GetRasterBand(1)
    if output_nodata:
        output_band.SetNoDataValue(output_nodata)
    output_band.WriteArray(output_array)
    output_band.FlushCache()
    output_band.GetStatistics(0, 1)
    output_ds = None


def array_geo_offsets(full_geo, sub_geo, cs):
    """Return x/y offset of a gdal.geotransform based on another gdal.geotransform

    Parameters
    ----------
    full_geo :
        larger gdal.geotransform from which the offsets should be calculated
    sub_geo :
        smaller form

    Returns
    -------
    x_offset: number of cells of the offset in the x direction
    y_offset: number of cells of the offset in the y direction

    """
    # Return UPPER LEFT array coordinates of sub_geo in full_geo
    # If portion of sub_geo is outside full_geo, only return interior portion
    x_offset = int(round((sub_geo[0] - full_geo[0]) / cs, 0))
    y_offset = int(round((sub_geo[3] - full_geo[3]) / -cs, 0))
    # Force offsets to be greater than zero
    x_offset, y_offset = max(x_offset, 0), max(y_offset, 0)
    return x_offset, y_offset


def date_range(start_dt, end_dt, days=1, skip_leap_days=False):
    """Generate dates within a range (inclusive)

    Parameters
    ----------
    start_dt : datetime
        Start date.
    end_dt : datetime
        End date (inclusive).
    days : int, optional
        Step size (the default is 1).
    skip_leap_days : bool, optional
        If True, skip leap days while incrementing (the default is False).

    Yields
    ------
    datetime

    """
    import copy
    curr_dt = copy.copy(start_dt)
    while curr_dt <= end_dt:
        if not skip_leap_days or curr_dt.month != 2 or curr_dt.day != 29:
            yield curr_dt
        curr_dt += datetime.timedelta(days=days)


def get_ee_assets(asset_id, shell_flag=False):
    """Return assets IDs in a collection

    Parameters
    ----------
    asset_id : str
        A folder or image collection ID.
    shell_flag : bool, optional
        If True, execute the command through the shell (the default is False).

    Returns
    -------
    list : Asset IDs

    """
    asset_id_list = []
    for i in range(1, 10):
        try:
            asset_id_list = subprocess.check_output(
                ['earthengine', 'ls', asset_id], universal_newlines=True,
                shell=shell_flag)
            asset_id_list = [x.strip() for x in asset_id_list.split('\n') if x]
            break
        except Exception as e:
            logging.error(
                '  Error getting asset list, retrying ({}/10)\n'
                '  {}'.format(i, e))
            sleep(i ** 2)
        except ValueError:
            logging.info('  Collection or folder doesn\'t exist')
            raise sys.exit()
    return asset_id_list


def get_ee_tasks(states=['RUNNING', 'READY']):
    """Return current active tasks

    Parameters
    ----------
    states : list

    Returns
    -------
    dict : Task descriptions (key) and task IDs (value).

    """

    logging.debug('  Active Tasks')
    tasks = {}
    for i in range(1,10):
        try:
            task_list = ee.data.getTaskList()
            task_list = sorted([
                [t['state'], t['description'], t['id']]
                for t in task_list if t['state'] in states])
            tasks = {t_desc: t_id for t_state, t_desc, t_id in task_list}
            break
        except Exception as e:
            logging.info(
                '  Error getting active task list, retrying ({}/10)\n'
                '  {}'.format(i, e))
            sleep(i ** 2)
    return tasks


def url_download(download_url, output_path):
    """

    Parameters
    ----------
    download_url : str
    output_path : str

    Returns
    -------
    None

    """
    for i in range(1, 10):
        try:
            response = requests.get(download_url)
        except Exception as e:
            logging.info('  Exception: {}'.format(e))
            return False

        logging.debug('  HTTP Status: {}'.format(response.status_code))
        if response.status_code == 200:
            pass
        elif response.status_code == 404:
            logging.debug('  Skipping')
            return False
        else:
            logging.info('  Retry attempt: {}'.format(i))
            sleep(i ** 2)
            continue

        try:
            with open(output_path, "wb") as output_f:
                output_f.write(response.content)
            return True
        except Exception as e:
            logging.info('  Exception: {}'.format(e))
            return False


def arg_valid_date(input_date):
    """Check that a date string is ISO format (YYYY-MM-DD)

    This function is used to check the format of dates entered as command
      line arguments.
    DEADBEEF - It would probably make more sense to have this function
      parse the date using dateutil parser (http://labix.org/python-dateutil)
      and return the ISO format string

    Parameters
    ----------
    input_date : string

    Returns
    -------
    datetime

    Raises
    ------
    ArgParse ArgumentTypeError

    """
    try:
        return datetime.datetime.strptime(input_date, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{}'.".format(input_date)
        raise argparse.ArgumentTypeError(msg)


def arg_valid_file(file_path):
    """Argparse specific function for testing if file exists

    Convert relative paths to absolute paths
    """
    if os.path.isfile(os.path.abspath(os.path.realpath(file_path))):
        return os.path.abspath(os.path.realpath(file_path))
        # return file_path
    else:
        raise argparse.ArgumentTypeError('{} does not exist'.format(file_path))


def arg_parse():
    """"""
    end_dt = datetime.datetime.today()

    parser = argparse.ArgumentParser(
        description='Ingest CIMIS daily data into Earth Engine',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--workspace', metavar='PATH',
        default=os.path.dirname(os.path.abspath(__file__)),
        help='Set the current working directory')
    parser.add_argument(
        '-s', '--start', type=arg_valid_date, metavar='DATE',
        default=(end_dt - datetime.timedelta(days=30)).strftime('%Y-%m-%d'),
        help='Start date (format YYYY-MM-DD)')
    parser.add_argument(
        '-e', '--end', type=arg_valid_date, metavar='DATE',
        default=(end_dt - datetime.timedelta(days=0)).strftime('%Y-%m-%d'),
        help='End date (format YYYY-MM-DD)')
    parser.add_argument(
        '-v', '--variables', nargs='+', metavar='VAR',
        default=['Tdew', 'Tx', 'Tn', 'Rnl', 'Rs', 'K', 'U2',
                 'ETo', 'ETo_ASCE', 'ETr_ASCE'],
        choices=['Tdew', 'Tx', 'Tn', 'Rnl', 'Rs', 'K', 'U2',
                 'ETo', 'ETo_ASCE', 'ETr_ASCE'],
        help='CIMIS daily variables')
    parser.add_argument(
        '-o', '--overwrite', default=False, action='store_true',
        help='Force overwrite of existing files')
    parser.add_argument(
        '--cron', default=False, action='store_true',
        help='Remove intermediate files')
    parser.add_argument(
        '--reverse', default=False, action='store_true',
        help='Process dates in reverse order')
    # The default values shows up as True for these which is confusing
    parser.add_argument(
        '--no-composite', action='store_false', dest='composite',
        help='Don\'t build multi-band composites images')
    parser.add_argument(
        '--no-upload', action='store_false', dest='upload',
        help='Don\'t upload images to cloud stroage bucket')
    parser.add_argument(
        '--no-ingest', action='store_false', dest='ingest',
        help='Don\'t ingest images into Earth Engine')
    parser.add_argument(
        '--key', type=arg_valid_file, metavar='FILE',
        help='JSON key file')
    parser.add_argument(
        '-d', '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action='store_const', dest='loglevel')
    args = parser.parse_args()

    # Convert relative paths to absolute paths
    if args.workspace and os.path.isdir(os.path.abspath(args.workspace)):
        args.workspace = os.path.abspath(args.workspace)

    return args


if __name__ == '__main__':
    args = arg_parse()
    logging.basicConfig(level=args.loglevel, format='%(message)s')
    main(workspace=args.workspace, start_dt=args.start, end_dt=args.end,
         variables=args.variables, overwrite_flag=args.overwrite,
         cron_flag=args.cron, composite_flag=args.composite,
         upload_flag=args.upload, ingest_flag=args.ingest,
         reverse_flag=args.reverse, key=args.key,
    )
