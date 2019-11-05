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
from ETref_tools.metdata_preprocessor import jornada_preprocess, leyendecker_preprocess, airport_preprocess, uscrn_preprocess, uscrn_subhourly

"""This script uses other functions to get daily ETr from Leyendecker II met station in Las Cruces and the Jornada
 weather station at the Jornada LTER near las cruces and plots the two timeseries for comparison"""

pd.plotting.register_matplotlib_converters()

# ================= Leyendecker II =================

mpath = r'Z:\Users\Gabe\refET\met_datasets\central_NV\Mercury_NV_USCRN_5min.txt'
header = r'Z:\Users\Gabe\refET\met_datasets\USCRN_5min_headers'

# uscrn_preprocess(metpath=mpath, header_txt=header)
uscrn_df = uscrn_subhourly(metpath=mpath, header_txt=header)

# === other constants needed ===
# 1) Height of windspeed instrument (its 1.5m but we already did the adjustment)
# 2) Elevation above sealevel
m_abv_sl = 1155  # (Sourced from Wikipedia)
# 3) Lon Lat location (must be a geographic coordinate system?)
lonlat = (-116.02, 36.62)
# {'MAX_AIR': np.max,'MIN_AIR': np.min, 'AIR_TEMPERATURE': np.mean,
#                                         'SOLAR_MJ_FLUX': np.sum, 'PRECIPITATION': np.sum, 'MAX_REL_HUM': np.max,
#                                         'MIN_REL_HUM': np.min, 'RELATIVE_HUMIDITY': np.mean, 'WIND_2': np.mean,
#                                         'DOY': np.min}
#4) Format the columns of the dataframe to a standard for ETo calculation
uscrn_uniformat = metdata_df_uniformat(df=uscrn_df, max_air='MAX_AIR', min_air='MIN_AIR', avg_air='AIR_TEMPERATURE',
                               solar='SOLAR_MJ_FLUX', ppt='PRECIPITATION', maxrelhum='MAX_REL_HUM',
                               minrelhum='MIN_REL_HUM', avgrelhum='RELATIVE_HUMIDITY', sc_wind_mg='WIND_2', doy='DOY')

#5) with the new standardized dataframe calculate ETo
ld_ETo = calc_daily_ETo_uniformat(dfr=uscrn_uniformat, meters_abv_sealevel=m_abv_sl, lonlat=lonlat)
