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
import math
from datetime import datetime, timedelta
# ============= standard library imports ========================
from utils.os_utils import windows_path_fix
from ETref_tools.refet_functions import conv_F_to_C, conv_mph_to_mps, conv_in_to_mm, conv_avgWattsRad_to_DailyKJmSquared


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
        # print(jdfr.index)
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

def dri_preprocess(metpath, interpolate=True, terp_lim=3):
    """preprocessing DRI NICE Net textfiles"""

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

    met_df = pd.DataFrame(data=rawdata, columns=data_cols, dtype=float)
    # take care on NaN vals
    met_df[met_df == -9999.0] = np.nan
    print(met_df.head())

    # data is already in daily metric formats so we just need to do unit conversions

    # Radiation - kW-hr/m2 -> MJ/m2    1kw-hr = 3.6 MJ
    met_df['Solar'] = met_df['Solar'].astype(float) * 3.6
    # # convert back to string
    # met_df['Solar'] = met_df['Solar'].astype(str)

    # atm pressure - mbar to KPa   1mbar = 0.1 kPa
    met_df['mean_press_mb'] = met_df['mean_press_mb'].astype(float) * 0.1
    # # back to string
    # met_df['mean_press_mb'] = met_df['mean_press_mb'].astype(str)

    # Get the dataframe to be dateindexed
    met_df['dt'] = met_df.apply(lambda x: datetime.strptime(x['Date'], '%m/%d/%Y'), axis=1)
    print(met_df['dt'])
    met_df = met_df.set_index('dt')

    if interpolate:
        # USE PANDAS interpolation to cut down on missing values
        print('DOING A LINEAR INTERPOLATION with a limit of {} spots'.format(terp_lim))
        met_df.interpolate(method='linear', limit=terp_lim)

    if not interpolate:
        print('NOT INTERPOLATING!!!')

    print('dri index', met_df.index)

    met_df.to_csv(r'C:\Users\gparrish\Desktop\dri_test.csv')

    return met_df

def azmet_preprocess(metpath):
    """"""
    pass


def okmesonet_preprocess(metpath):
    """"""

    def convert_f_to_c(degrees_f):
        """"""
        deg_C = (degrees_f - 32) * (5/9)
        return deg_C

    def convert_mph_to_mps(mph):
        """"""
        mps = mph * 0.44704
        return mps

    def convert_in_to_mm(inches):
        """"""
        mm = inches * 25.4
        return mm

    okdf = pd.read_csv(metpath, header=0, index_col=False)

    # Taking care of the Nodata Values
    okdf[(okdf == 999) | (okdf == 999.0) | (okdf == 0.0) | (okdf == 0) | (okdf == -996) | (okdf == -996.0) | (okdf == -999) | (okdf == -999.0)] = np.nan

    okdf['dt'] = okdf.apply(lambda x: datetime.strptime("{}-{:02d}-{:02d}".format(int(x['YEAR']), int(x['MONTH']), int(x['DAY'])), '%Y-%m-%d'), axis=1)
    okdf['DOY'] = okdf.apply(lambda x: x['dt'].timetuple().tm_yday, axis=1)

    okdf['TMAX'] = okdf.apply(lambda x: convert_f_to_c(x['TMAX']), axis=1)
    okdf['TMIN'] = okdf.apply(lambda x: convert_f_to_c(x['TMIN']), axis=1)
    okdf['TAVG'] = okdf.apply(lambda x: convert_f_to_c(x['TAVG']), axis=1)

    okdf['RAIN'] = okdf.apply(lambda x: convert_in_to_mm(x['RAIN']), axis=1)

    # This was llllllll
    okdf['2AVG'] = okdf.apply(lambda x: convert_mph_to_mps(x['2AVG']), axis=1)

    # set the index to the datetime.
    okdf = okdf.set_index('dt')

    return okdf


