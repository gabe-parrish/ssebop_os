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
"""This script goes through date-named shape files from US Drought Monitor, GeoPandas compares a point
(coords or shape) representing a weather station, and sees what the drought condition is. If it's a D3 or D4 drought,
the datetime is noted. Discrete drought intervals are made from the drought condition time-series."""
import os
import sys
from shapely.geometry import Point
import geopandas as geopd
from datetime import datetime
from progressbar import progressbar
# ============= standard library imports ========================

# class Drought_USDM:
#     """A little tool specializing in getting timeseries of drought/nondrought conditions from US Drought Monitor
#     shapefiles based on coordinates. The user can optionally produce a csv file of the timeseries, otherwise, it is
#     simply held as an attribute in the object."""
#
#     accepted_formats = []
#     # if the output directory is None, make this an empty dictionary and fill it up.
#     drought_type = []
#     dates = []
#     drought_time_series = None
#
#     def __init__(self, coords, root_dir, fmt='USDM_YYYYmmdd.shp', output_dir=None, station_name='point_location'):
#         """
#
#         :param coords: A tuple of floats, read from a multi featured point shapefile, or input as is.
#         :param root_dir: Directory location of USDM drought shapefiles.
#         :param fmt: String key to indicate what the format is of the USDM drought shapefiles
#         :param output_dir: Optional parameter to output a csv file of the drought location for the point
#         :param station_name: Optional parameter to have the output csv station name included in the csv output filename.
#         """
#
#         self.point_location = Point(coords[0], coords[1])
#         self.root = root_dir
#         self.fmt = fmt
#
#         if output_dir is None:
#             self.drought_time_series = {}
#
#         self.output_dir = output_dir
#         self.station_name = station_name
#
#         if self.fmt != 'USDM_YYYYmmdd.shp':
#             print('USDM shapefiles of format USDM_YYYYmmdd.shp only accepted at this time')
#             sys.exit()
#
#     def drought_times(self, debug=False):
#         count = 0
#         for f in progressbar(os.listdir(self.root), redirect_stdout=True):
#             if f.endswith('.shp'):
#                 fpath = os.path.join(self.root, f)
#                 # get the datetime
#                 if self.fmt == 'USDM_YYYYmmdd.shp':
#                     fname = f.split('.')[0]
#                     dt_str = fname.split('_')[1]
#                     dt = datetime.strptime(dt_str, '%Y%m%d')
#                     self.dates.append(dt)
#                 else:
#                     print(f'{self.fmt} for that file-name style is not yet implemented')
#                     sys.exit()
#
#                 # geopandas open file, read as geodataframe
#                 gdf = geopd.read_file(fpath)
#                 # print('geodataframe \n', gdf.columns)
#                 # print('drought intersection \n', gdf['geometry'].contains(self.point_location))
#                 # make sure the dataframe is indexed by the Drought Monitor score of 0-4
#                 gdf.set_index('DM', inplace=True)
#                 # get a True/False answer for whether the drought geometry surface contains the point.
#                 try:
#                     drought_bool = gdf['geometry'].contains(self.point_location)
#                     # print('index stuff', drought_bool[drought_bool].index.values[0])
#                     dm_value = drought_bool[drought_bool].index.values[0]
#                 except:
#                     # print('No drought designation, exception thrown')
#                     dm_value = 0
#
#                 self.drought_type.append(dm_value)
#
#         if self.output_dir is None:
#             # if there is no output dir, retain the dates and drought type as an attribute for the user to access.
#             self.drought_time_series['Date'] = self.dates
#             self.drought_time_series['Drought'] = self.drought_type
#         else:
#             # output a file to a csv.
#             # sort them before writing to file!
#             # used: https://stackoverflow.com/questions/6618515/sorting-list-based-on-values-from-another-list
#             # or this one : https://www.geeksforgeeks.org/python-sort-values-first-list-using-second-list/
#             # or this? https://stackoverflow.com/questions/9764298/how-to-sort-two-lists-which-reference-each-other-in-the-exact-same-way
#             # apparently sort cannot do ints?
#             drght_type = [float(i) for i in self.drought_type]
#             # a decorate -> sort -> undecorate idiom...
#             sorted_drought_index, sorted_date = zip(*sorted(zip(drght_type, self.dates)))
#             print('sorted index \n', sorted_drought_index)
#             print('sorted date \n', sorted_date)
#             print('len sorted index \n', len(sorted_drought_index))
#             print('len sorted date \n', len(sorted_date))
#             # re intergerize.
#             sorted_drought_index = [int(i) for i in sorted_drought_index]
#             # todo - why is it repeating 3 times?!?! - DEBUG for real.
#             with open(os.path.join(self.output_dir, f'drought_timeline_{self.station_name}.csv'), 'w') as wfile:
#                 wfile.write('Date,Drought\n')
#                 for d, dtype in zip(sorted_date, sorted_drought_index):
#                     wfile.write('{}{:02d}{:02d},{}\n'.format(d.year, d.month, d.day, dtype))
#         # reset the dates and times at the end.
#         print('reseting')
#         self.dates = []
#         self.drought_type = []
#         print('also deleting index and date that are sorted')
#         del sorted_drought_index
#         del sorted_date
#         del drght_type
#
#     def read_drought_csv(self):
#         # todo - make this function able to read a pre-existing drought file
#         pass


