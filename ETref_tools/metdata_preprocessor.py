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
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
# ============= standard library imports ========================
from utils.os_utils import windows_path_fix
from ETref_tools.refet_functions import conv_F_to_C, conv_mph_to_mps, conv_in_to_mm
"""This script will include functions for preprocessing Meteorological data from a given source. The functions here 
are bespoke to the weather station raw data format that is downloaded. The data will then be used to calculate ETo
 using dataframe_calc_daily_ETr.py and the functions in refet_functions.py"""

def strip_space_separated(space_separated_file):
    """For stripping lines of space separated files into a big list of lists"""
    stripped_rows = []
    with open(space_separated_file, 'r') as rfile:
        rows = [line for line in rfile]
        for r in rows:
            space_free = r.strip(' ')
            no_return = space_free.strip('\n')
            line_lst = no_return.split(' ')
            # print(repr(line_lst))
            line_lst = [l for l in line_lst if l != '']
            stripped_rows.append(line_lst)

    return stripped_rows

def jornada_preprocess(jornada_metpath):
    """
    gets the data of the jornada weather station and resamples etc to make it useful to calculate ETo
    :param jornada_metpath: path to a textfile of jornada meteorological data
    :return:
    """

    with open(jornada_metpath, 'r') as rfile:

        rows = [line for line in rfile]
        data_rows = []
        for r in rows:
            space_free = r.strip(' ')
            no_return = space_free.strip('\n')
            line_lst = no_return.split(' ')
            # print(repr(line_lst))
            line_lst = [l for l in line_lst if l != '']
            print(line_lst)

            if len(line_lst) == 41:
                data_rows.append(line_lst)

        rawdata = data_rows[1:]
        data_cols = data_rows[0]

        jdf = pd.DataFrame(data=rawdata, columns=data_cols)

        # from here need to resample to daily average and min and max based on certain criteria.
        date_series = jdf['Date']
        time_series = jdf['Time']

        def jornada_dt_format(date_str, time_str):
            """

            :param date_str: formatted like 01/01/2012 MM/DD/YYY
            :param time_str: hmm NOT zero padded like 945 or 1230 or 2400
            :return: datetime object
            """

            date_lst = date_str.split('/')
            # get the year month and day from [MM, DD, YYYY]
            mo = date_lst[0]
            day = date_lst[1]
            yr = date_lst[2]

            # split up the minute and the hour from the HHMM string
            min_str = time_str[-2:]
            hr = time_str[:-2]

            # to pad zeros onto a digit in string formatting it has to be an actual int or float, not string.
            hr_int = int(hr)

            # cool new 'literal' formatting of variables directly into a string - python 3.6 and better.
            dt_str = f'{mo}-{day}-{yr}-{hr_int:02d}-{min_str}'

            try:
                # turn the string into a datetime object
                dt = datetime.strptime(dt_str, '%m-%d-%Y-%H-%M')
            except ValueError:
                # John Anderson marks the 24th hour as belonging to the previous day...
                # Datetimes can only go to 23:59 for a given day

                # set the clock back to 23
                hr_int = 23
                min_str = '00'
                # make the datetime obj
                dt_str = f'{mo}-{day}-{yr}-{hr_int:02d}-{min_str}'
                dt = datetime.strptime(dt_str, '%m-%d-%Y-%H-%M')
                # manually set the datetime forward by one hour
                dt += timedelta(hours=1)

            print('jornada datetime', dt)
            return dt

        # apply the datetime function to two columns of the dataframe and create a new column
        jdf['datetime'] = jdf.apply(lambda x: jornada_dt_format(x['Date'], x['Time']), axis=1)
        # jdf['datetime'] = jdf[['Date', 'Time']].apply(lambda x: datetimeFormat(*x), axis=1) # another way to skin the cat

        print(jdf['datetime'])

        print('Hello World')

        # Use the datetime column to get the julian date as an interger
        jdf['doy'] = jdf.apply(lambda x: x['datetime'].timetuple().tm_yday, axis=1)

        # === get rid of bad or missing values -9 for temp and -99 for all others ===
        jdf[(jdf == '-9') | (jdf == '-99')] = np.nan
        # linearly interpolate across nan vals
        jdf.interpolate(method='linear')

        # === resample the timeseries to daily data ===
        # set the index to the datetime column
        jdf = jdf.set_index('datetime')
        # turn things into numbers that are numbers (only after setting the index)
        jdf = jdf.apply(pd.to_numeric, errors='ignore')
        print(jdf.head())

        # we need more than one RelHum column. 'RelHum' is avg relative humidity. New rows will be for daily Min and Max
        jdf['MaxRelHum'] = jdf['RelHum']
        jdf['MinRelHum'] = jdf['RelHum']

        # resample to daily data '1D'-> 1 day (different resamplings for different columns)
        jdfr = jdf.resample('1D').agg({'MaxAir': np.max, 'MinAir': np.min, 'AvgAir': np.mean, 'Solar': np.sum,
                                       'Ppt': np.sum, 'MaxRelHum': np.max, 'MinRelHum': np.min, 'RelHum': np.mean,
                                       'ScWndMg': np.mean, '5cmSoil': np.mean, '20cmSoil': np.mean, 'doy': np.median})

        return jdfr