def okmesonet_separate(metpath, output_loc):
    """
    This function is called on it's own to break up daily metdata from OK mesonet into separate files
    corresponding to site.
    :param metpath: string path
    :param output_loc: string path where all .csv files for 140+ sites will be written.
    :return:
    """

    # # we split the line and not ln bc we want to keep the \n HERE WE ARE FIXING SOME UNITS WE NEED...
    # # ...FOR OUR CALCULATION
    # ln_lst = convert_seven_indices(line.split(','))
    # # undo the split of the list with the corrected units
    # units_line = ','.join(ln_lst)

    def convert_f_to_c(degrees_f):

        deg_C = (degrees_f - 32) * (5/9)
        return deg_C

    def convert_mph_to_mps(mph):

        mps = mph * 0.44704
        return mps

    def convert_in_to_mm(inches):
        mm = inches * 25.4
        return mm

    def convert_seven_indices(ln_lst):
        """"""
        # convert temperatures
        ln_lst[4] = str(convert_f_to_c(float(ln_lst[4])))
        ln_lst[5] = str(convert_f_to_c(float(ln_lst[5])))
        ln_lst[6] = str(convert_f_to_c(float(ln_lst[6])))

        # convert wind speeds
        ln_lst[28] = str(convert_mph_to_mps(float(ln_lst[28])))
        ln_lst[29] = str(convert_mph_to_mps(float(ln_lst[29])))
        ln_lst[30] = str(convert_mph_to_mps(float(ln_lst[30])))

        ln_lst[38] = str(conv_in_to_mm(float(ln_lst[38])))

        return ln_lst


    doc_dict = {}
    with open(metpath, 'r') as rfile:
        for i, line in enumerate(rfile):
        # for i, line in zip(range(10), rfile):
            print(line)
            if i == 0:
                col_line = line.strip('\n')
            else:
                # print(line)
                ln = line.strip('\n')
                ln_lst = ln.split(',')
                stid = ln_lst[3]

                # print('id: ', stid)
                doc_dict[stid] = []

    with open(metpath, 'r') as rfile:
        for i, line in enumerate(rfile):
        # for i, line in zip(range(10), rfile):
            if i != 0:
                ln = line.strip('\n')
                ln_lst = ln.split(',')
                stid = ln_lst[3]

                # print('id append:', stid)
                doc_dict[stid].append(line)

    # print('doc dict, \n', doc_dict)
    # print('cols:', col_line)

    outfilenames = []
    for k, v in doc_dict.items():
        with open(os.path.join(output_loc, f'{k}.csv'), 'w') as wfile:
            outfilenames.append(f'{k}.csv')
            wfile.write(col_line)
            for line in v:
                wfile.write(line)

def delaware_separate(metpath, output_loc):
    """"""

    doc_dict = {}
    with open(metpath, 'r') as rfile:
        for i, line in enumerate(rfile):
            # for i, line in zip(range(10), rfile):
            print(line)
            if i == 0:
                col_line = line.strip('\n')
            else:
                # print(line)
                ln = line.strip('\n')
                ln_lst = ln.split(',')
                stid = ln_lst[0]

                # print('id: ', stid)
                doc_dict[stid] = []

    with open(metpath, 'r') as rfile:
        for i, line in enumerate(rfile):
            # for i, line in zip(range(10), rfile):
            if i != 0:
                ln = line.strip('\n')
                ln_lst = ln.split(',')
                stid = ln_lst[0]

                # print('id append:', stid)
                doc_dict[stid].append(line)

    # print('doc dict, \n', doc_dict)
    # print('cols:', col_line)

    outfilenames = []
    for k, v in doc_dict.items():
        with open(os.path.join(output_loc, f'{k}.csv'), 'w') as wfile:
            outfilenames.append(f'{k}.csv')
            wfile.write(col_line)
            for line in v:
                wfile.write(line)

def illinois_CN_reformat(metpath, output_loc):
    """"""

    metfile = os.path.split(metpath)[1]
    metname = metfile[0:3]
    outfile = os.path.join(output_loc, '{}.csv'.format(metname))
    lines = []
    with open(metpath, 'r') as rfile:

        for i, line in enumerate(rfile):
            if i == 0:
                cols = line.split('\t')
                columns = '{}'.format(','.join(cols))
                print(len(columns))
            elif i == 1:
                print('not_cols', line.split('\t'))
            else:
                line = line.strip('\n')
                ln = line.split('\t')
                l ='{}\n'.format(','.join(ln))
                lines.append(l)

    with open(outfile, 'w') as wfile:
        wfile.write(columns)
        for i in lines:
            if i.split(',')[0].isdigit():
                wfile.write(i)