def drought_USDM(coords, root_dir, fmt='USDM_YYYYmmdd.shp', output_dir=None, station_name='point_location'):

    point_location = Point(coords[0], coords[1])
    root = root_dir
    fmt = fmt
    dates = []
    drought_type = []

    if output_dir is None:
        drought_time_series = {}

    station_name = station_name

    if fmt != 'USDM_YYYYmmdd.shp':
        print('USDM shapefiles of format USDM_YYYYmmdd.shp only accepted at this time')
        sys.exit()
    count = 0
    for f in progressbar(os.listdir(root), redirect_stdout=True):
        if f.endswith('.shp'):
            fpath = os.path.join(root, f)
            # get the datetime
            if fmt == 'USDM_YYYYmmdd.shp':
                fname = f.split('.')[0]
                dt_str = fname.split('_')[1]
                dt = datetime.strptime(dt_str, '%Y%m%d')
                dates.append(dt)
            else:
                print(f'{fmt} for that file-name style is not yet implemented')
                sys.exit()

            # geopandas open file, read as geodataframe
            gdf = geopd.read_file(fpath)
            # print('geodataframe \n', gdf.columns)
            # print('drought intersection \n', gdf['geometry'].contains(self.point_location))
            # make sure the dataframe is indexed by the Drought Monitor score of 0-4
            gdf.set_index('DM', inplace=True)
            # get a True/False answer for whether the drought geometry surface contains the point.
            try:
                drought_bool = gdf['geometry'].contains(point_location)
                # print('index stuff', drought_bool[drought_bool].index.values[0])
                dm_value = drought_bool[drought_bool].index.values[0]
            except:
                # print('No drought designation, exception thrown')
                dm_value = 0

            drought_type.append(dm_value)

    if output_dir is None:
        # if there is no output dir, retain the dates and drought type as an attribute for the user to access.
        drought_time_series['Date'] = dates
        drought_time_series['Drought'] = drought_type
    else:
        # output a file to a csv.
        # sort them before writing to file!
        # https://stackoverflow.com/questions/9764298/how-to-sort-two-lists-which-reference-each-other-in-the-exact-same-way
        # apparently sort cannot do ints?
        drght_type = [float(i) for i in drought_type]
        # a decorate -> sort -> undecorate idiom...
        # sorted_drought_index, sorted_date = zip(*sorted(zip(drght_type, dates)))
        # from https://www.geeksforgeeks.org/python-sort-values-first-list-using-second-list/
        sorted_drought_index = [x for _, x in sorted(zip(dates, drght_type))]
        sorted_date = sorted(dates)
        print('sorted index \n', sorted_drought_index)
        print('sorted date \n', sorted_date)
        print('len sorted index \n', len(sorted_drought_index))
        print('len sorted date \n', len(sorted_date))
        # re intergerize.
        sorted_drought_index = [int(i) for i in sorted_drought_index]
        with open(os.path.join(output_dir, f'drought_timeline_{station_name}.csv'), 'w') as wfile:
            wfile.write('Date,Drought\n')
            for d, dtype in zip(sorted_date, sorted_drought_index):
                wfile.write('{}{:02d}{:02d},{}\n'.format(d.year, d.month, d.day, dtype))
    # # reset the dates and times at the end.
    # print('reseting')
    # dates = []
    # drought_type = []
    # print('also deleting index and date that are sorted')
    # del sorted_drought_index
    # del sorted_date
    # del drght_type

