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
import matplotlib.pyplot as plt
# ============= standard library imports ========================
from utils.os_utils import windows_path_fix
from ETref_tools.dataframe_calc_daily_ETr import metdata_df_uniformat, calc_daily_ETo_uniformat
from ETref_tools.refet_functions import conv_F_to_C, conv_mph_to_mps, conv_in_to_mm, conv_f_to_m
from ETref_tools.metdata_preprocessor import jornada_preprocess

"""This script uses other functions to get daily ETr from Leyendecker II met station in Las Cruces and the Jornada
 weather station at the Jornada LTER near las cruces and plots the two timeseries for comparison"""

pd.plotting.register_matplotlib_converters()

# ================= Leyendecker II =================

ld_csv = pd.read_csv(r'Z:\Users\Gabe\refET\jupyter_nbs\weather_station_data\leyendecker_2012_daily.csv')

# === other constants needed ===
# 1) Height of windspeed instrument (we assume 2m for this instrument so we don't adjust)
# 2) Elevation above sealevel
feet_abv_sl = 3858.46
m_abv_sl = conv_f_to_m(foot_lenght=feet_abv_sl)
# 3) Lon Lat location (must be a geographic coordinate system?)
lonlat = (-106.74, 32.20)

# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
#     print('essential df \n', ld_csv.head(10))

# === Now format the dataframe appropriately ===
# TODO - make the formatting it's own separate function in metdata_preprocessor
#1) julian date
# first make 'Date' into datetime
ld_csv['datetime'] = ld_csv.apply(lambda x: datetime.strptime(x['Date'], '%Y-%m-%d'), axis=1)
# then make the datetime into a day of year
ld_csv['doy'] = ld_csv.apply(lambda x: x['datetime'].timetuple().tm_yday, axis=1)
#
#2) Set the index to be a datetime
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
print('do we get here 1')
ld_csv['wind_mps'] = ld_csv.apply(lambda x: conv_mph_to_mps(mph=x['Mean Wind Speed (MPH)']), axis=1)
print(2)
# now precip
ld_csv['ppt'] = ld_csv.apply(lambda x: conv_in_to_mm(inches=x['Total Precipitation (in.)']), axis=1)

#4) Format the columns of the dataframe to a standard for ETo calculation
ldf_csv = metdata_df_uniformat(df=ld_csv, max_air='maxair', min_air='minair', avg_air='meanair',
                               solar='Total Solar Radiation (MJ/m^2)', ppt='ppt', maxrelhum='Max RH (%)',
                               minrelhum='Min RH (%)', avgrelhum='Mean RH (%)', sc_wind_mg='wind_mps', doy='doy')

#5) with the new standardized dataframe calculate ETo
ld_ETo = calc_daily_ETo_uniformat(dfr=ldf_csv, meters_abv_sealevel=m_abv_sl, lonlat=lonlat)


# ================= Jornada LTER =================
# --- Constants ----
# 1) Height of windspeed instrument
# ---> (no information so we assume 2m)
# 2) Elevation above sealevel
meters_abv_sl = 1360 # In FEET: 4460 feet
# 3) Lon Lat location (must be a geographic coordinate system?)
lonlat = (-106.797, 32.521) #  Lat DMS 106  47  50 , Lon DMS 32  31  17,

jornada_metpath = windows_path_fix(r'Z:\Users\Gabe\refET\jupyter_nbs\weather_station_data\Jornada_126002_lter_weather_station_hourly_data\wshour12.dat')

jdfr = jornada_preprocess(jornada_metpath=jornada_metpath)

# uniformat to format the DF (this df is in the correct format, but we do it anyway for propriety)
jdfr = metdata_df_uniformat(jdfr, max_air='MaxAir', min_air='MinAir', avg_air='AvgAir', solar='Solar',
                                    ppt='Ppt', maxrelhum='MaxRelHum', minrelhum='MinRelHum', avgrelhum='RelHum',
                                    sc_wind_mg='ScWndMg', doy='doy')
# calculate jornada ETo
jdfr = calc_daily_ETo_uniformat(dfr=jdfr, meters_abv_sealevel=meters_abv_sl, lonlat=lonlat)

# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
#     print('essential df \n', jdfr.head(10))

# ================= plot timeseries of ETo =================
print('plotting ETo')

# get plotting Variables from DFs
j_ETo = jdfr['ETo']
j_date = jdfr.index
l_ETo = ld_ETo['ETo']
l_date = ld_ETo.index

# plot
fig, ax = plt.subplots()
ax.plot(j_date, j_ETo, color='red', label='Jornada ETo (mm)')
ax.scatter(j_date, j_ETo, color='red', facecolor='none')
ax.plot(l_date, l_ETo, color='green', label='Leyendecker II ETo (mm)')
ax.scatter(l_date, l_ETo, color='green', facecolor='none')

ax.set(xlabel='Date', ylabel='mm of ETo',
       title='Jornada LTER ETo vs Leyendecker ETo - 2012')
ax.grid()

plt.ylim((0, 16))
plt.legend()
plt.show()