def illinois_CN_preprocess(metpath):
    """"""
    df = pd.read_csv(metpath, header=0, index_col=False)

    # Taking care of the Nodata Values
    df[(df == 999) | (df == 999.0) | (df == 0.0) | (df == 0) | (df == -996) | (df == -996.0) | (
                df == -999) | (df == -999.0) | (df == '----') | (df == '-----') | (df == '---') |
       (df == '---- ') | (df == '--- ') | (df == '0.00 M')] = np.nan

    df['dt'] = df.apply(
        lambda x: datetime.strptime("{}-{:02d}-{:02d}".format(int(x['year']), int(x['month']), int(x['day'])),
                                    '%Y-%m-%d'), axis=1)
    df['DOY'] = df.apply(lambda x: x['dt'].timetuple().tm_yday, axis=1)

    df['max_air_temp'] = df.apply(lambda x: conv_F_to_C(x['max_air_temp']), axis=1)
    df['min_air_temp'] = df.apply(lambda x: conv_F_to_C(x['min_air_temp']), axis=1)
    df['avg_air_temp'] = df.apply(lambda x: conv_F_to_C(x['avg_air_temp']), axis=1)

    df['precip'] = df.apply(lambda x: conv_in_to_mm(x['precip']), axis=1)
    df['pot_evapot'] = df.apply(lambda x: conv_in_to_mm(x['pot_evapot']), axis=1)

    df['max_wind_gust'] = df.apply(lambda x: conv_mph_to_mps(x['max_wind_gust']), axis=1)
    df['avg_wind_speed'] = df.apply(lambda x: conv_mph_to_mps(x['avg_wind_speed']), axis=1)

    df['min_rel_hum'] = df.apply(lambda x: float(x['min_rel_hum']), axis=1)
    df['max_rel_hum'] = df.apply(lambda x: float(x['max_rel_hum']), axis=1)

    df['sol_rad'] = df.apply(lambda x: float(x['sol_rad']), axis=1)

    # set the index to the datetime.
    df = df.set_index('dt')

    return df

def uscrn_subhourly(metpath, header_txt):
    """
    preprocessing 5 minute interval USCRN weather data textfiles to be time aggregated to
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

    met_df[(met_df == '-9999.0') | (met_df == '-99.000') | (met_df == '-9999')] = np.nan

    # print(met_df['SOLAR_RADIATION'])

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

        # print('uscrn datetime', dt)
        return dt


    # apply the datetime function to two columns of the dataframe and create a new column. Choose local time, not UTC
    met_df['datetime'] = met_df.apply(lambda x: uscrn_dt_format(x['LST_DATE'], x['LST_TIME']), axis=1)

    met_df['DOY'] = met_df.apply(lambda x: int(x['datetime'].strftime('%j').strip('0')), axis=1)

    # NEXT..... Unit conversions, then time aggregation

    # convert W/m2 = (J/s)/m2 to MJ/m2
    secs_in_5min = 5.0 * 60.0
    # 5 minute cumulative solar radiation
    met_df['SOLAR_MJ_FLUX'] = met_df['SOLAR_RADIATION'].astype(float) * secs_in_5min * 1.0e-6
    # met_df['SOLAR_MJ_FLUX'] = met_df.apply(lambda x: float(x['SOLAR_RADIATION']) * secs_in_5min * 1.0e-6)

    # adjust wind to be 2m above ground surface (USCRN set at 1.5m height)
    z1 = 1.5
    z2 = 2.0
    #ASCE pg 193 Jensen n Allen
    h = 0.12  # mean plant height in megters (for ETo after pg 2 "Step by Step Calculation of the Penman-Monteith
    # Evapotranspiration (FAO-56 Method) by Zotarelli et al)
    d = 0.67*h  # zero plane displacement height
    zom = 0.12 * h  # roughness length affecting momentum transfer
    # Eq 6 - 5 Jensen and Allen ASCE pg 111 used below (eq 11-60- on pg 394 is overly complicated) **math.log is ln
    met_df['WIND_1_5'] = met_df['WIND_1_5'].astype(float)
    met_df['WIND_2'] = met_df.apply(lambda x: x['WIND_1_5'] * ((math.log((z2 - d)/zom))/(math.log((z1 - d)/zom))), axis=1)

    # # 1) Need to get a daily Maximum and minimum air temp as well as the avg air temp.
    # temporarily set the columns equal to the values they will be calculated from
    met_df['AIR_TEMPERATURE'] = met_df['AIR_TEMPERATURE'].astype(float)
    met_df['MAX_AIR'] = met_df['AIR_TEMPERATURE']
    met_df['MIN_AIR'] = met_df['AIR_TEMPERATURE']
    # 2)  We need daily max and min relative humidity
    met_df['RELATIVE_HUMIDITY'] = met_df['RELATIVE_HUMIDITY'].astype(float)
    met_df['MAX_REL_HUM'] = met_df['RELATIVE_HUMIDITY']
    met_df['MIN_REL_HUM'] = met_df['RELATIVE_HUMIDITY']
    # 3) Solar radiation will be cumulative

    # set the index of the dataframe to the datetime
    met_df = met_df.set_index('datetime')

    print(met_df.index)

    met_df['PRECIPITATION'] = met_df['PRECIPITATION'].astype(float)
    met_df['DOY'] = met_df['DOY'].astype(int)

    met_df = met_df.resample('1D').agg({'MAX_AIR': np.max,'MIN_AIR': np.min, 'AIR_TEMPERATURE': np.mean,
                                        'SOLAR_MJ_FLUX': np.sum, 'PRECIPITATION': np.sum, 'MAX_REL_HUM': np.max,
                                        'MIN_REL_HUM': np.min, 'RELATIVE_HUMIDITY': np.mean, 'WIND_2': np.mean,
                                        'DOY': np.min})

    # get rid of extreme vals
    met_df[(met_df['SOLAR_MJ_FLUX'] < -100.0) | (met_df['SOLAR_MJ_FLUX'] > 100.0)] = np.nan

    met_df.to_csv(r'C:\Users\gparrish\Desktop\test.csv')

    return met_df

def uscrn_batch_agg(dirpath, header_path):
    """"Having downloaded a bunch of USCRN data as textfiles and put them all into a folder, this script will grab them,
