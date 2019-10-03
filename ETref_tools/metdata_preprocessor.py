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

"""This script will include functions for preprocessing Meteorological data from a given source. The functions here 
are bespoke to the weather station raw data format that is downloaded. The data will then be used to calculate ETo
 using dataframe_calc_daily_ETr.py and the functions in refet_functions.py"""

def jornada_preprocess(jornada_metpath):
    """"""

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
            yr = date_lst[0]
            mo = date_lst[1]
            day = date_lst[2]

            # split up the minute and the hour from the HHMM string
            min_str = time_str[-2:]
            hr = time_str[:-2]

            # to pad zeros onto a digit in string formatting it has to be an actual int or float, not string.
            hr_int = int(hr)

            # cool new 'literal' formatting of variables directly into a string - python 3.6 and better.
            dt_str = f'{yr}-{mo}-{day}-{hr_int:02d}-{min_str}'

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
                dt_str = f'{yr}-{mo}-{day}-{hr_int:02d}-{min_str}'
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