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
from ETref_tools.metdata_preprocessor import jornada_preprocess, leyendecker_preprocess, airport_preprocess, uscrn_subhourly, dri_preprocess

"""This script uses other functions to get daily ETo for 2 agricultural sites from the DRI network in NV and compares
 them with a nearby USCRN network for """

pd.plotting.register_matplotlib_converters()

# ================= Mercury NV =================

mpath = r'Z:\Users\Gabe\refET\met_datasets\central_NV\Mercury_NV_USCRN_5min.txt'
header = r'Z:\Users\Gabe\refET\met_datasets\USCRN_5min_headers'

# uscrn_preprocess(metpath=mpath, header_txt=header)
uscrn_df = uscrn_subhourly(metpath=mpath, header_txt=header)

# === other constants needed ===
# 1) Height of windspeed instrument (its 1.5m but we do the adjustment in metdata_preprocessor.py)
# 2) Elevation above sealevel
m_abv_sl = 1155  # (Sourced from Wikipedia)
# 3) Lon Lat location (must be a geographic coordinate system?)
lonlat = (-116.02, 36.62)

#4) Format the columns of the dataframe to a standard for ETo calculation
uscrn_uniformat = metdata_df_uniformat(df=uscrn_df, max_air='MAX_AIR', min_air='MIN_AIR', avg_air='AIR_TEMPERATURE',
                               solar='SOLAR_MJ_FLUX', ppt='PRECIPITATION', maxrelhum='MAX_REL_HUM',
                               minrelhum='MIN_REL_HUM', avgrelhum='RELATIVE_HUMIDITY', sc_wind_mg='WIND_2', doy='DOY')

#5) with the new standardized dataframe calculate ETo
uscrn_ETo = calc_daily_ETo_uniformat(dfr=uscrn_uniformat, meters_abv_sealevel=m_abv_sl, lonlat=lonlat, smoothing=True)


# ================= Sand Spring Valley (DRI - Agrimet/Blankenau) =================
# --- Constants ----
# 1) Height of windspeed instrument
# ---> (no information so we assume 2m)
# 2) Elevation above sealevel
meters_abv_sl = 1466
# 3) Lon Lat location (must be a geographic coordinate system?)
lonlat = (-115.7975, 37.646667)

sand_spring = windows_path_fix(r'Z:\Users\Gabe\refET\met_datasets\central_NV\Sand_Spring_Valley_NV_Agrimet_DRI.txt')

sand_df = dri_preprocess(sand_spring)

# uniformat to format the DF (this df is in the correct format, but we do it anyway for propriety)
sand_df = metdata_df_uniformat(sand_df, max_air='max_air_temp', min_air='min_air_temp', avg_air='mean_air_temp', solar='Solar',
                               ppt='precip', maxrelhum='max_rel_hum', minrelhum='min_rel_hum', avgrelhum='mean_rel_hum',
                               sc_wind_mg='aveSpeed', doy='DOY')
# calculate sand spring ETo
sand_df = calc_daily_ETo_uniformat(dfr=sand_df, meters_abv_sealevel=meters_abv_sl, lonlat=lonlat, smoothing=True)

# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
#     print('essential df \n', jdfr.head(10))

# ================= Rogers Spring NV (DRI Agrimet) =================
# --- Constants ----
# 1) Height of windspeed instrument
# ---> (no information so we assume 2m)
# 2) Elevation above sealevel
feet_abv_sl = 2260 # DRI website
m_abv_sl = conv_f_to_m(foot_lenght=feet_abv_sl)
# 3) Lon Lat location (must be a geographic coordinate system?)
lonlat = (-116.33083, 36.4783)

rog_spring = windows_path_fix(r'Z:\Users\Gabe\refET\met_datasets\central_NV\Rogers_Spring_NV_Agrimet_DRI.txt')

rog_df = dri_preprocess(rog_spring)

# uniformat to format the DF (this df is in the correct format, but we do it anyway for propriety)
rog_df = metdata_df_uniformat(rog_df, max_air='max_air_temp', min_air='min_air_temp', avg_air='mean_air_temp', solar='Solar',
                               ppt='precip', maxrelhum='max_rel_hum', minrelhum='min_rel_hum', avgrelhum='mean_rel_hum',
                               sc_wind_mg='aveSpeed', doy='DOY')
# calculate Rogers Spring ETo
rog_df = calc_daily_ETo_uniformat(dfr=rog_df, meters_abv_sealevel=meters_abv_sl, lonlat=lonlat, smoothing=True)
print('testing ppt \n', rog_df.Ppt)

# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
#     print('essential df \n', jdfr.head(10))


# ================= plot timeseries of ETo =================
print('plotting ETo')

# get plotting Variables from DFs
j_ETo = rog_df['ETo']
j_date = rog_df.index
l_ETo = sand_df['ETo']
l_date = sand_df.index
k_ETo = uscrn_ETo['ETo']
k_date = uscrn_ETo.index
# # === PRECIP ===
# j_precip = rog_df.Ppt
# l_precip = sand_df.Ppt
# k_precip = uscrn_df.Ppt



print(k_date)

# plot
fig, ax = plt.subplots(2, 1)
ax[0].plot(j_date, j_ETo, color='red', label='rogers spring ETo (mm)')
ax[0].scatter(j_date, j_ETo, color='red', facecolor='none')
ax[0].plot(l_date, l_ETo, color='green', label='sand spring ETo (mm)')
ax[0].scatter(l_date, l_ETo, color='green', facecolor='none')
ax[0].plot(k_date, k_ETo, color='brown', label='USCRN ETo Mercury NV (mm)')
ax[0].scatter(k_date, k_ETo, color='brown', facecolor='none')

ax[0].set(xlabel='Date', ylabel='mm of ETo',
       title='Central NV metstations comparison 2010')



# ax[1].plot(j_date, j_precip, color='red', label='rogers spring ppt (mm)')
# ax[1].plot(l_date, l_precip, color='green', label='sand spring ppt (mm)')
# ax[1].plot(k_date, k_precip, color='brown', label='USCRN Mercury NV ppt (mm)')


ax[0].grid()
ax[1].grid()

# plt.ylim((0, 16))
plt.tight_layout()
plt.legend()
plt.show()