# def main():
#     """Runs an example of the drought USDM class"""
#
#     coords = (-110.529, 35.755)
#     root_dir = r'Z:\Users\Gabe\refET\Drought'
#     fmt = 'USDM_YYYYmmdd.shp'
#     output_location = r'C:\Users\gparrish\Documents'
#     site_name = 'testsite'
#
#     usdm_drought = Drought_USDM(coords=coords, root_dir=root_dir, fmt=fmt, output_dir=output_location,
#                                 station_name=site_name)
#     # run drought
#     usdm_drought.drought_times()


def generate_drought_files():

    # the site 'name' in the shapefile attribute.
    snames = ['YumaSouthAZ', 'PalomaAZ', 'HarquahalaAZ',
              'WilcoxBenchAZ', 'QueenCreekAZ',
              'RollAZ', 'CoolidgeAZ', # Kansas Settlement, 'YumaNorthGilaAZ'
              'DeKalbIL', 'BondvilleIL', 'MonmouthIL',
              'AntelopeValleyNV', 'CloverValleyNV', 'SnakeValleyNV',
              'SandSpringValleyNV', 'SmithValleyNV', 'HualapaiFlatNV',
              'ParadiseValleyNV', 'ReeseRiverValleyNV',  # MoapaValleyNV, Something_MA
              'LANEOK', 'RINGOK', 'EVAXOK',
              'BOISOK', 'HOLLOK', 'ALTUOK',
              'TIPTOK', 'GOODOK']
    # =loop through the features in the study site locations, and extract the coordinates, then using the
    #  Drought_USDM class, make csv files all throghout.
    study_site_locations = r'Z:\Users\Gabe\refET\refET_geo_files\true_reference_selectedCONUS.shp'
    # open the shapefile with Fiona, or geopandas.
    gdf = geopd.read_file(study_site_locations)

    print(gdf.head(15))
    names = gdf['name'].to_list()
    geometries = gdf['geometry'].to_list()

    print('names \n', names, '\ngeometries\n', geometries)

    root_dir = r'Z:\Users\Gabe\refET\Drought\full_ts'
    fmt = 'USDM_YYYYmmdd.shp'
    output_location = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\USDM_Drought_timeseries'
    overwrite = True
    # looping through the snames
    for sn, geom in zip(names, geometries):

        # drought_obj = Drought_USDM(coords=(geom.x, geom.y),  root_dir=root_dir, fmt=fmt, output_dir=output_location,
        #                            station_name=sn)
        # drought_obj.drought_times(debug=True)
        # # we need to delet the drought object otherwise shit accumulates
        #
        # print('deleting drought object')
        # del drought_obj
        drought_USDM(coords=(geom.x, geom.y),  root_dir=root_dir, fmt=fmt, output_dir=output_location,
                                   station_name=sn)


if __name__ == '__main__':
    # main()
    generate_drought_files()