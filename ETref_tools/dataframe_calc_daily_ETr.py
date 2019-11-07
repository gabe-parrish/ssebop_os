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
import pandas as pd
import matplotlib.pyplot as plt
# ============= standard library imports ========================
from ETref_tools.refet_functions import *

"""
This script supports calculating daily reference ET from a pandas dataframe containing daily meteorological parameters.

The functionality should include (eventually)

1) support for renaming df columns to a standard format.
2) support for gapfilling potential missing data (this maybe can be left up to metdata_preprocessor.py)
3) accept user input for geography, elevation, wind speed height etc for the weather station.
3) calling "refet_functions.py" - functions to calculate ETo and intermediate parameters.
--- GELP 10/2/2019 ---
"""

def metdata_df_uniformat(df, max_air, min_air, avg_air, solar, ppt, maxrelhum, minrelhum, avgrelhum, sc_wind_mg, doy):
    """
    A tool for standardizing meteorological data from a dataframe. All columns of the dataframe must be present but need
    not be exlusive. All the units must be correct before this function is used.

    :param df: a date-indexed dataframe of appropriately aggregated daily meteorological variables
    :param max_air: (string) df column name of maximum daily air temperature Celsius
    :param min_air: (string) df column name of minimum daily air temperature Celsius
    :param avg_air: (string) df column name of average daily air temperature Celsius
    :param solar: (string) df column name of Total daily solar radiation in MJ/m^2
    :param ppt: (string) df column name of total daily precipitation in mm
    :param maxrelhum: (string) df column name of maximum daily relative humidity as a %
    :param minrelhum: (string) df column name of minimum daily relative humidity as a %
    :param avgrelhum: (string) df column name of average daily relative humidity as a %
    :param sc_wind_mg: (string) df column name of scalar wind magnitude in m/s
    :param doy: (string) df column name of day of year 1 - 365/366
    :return: (string) df column name of a date-indexed dataframe with uniform column headings for calculation of Reference ET
    """
    new_df = pd.DataFrame()
    # change the essential column headings
    new_df['MaxAir'] = df[max_air]
    new_df['MinAir'] = df[min_air]
    new_df['AvgAir'] = df[avg_air]
    new_df['Solar'] = df[solar]
    new_df['Ppt'] = df[ppt]
    new_df['MaxRelHum'] = df[maxrelhum]
    new_df['MinRelHum'] = df[minrelhum]
    new_df['RelHum'] = df[avgrelhum]
    new_df['ScWndMg'] = df[sc_wind_mg]
    new_df['doy'] = df[doy]

    new_df.set_index(df.index)
    print('index used \n {}'.format(df.index))

    return new_df
    # {'MaxAir': np.max, 'MinAir': np.min, 'AvgAir': np.mean, 'Solar': np.sum,
    #                                    'Ppt': np.sum, 'MaxRelHum':np.max, 'MinRelHum':np.min, 'RelHum': np.mean,
    #                                     'ScWndMg': np.mean, '5cmSoil':np.mean, '20cmSoil': np.mean, 'doy': np.median}

