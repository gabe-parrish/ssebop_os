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
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
# ============= standard library imports ========================
from utils.os_utils import windows_path_fix
from ETref_tools.refet_functions import *
from ETref_tools.dataframe_calc_daily_ETr import metdata_df_uniformat, calc_daily_ETo_uniformat

register_matplotlib_converters()

jornada_metpath = windows_path_fix(r'Z:\Users\Gabe\refET\jupyter_nbs\weather_station_data\Jornada_126002_lter_weather_station_hourly_data\wshour12.dat')

with open(jornada_metpath, 'r') as rfile:

    rows = [line for line in rfile]

    data_rows = []
    for r in rows:
        # print(repr(r))

        space_free = r.strip(' ')
        no_return = space_free.strip('\n')

        line_lst = no_return.split(' ')
        # print(repr(line_lst))

        line_lst = [l for l in line_lst if l != '' ]
        print(line_lst)

        if len(line_lst) == 41:
            data_rows.append(line_lst)


    print(len(data_rows))

    rawdata = data_rows[1:]
    data_cols = data_rows[0]

    jdf = pd.DataFrame(data=rawdata, columns=data_cols)



    print(jdf.head())

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
                                   'Ppt': np.sum, 'MaxRelHum':np.max, 'MinRelHum':np.min, 'RelHum': np.mean,
                                   'ScWndMg': np.mean, '5cmSoil':np.mean, '20cmSoil': np.mean, 'doy': np.median})

    # jdf.to_csv(windows_path_fix(r'C:\Users\gparrish\Desktop\jdf_after_jdfr_creation.csv'))
    # to dislplay all columns when printing in terminal
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print('essential df \n', jdfr.head(10))

    # uniformat to format the DF (this df is in the correct format, but we do it anyway for propriety)
    jdfr = metdata_df_uniformat(jdfr, max_air='MaxAir', min_air='MinAir', avg_air='AvgAir', solar='Solar',
                                        ppt='Ppt', maxrelhum='MaxRelHum', minrelhum='MinRelHum', avgrelhum='RelHum',
                                        sc_wind_mg='ScWndMg', doy='doy')
    # jdfr.to_csv(windows_path_fix(r'C:\Users\gparrish\Desktop\uniformattest2.csv'))
    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    #     print('essential df \n', jdfr.head(10))


    # do the daily ref ET calculation
    print('doing ET')
    # --- Constants ----
    # 1) Height of windspeed instrument
    # ---> (no information so we assume 2m)
    # 2) Elevation above sealevel
    meters_abv_sl = 1360 # In FEET: 4460 feet
    # 3) Lon Lat location (must be a geographic coordinate system?)
    lonlat = (-106.797, 32.521) #  Lat DMS 106  47  50 , Lon DMS 32  31  17,

    # testing uniformat
    calc_daily_ETo_uniformat(dfr=jdfr, meters_abv_sealevel=meters_abv_sl, lonlat=lonlat)

    # # # Step 1 Mean daily temp
    # # # return mean temp in metric units
    # # Step 1 pandas mode
    # print('Step 1')
    # jdfr['Tmean'] = jdf.apply(lambda x: calc_Tmean(Tmax=x['MaxAir'], Tmin=x['MinAir'], metric=True), axis=1)
    #
    # # step 2 convert solar rad from watts to meters (skip for this dataset)
    #
    # # step 3 get average daily wind speed in m/s at 2 m by adjusting (for now assume wind speed is at 2m)
    # # wind speed is 'ScWndMg' as in: Scalar Wind Magnitude
    #
    # print('step 4')
    # # step 4 - Slope of saturation vapor pressure
    # jdfr['delta'] = jdfr.apply(lambda x: calc_delta(Tmean=x['Tmean']), axis=1)
    #
    # print('step 5')
    # # step 5 - Calculate atmospheric pressure
    # jdfr['atmP'] = jdfr.apply(lambda x: calc_atmP(z=meters_abv_sl, metric=True), axis=1)
    #
    # print('step 6')
    # # step 6 - calculate the psychrometric constant
    # jdfr['gamma'] = jdfr.apply(lambda x: calc_psych_const(p_atm=x['atmP']), axis=1)
    #
    # print('step 7') # TODO - why do the first values come out as NaN?
    # # step 7 - Calculate the delta term of PM (Auxiliary term for Radiation)
    # jdfr['DT'] = jdfr.apply(lambda x: calc_DT(delta=x['delta'], psych_const=x['gamma'], u2_vel=x['ScWndMg']), axis=1)
    #
    # print('step 8')
    # # step 8 - calculate psi term PT for PM equation (Auxiliary calc for wind term)
    # jdfr['PT'] = jdfr.apply(lambda x: calc_PT(delta=x['delta'], psych_const=x['gamma'], u2_vel=x['ScWndMg']), axis=1)
    #
    # print('step 9')
    # # step 9 - calculate temp term (TT) for PM equation (Aux calc for wind term)
    # jdfr['TT'] = jdfr.apply(lambda x: calc_TT(Tmean=x['Tmean'], u2_vel=x['ScWndMg']), axis=1)
    #
    # print('step 10 - EPIC!')
    # # step 10 - Mean saturation vapor pressure from air Temp (this is kinda complicated since the function outputs a tuple)
    # # example from: https://stackoverflow.com/questions/52876635/pandas-apply-tuple-unpack-function-on-multiple-columns
    # # make a separate dataframe from the function and set index to be the same (Pretty Crazy)
    # e_df = pd.DataFrame(jdfr.apply(lambda x: calc_sat_vp(Tmax=x['MaxAir'], Tmin=x['MinAir']), 1).to_list(), columns=['e_sat', 'e_tmax', 'e_tmin'], index=jdfr.index)
    # # concatenate the dataframes along the column axis
    # jdfr = pd.concat([jdfr, e_df], axis=1)
    # # print('test the resulting DF')
    # # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    # #     print(jdfr.head(10))
    #
    # print('step 11')
    # # step 11 - actual vapor pressure from relative humidity
    # jdfr['e_a'] = jdfr.apply(lambda x: calc_e_actual(rh_max=x['MaxRelHum'], rh_min=x['MinRelHum'], e_tmax=x['e_tmax'],
    #                                                  e_tmin=x['e_tmin']), axis=1)
    # # ## Optional functions
    # # # if you only have a max relative humidity
    # # jdfr['e_a'] = jdfr.apply(lambda x: calc_e_actual(rh_max=x['MaxRelHum'], e_tmax=x['e_tmax'], e_tmin=x['e_tmin'], rhmax_only=True), axis=1)
    # # # if you only have mean relative humidity
    # # jdfr['e_a'] = jdfr.apply(lambda x: calc_e_actual(e_tmax=x['e_tmax'], e_tmin=x['e_tmin'], rh_mean=x['RelHum']), axis=1)
    #
    #
    # # === Calculating Radiation Terms ===
    #
    # print('step 12')
    # # step 12 - calculate relative earth sun distance and solar declination
    # jdfr['solar_declination'] = jdfr.apply(lambda x: calc_sol_decl(julian_date=x['doy']), axis=1)
    # jdfr['dr'] = jdfr.apply(lambda x: calc_dr(julian_date=x['doy']), axis=1)
    #
    # print('step 13')
    # # step 13 - convert latitude from degrees to radians
    # jdfr['lat_rad'] = jdfr.apply(lambda x: conv_lat_deg2rad(degrees_lat=lonlat[1]), axis=1)
    #
    # print('step 14')
    # # step 14 - sunset hour angle
    # jdfr['omega_sun'] = jdfr.apply(lambda x: calc_sunsethour_angle(lat_rad=x['lat_rad'],
    #                                                                sol_decl=x['solar_declination']), axis=1)
    #
    # print('step 15')
    # # step 15 - extraterrestrial radiation
    # jdfr['Ra'] = jdfr.apply(lambda x: calc_Ra(dr=x['dr'], omega_sun=x['omega_sun'],
    #                                           lat_rad=x['lat_rad'], sol_decl=x['solar_declination']), axis=1)
    # print('step 16')
    # # step 16 - clear sky radiation
    # jdfr['Rso'] = jdfr.apply(lambda x: calc_Rso(z=meters_abv_sl, Ra=x['Ra']), axis=1)
    #
    # print('step 17')
    # # step 17 Net shortwave -
    # jdfr['Rns'] = jdfr.apply(lambda x: calc_Rns(Rs=x['Solar']), axis=1)
    #
    # print('step 18')
    # # step 18 Net longwave
    # jdfr['Rnl'] = jdfr.apply(lambda x: calc_Rnl(Tmax=x['MaxAir'], Tmin=x['MinAir'], e_actual=x['e_a'],
    #                                             Rs=x['Solar'], Rso=x['Rso'], Ra=x['Ra']), axis=1)
    #
    # print('step 19')
    # # step 19 Net Rad
    # jdfr['Rn'] = jdfr.apply(lambda x: calc_Rn(Rns=x['Rns'], Rnl=x['Rnl'], mm=True), axis=1)
    #
    # print('calculate ETo')
    # # calc ETo
    #
    # # radiation term
    # jdfr['ETrad'] = jdfr['DT'] * jdfr['Rn']
    # # wind term
    # jdfr['ETwind'] = jdfr['PT'] * jdfr['TT'] * (jdfr['e_sat'] - jdfr['e_a'])
    # # short crop refET
    # jdfr['ETo'] = jdfr['ETwind'] + jdfr['ETrad']
    #
    # # # test the dataframe (ETo seems tooo high)
    # # jdfr.to_csv(windows_path_fix(r'C:\Users\gparrish\Desktop\jdfr.csv'))
    #
    # # plot timeseries of ETo
    # print('plotting ETo')
    #
    # # plotting Variables
    # ETo = jdfr['ETo']
    # # day_of_year = jdfr['doy']
    # j_date = jdfr.index
    #
    # fig, ax = plt.subplots()
    # ax.plot(j_date, ETo, color='green', label='Jornada ETo in mm')
    # ax.scatter(j_date, ETo, color='green', facecolor='none')
    #
    # # ax.plot(w2dates, w2dbgs, color='blue', label='SampleWell-2 Radium Springs NM')
    # # ax.plot(w3dates, w3dbgs, color='orange', label='SampleWell-3 Las Cruces NM')
    # # ax.plot(w4dates, w4dbgs, color='red', label='SampleWell-4 Anthony Tx')
    #
    # ax.set(xlabel='Date', ylabel='mm of ETo',
    #        title='Jornada LTER Weather Station ETo and Metdata - 2012')
    # ax.grid()
    #
    # plt.ylim((0, 16))
    # plt.legend()
    # plt.show()


    # # And old - school way of calculating it
    # A = delta * (Rn)
    #
    # # Figure out why you're getting e-sat wrong
    # print('e actual', e_a, 'E_SAT', e_sat)
    # B = gamma * (900 / (Tmean + 273)) * u2 * (e_sat - e_a)
    #
    # C = gamma * (1 + (0.34 * u2))
    #
    # print('a', A, 'b', B, 'c', C, 'delta', delta)
    #
    # print('numerator', A + B)
    # print('denominator', delta + C)
    #
    # ETo = (A + B) / (delta + C)
    # print('O.G. ETo', ETo)