join them together and make one big text file. in future use uscrn_ftp.py once written"""
    df_list = []
    for i in os.listdir(dirpath):
        fullpath = os.path.join(dirpath, i)
        # df_list.append(fullpath)

        df = uscrn_subhourly(fullpath, header_path)
        # df_final = uscrn_subhourly(fullpath, header_path)
        df_list.append(df)

    uscrn_df = pd.concat(df_list)
    return uscrn_df

def nc_econet_reformat(metpath, output_loc):
    """"""
    filen = os.path.split(metpath)[1]
    sitename = filen.split('_')[-2]

    datas = []
    with open(metpath, 'r') as rfile:
        for i, line in enumerate(rfile):
            ln = line.split('\t')
            print(ln)
            if i == 0:
                columns = ','.join(ln)
                print(columns)

            else:
                dataline = ','.join(ln)
                print(dataline)
                datas.append(dataline)

    with open(os.path.join(output_loc, '{}.csv'.format(sitename)), 'w') as wfile:
        wfile.write(columns)
        for dline in datas:
            wfile.write(dline)

def nc_econet_preprocess(metpath):
    """"""

    # == NOTE:  solar rad for NC is available as Average Solar Radiation in W/m2 not total daily solar radiation ==
    df = pd.read_csv(metpath, header=0, index_col=False)

    # Taking care of the Nodata Values
    df[(df == 999) | (df == 999.0) | (df == 0.0) | (df == 0) | (df == -996) | (df == -996.0) | (
            df == -999) | (df == -999.0) | (df == '----') | (df == '-----') | (df == '---') |
       (df == '---- ') | (df == '--- ') | (df == '0.00 M') | (df == '') | (df == ' ') | (df == -6999) | (df == -6999.0)
       | (df == '-6999')] = np.nan

    df['dt'] = df.apply(lambda x: datetime.strptime(x['Date/Time (EST)'], '%Y-%m-%d'), axis=1)

    df['DOY'] = df.apply(lambda x: x['dt'].timetuple().tm_yday, axis=1)

    df['max_air_temp'] = df.apply(lambda x: conv_F_to_C(x['Maximum Temperature (F)']), axis=1)
    df['min_air_temp'] = df.apply(lambda x: conv_F_to_C(x['Minimum Temperature (F)']), axis=1)
    df['avg_air_temp'] = df.apply(lambda x: conv_F_to_C(x['Average Temperature (F)']), axis=1)

    # NOTE NC ECONET does not come with precip
    # df['precip'] = df.apply(lambda x: conv_in_to_mm(x['precip']), axis=1)
    df['pot_evapot'] = df.apply(lambda x: conv_in_to_mm(x['Penman-Monteith Reference Crop Evapotranspiration (in)']), axis=1)

    df['max_wind_gust'] = df.apply(lambda x: conv_mph_to_mps(x['Maximum Wind Speed (mph)']), axis=1)
    df['avg_wind_speed'] = df.apply(lambda x: conv_mph_to_mps(x['Average Wind Speed (mph)']), axis=1)

    df['min_rel_hum'] = df.apply(lambda x: float(x['Minimum Relative Humidity (%)']), axis=1)
    df['max_rel_hum'] = df.apply(lambda x: float(x['Maximum Relative Humidity (%)']), axis=1)
    df['avg_rel_hum'] = df.apply(lambda x: float(x['Average Relative Humidity (%)']), axis=1)

    df['sol_rad'] = df.apply(lambda x: float(conv_avgWattsRad_to_DailyKJmSquared(x['Average Solar Radiation (W/m2)'])),
                             axis=1)

    # set the index to the datetime.
    df = df.set_index('dt')

    return df

def florida_separate(metpath, output_loc):
    """"""

    doc_dict = {}
    with open(metpath, 'r') as rfile:
        for i, line in enumerate(rfile):
            print(line)
            if i == 0:
                col_line = line.strip('\n')
            else:
                # print(line)
                ln = line.strip('\n')
                ln_lst = ln.split(',')
                stid = ln_lst[0]

                # print('id: ', stid)
                doc_dict[stid] = []

    with open(metpath, 'r') as rfile:
        for i, line in enumerate(rfile):
            # for i, line in zip(range(10), rfile):
            if i != 0:
                ln = line.strip('\n')
                ln_lst = ln.split(',')
                stid = ln_lst[0]

                # print('id append:', stid)
                doc_dict[stid].append(line)

    # print('doc dict, \n', doc_dict)
    # print('cols:', col_line)

    outfilenames = []
    for k, v in doc_dict.items():
        with open(os.path.join(output_loc, f'{k}.csv'), 'w') as wfile:
            outfilenames.append(f'{k}.csv')
            wfile.write(col_line)
            for line in v:
                wfile.write(line)


if __name__ == "__main__":

    # mpath = r'Z:\Users\Gabe\refET\met_datasets\central_NV\Sand_Spring_Valley_NV_Agrimet_DRI.txt'
    # dri_preprocess(metpath=mpath)

    # print('done')

    # mpath = r'Z:\Users\Gabe\refET\met_datasets\central_NV\Mercury_NV_USCRN_5min.txt'
#     # header = r'Z:\Users\Gabe\refET\met_datasets\USCRN_5min_headers'
#     #
#     # # uscrn_preprocess(metpath=mpath, header_txt=header)
#     # uscrn_subhourly(metpath=mpath, header_txt=header)
#     #
# #     # # TODO - WE need a script way to pull the sub-hourly data offline. copy paste is not practical.
#     mesonet_path = r'Z:\Users\Gabe\refET\OK_Mesonet\64040170\64040170.csv'
#     mnet_path = r'Z:\Users\Gabe\refET\OK_Mesonet'
#     okmesonet_separate(metpath=mesonet_path, output_loc=mnet_path)


    # # === Illinois ===
    # root = r'Z:\Users\Gabe\refET\Illinois_CN\allstations_archived'
    # for f in os.listdir(root):
    #     metpath = os.path.join(root, f)
    #     illinois_CN_reformat(metpath, output_loc=r'Z:\Users\Gabe\refET\Illinois_CN\reformatted')


    # # === Cackalack Del Norte ===
    # # NOTE - Average Solar radiation in (W/(m^2)) not total radiation in KJ Needs to be converted
    # root = r'Z:\Users\Gabe\refET\NC_EcoNet\NC_EcoNet_Data'
    # for f in os.listdir(root):
    #     if f.endswith('.txt'):
    #         metpath = os.path.join(root, f)
    #         nc_econet_reformat(metpath, output_loc=r'Z:\Users\Gabe\refET\NC_EcoNet\NC_Econet_Reformat')

    # # === Delaware extract ===
    # root = r'Z:\Users\Gabe\refET\Delaware'
    # file = r'data_gabriel.csv'
    # outloc = r'delaware_siteData_reformat'
    #
    # p = os.path.join(root, file)
    # op = os.path.join(root, outloc)
    #
    # delaware_separate(p, op)

    # === Florida FAWN extraction ===

    # PHASE 1

    # ### ==== Phase I FLORIDA =====
    # fla_out = r'C:\Users\gparrish\Desktop\mfile_out'
    # fla_in = r'Z:\Users\Gabe\refET\FAWN\FAWN_raw'
    #
    # columns = None
    # megafile = []
    #
    # for path, dir, fil in os.walk(fla_in):
    #     print(path)
    #     print(fil)
    #
    #     for f in fil:
    #         if f.endswith('.csv'):
    #             fpath = os.path.join(path, f)
    #             with open(fpath, 'r') as rfile:
    #                 for i, line in enumerate(rfile):
    #                     if i == 0:
    #                         columns = line
    #                     else:
    #                         megafile.append(line)
    # outpath = os.path.join(fla_out, 'megafile.csv')
    #
    # with open(outpath, 'w') as wfile:
    #     wfile.write(columns)
    #     for line in megafile:
    #         wfile.write(line)

    # ===== PHASE II ======

    mpath = r'C:\Users\gparrish\Desktop\mfile_out\megafile.csv'
    outp = r'C:\Users\gparrish\Desktop\mfile_out\\florida_csvs'

    florida_separate(mpath, outp)