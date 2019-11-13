# ===============================================================================
# Copyright 2019 Gabriel Parrish
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import os
import gdal
import ogr
import sys
from datetime import date, datetime
import pandas as pd
# ============= standard library imports ========================
from utils.os_utils import windows_path_fix

"""This script stores functions related to reading and writing raster data using GDAL"""


def x_y_extract(point_path, field='id'):
    """
    This extracts the x and y raster grid coordinates from a point shapefile
    :param point_path: string path to point shapefile
    :return:
    """
    # get an appropriate driver
    driver = ogr.GetDriverByName('ESRI Shapefile')

    # open the shapefile. Use 0 for read-only mode.
    datasource_obj = driver.Open(point_path, 0)
    if datasource_obj is None:
        print("cannot open {}".format(point_path))
        sys.exit(1)

    # get the layer object from the datasource
    layer_obj = datasource_obj.GetLayer()

    # get the features in the layer
    feature_count = layer_obj.GetFeatureCount()

    print("there are {} features".format(feature_count))

    # # get the feature of the shapefile. You can loop through features, but there should only be one.
    # feature = layer_obj.GetFeature(2)

    feature_dict = {}
    for i in range(1, feature_count+1, 1):

        feature = layer_obj.GetNextFeature()

        # you could get a features 'fields' like feature.GetField('id')
        field_value = feature.GetField(field)

        print("field -> {}".format(field_value))

        # but we just want the geometry of the feature
        geometry = feature.GetGeometryRef()

        # get the x and y
        x = geometry.GetX()
        y = geometry.GetY()

        print("x -> {}, y -> {}".format(x, y))

        feature_dict[field_value] = (x, y)

        # housekeeping
        feature.Destroy()  # always destroy the feature before the datasource

    # housekeeping
    datasource_obj.Destroy()

    return feature_dict


def raster_extract(raster_path, x, y, arc=True):
    """
    uses x and y from x_y_extract function to grab the value at the cordinates from the raster given in raster_path
    :param raster_path:
    :param x:
    :param y:
    :return:
    """

    # don't forget to register
    gdal.AllRegister()

    # open the raster datasource
    datasource_obj = gdal.Open(raster_path)
    if datasource_obj is None:
        print("Can't open the datasource from {}".format(raster_path))
        sys.exit(1)

    # get the size of image (for reading)
    rows = datasource_obj.RasterYSize
    cols = datasource_obj.RasterXSize

    print('rows and cols \n', rows, cols)

    # get georefference info to eventually calculate the offset:
    transform = datasource_obj.GetGeoTransform()
    xOrigin = transform[0]
    yOrigin = transform[3]
    print('xy origin', xOrigin, yOrigin)
    width_of_pixel = transform[1]
    height_of_pixel = transform[5]

    print('widht and height \n', width_of_pixel, height_of_pixel)

    # read in a band (only one band)
    band = datasource_obj.GetRasterBand(1)
    # ReadAsArray(xoffset, yoffset, xcount, ycount)
    data = band.ReadAsArray(0, 0, cols, rows)

    print('shape:', data.shape)

    # get the offsets so you can read the data from the correct position in the array.
    print(x, xOrigin, width_of_pixel)
    print(y, yOrigin, height_of_pixel)
    x_offset = int((x - xOrigin) / width_of_pixel)
    y_offset = int((y - yOrigin) / height_of_pixel)

    print('offset\n',x_offset, y_offset)

    # is this a [rows, columns] thing?
    try:
        value = data[y_offset, x_offset]
    except IndexError:
        print('INDEX ERROR, ASSUMING that we are using mini-models and that the array is 3X3 and taking center value')
        value = data[1, 1]
    # print "VALUE {}".format(value)

    # # housekeeping
    # datasource_obj.Destroy()

    return value


# def run_point_extract(point_path, raster_path, ending, landsat=False, sseb=False, output_path=None):
#     """
#
#     :param output_path:
#     :param point_path:
#     :param raster_path:
#     :param ending:
#     :return:
#     """
#
#     # Begin extraction from the point path.
#     feature_dictionary = x_y_extract(point_path)
#     print("feature dictionary", feature_dictionary)
#
#     # Use the feature dictionary to extract data from the rasters.
#     for feature, tup in feature_dictionary.iteritems():
#
#         # Get the X and Y coords from the dictionary and unpack them
#         x, y = tup
#         print(x, y)
#
#         # === Iterate the rasters ===
#
#         # Containers to hold the dates and values for the rasters
#         raster_date = []
#         raster_values = []
#
#         sseb_dict = {}
#
#         # store the raster values and image dates for the x and y coordinate pair into the lists
#         for path, dir, file in os.walk(raster_path, topdown=False):
#
#             print(path, dir, file)
#
#             for file in file:
#                 if file.endswith(ending):
#
#                     # path to the raster file
#                     raster_address = os.path.join(path, file)
#
#
#                     if landsat:
#
#                         # Format the date into dt object
#                         date_str = file.split('_')[0]
#                         date_str = date_str[-12:-5]
#
#                         print("date string {}".format(date_str))
#                         # get a datetime object from a julian date
#                         r_date = datetime.strptime(date_str, '%Y%j').date()
#                         raster_date.append(r_date)
#
#                     if sseb:
#                         name = file.split('.')[0]
#                         year = int(name.split('_')[-2])
#                         month = int(name.split('_')[-1])
#                         r_date = date(year, month, 1)
#                         raster_date.append(r_date)
#
#
#                     # get the raster value using raster_extract() function
#                     value = raster_extract(raster_address, x, y)
#                     raster_values.append(value)
#
#         if landsat:
#             # format the values from the different dates into a dataframe
#             output_dict = {'date': raster_date, 'value': raster_values}
#             output_df = pd.DataFrame(output_dict, columns=['date', 'value'])
#             csv_path = os.path.join(output_path, "point_shape_id_{}.csv".format(feature))
#
#             # use the pandas.to_csv() method to output to csv
#             output_df.to_csv(csv_path)
#
#         if sseb:
#             output_dict = {'date': raster_date, 'value': raster_values}
#
#             sseb_dict['{}'.format(feature)] = output_dict
#
#     if sseb:
#         return sseb_dict
#
#
#     print("COMPLETE")