def leyendecker_preprocess(metpath):
    """"""

    ld_csv = pd.read_csv(metpath)

    # === Now format the dataframe appropriately ===
    # TODO - make the formatting it's own separate function in metdata_preprocessor
    # 1) julian date
    # first make 'Date' into datetime
    ld_csv['datetime'] = ld_csv.apply(lambda x: datetime.strptime(x['Date'], '%Y-%m-%d'), axis=1)
    # then make the datetime into a day of year
    ld_csv['doy'] = ld_csv.apply(lambda x: x['datetime'].timetuple().tm_yday, axis=1)
    # 2) Set the index to be a datetime
    ld_csv = ld_csv.set_index('datetime')

    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print('essential df \n', ld_csv.head(10))

    # 3) get the units in metric and MJ (windspeed MilesPerHour -> MetersPerSecond & min, max and avg air temp F -> C, precip in->mm)
    # airtemp first
    temp_cols = ['Max Air Temperature (F)', 'Min Air Temperature (F)', 'Mean Air Temperature (F)']
    new_temp_cols = ['maxair', 'minair', 'meanair']
    for old, new in zip(temp_cols, new_temp_cols):
        ld_csv[new] = ld_csv.apply(lambda x: conv_F_to_C(tempF=x[old]), axis=1)
    # now windspeed
    ld_csv['wind_mps'] = ld_csv.apply(lambda x: conv_mph_to_mps(mph=x['Mean Wind Speed (MPH)']), axis=1)
    print(2)
    # now precip
    ld_csv['ppt'] = ld_csv.apply(lambda x: conv_in_to_mm(inches=x['Total Precipitation (in.)']), axis=1)

    return ld_csv


def airport_preprocess(weather_metpath):
    pass

def dri_preprocess(metpath):
    """preprocessing DRI Agrimet textfiles"""

    # todo ==== Generalize this bit of code to work for any metdata ====
    data_rows = []
    with open(metpath, 'r') as rfile:

        rows = [line for line in rfile]

        for r in rows:
            space_free = r.strip(' ')
            no_return = space_free.strip('\n')
            line_lst = no_return.split(' ')
            # print(repr(line_lst))
            line_lst = [l for l in line_lst if l != '']
            # print(line_lst)

            # if len(line_lst) == 41:
            data_rows.append(line_lst)

    # ^^^^^^ Generalize this bit of code to work for any metdata text file eh?^^^^^
    rawdata = data_rows[6:-2]

    data_cols = ['Date', 'Year', 'DOY', 'DOR', 'Solar', 'aveSpeed', 'wind_dir', 'speed_gust', 'mean_air_temp',
                 'max_air_temp', 'min_air_temp', 'mean_fuel_temp', 'max_fuel_temp', 'min_fuel_temp', 'mean_soilT',
                 'max_soilT', 'min_soilT', 'mean_soilT_10cm', 'max_soilT_10cm',  'minn_soilT_10cm',
                 'mean_soilT_20cm', 'max_soilT_20cm', 'min_soilT_20cm', 'mean_soilT50cm', 'max_soilT50cm',
                 'min_soilT50cm', 'mean_rel_hum', 'max_rel_hum', 'min_rel_hum', 'mean_press_mb','mean_batvolts',
                 'max_batvolts', 'minbatvolts', 'ET_total_ASCE', 'ET_Penman_total',
                 'heating_deg_days', 'cooling_deg_days', 'growing_deg_days', 'growing_deg_days2',
                 'ave_soil_moist_10cm', 'max_soil_moist_10cm', 'min_soil_moist_10cm', 'ave_soil_moist_20cm',
                 'max_soil_moist_20cm', 'min_soil_moist_20cm','ave_soil_moist_50cm', 'max_soil_moist_50cm',
                 'min_soil_moist_50cm', 'precip']
    print(len(data_cols))

    met_df = pd.DataFrame(data=rawdata, columns=data_cols)
    print(met_df.head())

    # data is already in daily metric formats so we just need to do unit conversions

    # Radiation - kW-hr/m2 -> MJ/m2    1kw-hr = 3.6 MJ
    met_df['Solar'] = met_df['Solar'].astype(float) * 3.6
    # convert back to string
    met_df['Solar'] = met_df['Solar'].astype(str)

    # atm pressure - mbar to KPa   1mbar = 0.1 kPa
    met_df['mean_press_mb'] = met_df['mean_press_mb'].astype(float) * 0.1
    # back to string
    met_df['mean_press_mb'] = met_df['mean_press_mb'].astype(str)

    # Get the dataframe to be dateindexed
    met_df['dt'] = met_df.apply(lambda x: datetime.strptime(x['Date'], '%m/%d/%Y'), axis=1)
    print(met_df['dt'])
    met_df.set_index(met_df['dt'])

    return met_df