def calc_daily_ETo_uniformat(dfr, meters_abv_sealevel, lonlat, smoothing=False):
    """ETo after 'Step by Step Calculation of the Penman-Monteith Evapotranspiration
     (FAO-56 Method)' by Zotarelli et al"""


    #  # TODO - make options to deal with situations where a dataset may be missing e.g. max and min rel humidity...

    # # Step 1 Mean daily temp
    # # return mean temp in metric units
    # Step 1 pandas mode
    print('Step 1')
    dfr['Tmean'] = dfr.apply(lambda x: calc_Tmean(Tmax=x['MaxAir'], Tmin=x['MinAir'], metric=True), axis=1)

    # step 2 convert solar rad from watts to MJ (skip for this dataset)

    # step 3 get average daily wind speed in m/s at 2 m by adjusting (for now assume wind speed is at 2m)
    # wind speed is 'ScWndMg' as in: Scalar Wind Magnitude

    print('step 4')
    # step 4 - Slope of saturation vapor pressure
    dfr['delta'] = dfr.apply(lambda x: calc_delta(Tmean=x['Tmean']), axis=1)

    print('step 5')
    # step 5 - Calculate atmospheric pressure
    dfr['atmP'] = dfr.apply(lambda x: calc_atmP(z=meters_abv_sealevel, metric=True), axis=1)

    print('step 6')
    # step 6 - calculate the psychrometric constant
    dfr['gamma'] = dfr.apply(lambda x: calc_psych_const(p_atm=x['atmP']), axis=1)

    print('step 7')  # TODO - why do the first values come out as NaN?
    # step 7 - Calculate the delta term of PM (Auxiliary term for Radiation)
    dfr['DT'] = dfr.apply(lambda x: calc_DT(delta=x['delta'], psych_const=x['gamma'], u2_vel=x['ScWndMg']), axis=1)

    print('step 8')
    # step 8 - calculate psi term PT for PM equation (Auxiliary calc for wind term)
    dfr['PT'] = dfr.apply(lambda x: calc_PT(delta=x['delta'], psych_const=x['gamma'], u2_vel=x['ScWndMg']), axis=1)

    print('step 9')
    # step 9 - calculate temp term (TT) for PM equation (Aux calc for wind term)
    dfr['TT'] = dfr.apply(lambda x: calc_TT(Tmean=x['Tmean'], u2_vel=x['ScWndMg']), axis=1)

    print('step 10 - EPIC!')
    # step 10 - Mean saturation vapor pressure from air Temp (this is kinda complicated since the function outputs a tuple)
    # example from: https://stackoverflow.com/questions/52876635/pandas-apply-tuple-unpack-function-on-multiple-columns
    # make a separate dataframe from the function and set index to be the same (Pretty Crazy)
    e_df = pd.DataFrame(dfr.apply(lambda x: calc_sat_vp(Tmax=x['MaxAir'], Tmin=x['MinAir']), 1).to_list(),
                        columns=['e_sat', 'e_tmax', 'e_tmin'], index=dfr.index)
    # concatenate the dataframes along the column axis
    dfr = pd.concat([dfr, e_df], axis=1)
    # print('test the resulting DF')
    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    #     print(jdfr.head(10))

    print('step 11')
    # step 11 - actual vapor pressure from relative humidity
    dfr['e_a'] = dfr.apply(lambda x: calc_e_actual(rh_max=x['MaxRelHum'], rh_min=x['MinRelHum'], e_tmax=x['e_tmax'],
                                                   e_tmin=x['e_tmin']), axis=1)
    # ## Optional functions
    # # if you only have a max relative humidity
    # jdfr['e_a'] = jdfr.apply(lambda x: calc_e_actual(rh_max=x['MaxRelHum'], e_tmax=x['e_tmax'], e_tmin=x['e_tmin'], rhmax_only=True), axis=1)
    # # if you only have mean relative humidity
    # jdfr['e_a'] = jdfr.apply(lambda x: calc_e_actual(e_tmax=x['e_tmax'], e_tmin=x['e_tmin'], rh_mean=x['RelHum']), axis=1)

    # === Calculating Radiation Terms ===

    print('step 12')
    # step 12 - calculate relative earth sun distance and solar declination
    dfr['solar_declination'] = dfr.apply(lambda x: calc_sol_decl(julian_date=x['doy']), axis=1)
    dfr['dr'] = dfr.apply(lambda x: calc_dr(julian_date=x['doy']), axis=1)

    print('step 13')
    # step 13 - convert latitude from degrees to radians
    dfr['lat_rad'] = dfr.apply(lambda x: conv_lat_deg2rad(degrees_lat=lonlat[1]), axis=1)

    print('step 14')
    # step 14 - sunset hour angle
    dfr['omega_sun'] = dfr.apply(lambda x: calc_sunsethour_angle(lat_rad=x['lat_rad'],
                                                                 sol_decl=x['solar_declination']), axis=1)

    print('step 15')
    # step 15 - extraterrestrial radiation
    dfr['Ra'] = dfr.apply(lambda x: calc_Ra(dr=x['dr'], omega_sun=x['omega_sun'],
                                            lat_rad=x['lat_rad'], sol_decl=x['solar_declination']), axis=1)
    print('step 16')
    # step 16 - clear sky radiation
    dfr['Rso'] = dfr.apply(lambda x: calc_Rso(z=meters_abv_sealevel, Ra=x['Ra']), axis=1)

    print('step 17')
    # step 17 Net shortwave -
    dfr['Rns'] = dfr.apply(lambda x: calc_Rns(Rs=x['Solar']), axis=1)

    print('step 18')
    # step 18 Net longwave
    dfr['Rnl'] = dfr.apply(lambda x: calc_Rnl(Tmax=x['MaxAir'], Tmin=x['MinAir'], e_actual=x['e_a'],
                                              Rs=x['Solar'], Rso=x['Rso'], Ra=x['Ra']), axis=1)

    print('step 19')
    # step 19 Net Rad
    dfr['Rn'] = dfr.apply(lambda x: calc_Rn(Rns=x['Rns'], Rnl=x['Rnl'], mm=True), axis=1)

    print('calculate ETo')
    # calc ETo

    # radiation term
    dfr['ETrad'] = dfr['DT'] * dfr['Rn']
    # wind term
    dfr['ETwind'] = dfr['PT'] * dfr['TT'] * (dfr['e_sat'] - dfr['e_a'])
    # short crop refET
    dfr['ETo'] = dfr['ETwind'] + dfr['ETrad']

    if smoothing:

        print("'smoothing' set to True: Applying a 5-day moving average to smooth the data")
        print("some columns will now become meaningless like DOY. If such behaviour is not desired recode smoothing"
              " using .agg('VAR': np.func)")
        # dfr = dfr.resample('5D').mean()

        dfr = dfr.rolling('10D').mean()


    return dfr