def uscrn_preprocess(metpath, header_txt):
    """preprocessing USCRN weather data textfiles"""

    # get the header as a list first

    header_file_rows = strip_space_separated(header_txt)

    print(header_file_rows)

    headers = [i[1] for i in header_file_rows[2:]]

    print(headers)

    metdata = strip_space_separated(metpath)

    print(metdata)

    met_dict = {}

    for h in headers:
        met_dict[h] = []

    for line in metdata:

        for i, j in zip(line, headers):

            met_dict[j].append(i)


    met_df = pd.DataFrame(met_dict, columns=headers)

    print(met_df)

    # No unit corrections necessary

    return met_df

def uscrn_subhourly(metpath, header_txt):
    """
    preprocessing 5 minut interval USCRN weather data textfiles to be time aggregated to
    daily values for PM ETo calculations
    :param metpath: string of path to meteorological data files separated by spaces
    :param header_txt: string of path to header data separated by spaces
    :return: dataframe of daily met variables
    """

    # get the header as a list first
    header_file_rows = strip_space_separated(header_txt)
    # get the header value out and put it into a list, skipping the headings in the file.
    headers = [i[1] for i in header_file_rows[2:]]
    # format the met data into a list of lists
    metdata = strip_space_separated(metpath)
    met_dict = {}
    for h in headers:
        met_dict[h] = []
    for line in metdata:
        for i, j in zip(line, headers):
            met_dict[j].append(i)

    met_df = pd.DataFrame(met_dict, columns=headers)

    print(met_df['SOLAR_RADIATION'])

    # A function for formatting the date and time columns into a datetime for the dataframe.
    def uscrn_dt_format(date_str, time_str):
        """
        5 minute interval data
        :param date_str: formatted like 20160101 YYYYMMDD
        :param time_str: hhmm ZERO PADDED like 0945 or 1230 or 2400
        :return: datetime object
        """

        # get the year month and day from [MM, DD, YYYY]
        yr = date_str[0:4]
        mo = date_str[4:6]
        day = date_str[6:]

        # split up the minute and the hour from the HHMM string
        min_str = time_str[-2:]
        hr = time_str[:-2]

        # cool new 'literal' formatting of variables directly into a string - python 3.6 and better.
        dt_str = f'{yr}-{mo}-{day}-{hr}-{min_str}'

        try:
            # turn the string into a datetime object
            dt = datetime.strptime(dt_str, '%Y-%m-%d-%H-%M')
        except ValueError:
            raise

        print('uscrn datetime', dt)
        return dt

    # apply the datetime function to two columns of the dataframe and create a new column. Choose local time, not UTC
    met_df['datetime'] = met_df.apply(lambda x: uscrn_dt_format(x['LST_DATE'], x['LST_TIME']), axis=1)

    # NEXT..... Unit conversions, then time aggregation





if __name__ == "__main__":

    # mpath = r'Z:\Users\Gabe\refET\met_datasets\central_NV\Sand_Spring_Valley_NV_Agrimet_DRI.txt'
    # dri_preprocess(metpath=mpath)
    #
    # print('done')

    mpath = r'Z:\Users\Gabe\refET\met_datasets\central_NV\Mercury_NV_USCRN_5min.txt'
    header = r'Z:\Users\Gabe\refET\met_datasets\USCRN_5min_headers'

    # uscrn_preprocess(metpath=mpath, header_txt=header)
    uscrn_subhourly(metpath=mpath, header_txt=header)

    # TODO - WE need a script way to pull the sub-hourly data offline. copy paste is not practical.