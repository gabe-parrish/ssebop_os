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
from matplotlib import pyplot as plt
from datetime import datetime
# ============= standard library imports ========================
from ETref_tools.dataframe_calc_daily_ETr import metdata_df_uniformat, calc_daily_ETo_uniformat
from ETref_tools.metdata_preprocessor import dri_preprocess
from SEEBop_os.raster_utils import gridmet_eto_reader


"""In this script I'm comparing how different my ETo calculation based on daily average values is different from DRIs ET supposedly calculated from hourly data"""

DRI_testfile = r'C:\Users\gparrish\Desktop\DRI_2011_test'
SSV = r'Z:\Users\Gabe\refET\DRI_Agrimet_Metfiles\Sand Spring Valley.txt'
gridmet_ssv = r'C:\Users\gparrish\Desktop\gridmet_test.csv'

# ================= Sand Spring Valley (DRI - Agrimet/Blankenau) =================
# --- Constants ----
# 1) Height of windspeed instrument
# ---> (no information so we assume 2m)
# 2) Elevation above sealevel
meters_abv_sl = 1466
# 3) Lon Lat location (must be a geographic coordinate system?)
lonlat = (-115.7975, 37.646667)

# sand_spring = windows_path_fix(r'Z:\Users\Gabe\refET\met_datasets\central_NV\Sand_Spring_Valley_NV_Agrimet_DRI.txt')
sand_spring = r'Z:\Users\Gabe\refET\DRI_Agrimet_Metfiles\Sand Spring Valley.txt'
sand_df = dri_preprocess(sand_spring)

# uniformat to format the DF (this df is in the correct format, but we do it anyway for propriety)
sand_df = metdata_df_uniformat(sand_df, max_air='max_air_temp', min_air='min_air_temp', avg_air='mean_air_temp', solar='Solar',
                               ppt='precip', maxrelhum='max_rel_hum', minrelhum='min_rel_hum', avgrelhum='mean_rel_hum',
                               sc_wind_mg='aveSpeed', doy='DOY')
# calculate sand spring ETo
sand_df = calc_daily_ETo_uniformat(dfr=sand_df, meters_abv_sealevel=meters_abv_sl, lonlat=lonlat, smoothing=False)

l_ETo = sand_df['ETo']
l_date = sand_df.index

# ================= Sand Spring Valley DRI Calculated ET =================

et = []
counts = []
datet = []

with open(DRI_testfile, 'r') as rfile:
    count = 0
    for i in rfile:
        counts.append(count)
        i = i.strip('\n')
        line = i.split(' ')
        line = [i.strip(' ') for i in line]
        line = [i for i in line if i != '']
        print(line)
        # using ASCE standard ET
        et.append(float(line[-3]))
        # # using Penman ET
        # et.append(float(line[-2]))
        datet.append(datetime.strptime(line[0], '%m/%d/%Y'))
        count += 1

# ================= GRIDMET ETo for Sand Spring Valley DRI =========

gridmet_df = gridmet_eto_reader(gridmet_eto_loc=gridmet_ssv, smoothing=False)

# ================= Compare Parrish and DRI ref et =================
#
# TODO - ETo or ETr?

d = {'et': et, 'count': counts, 'date': datet}

df = pd.DataFrame(d, columns=['et', 'count', 'date'])
df.set_index('date', inplace=True)




# df = df.resample('1M').sum()

plt.plot(df.index, df.et, color='black', label='DRI ASCE ET')
plt.plot(l_date, l_ETo, color='green', label='Gabe')
plt.plot(gridmet_df.index, gridmet_df['ETo'], color='blue', label='GRIDMET')
# plt.scatter(counts, et, facecolor='none')
plt.title('Sand Spring Valley DRI Test')
plt.legend()
plt.show()

# Compare Parrish and DRI ref ET on monthly timestep
df = df.resample('1M').sum()
sand_df = sand_df.resample('1M').sum()
gridmet_df = gridmet_df.resample('1M').sum()

# Also, plot the percent difference alongside
# get percent difference of gridmet and DRI
pdiff = (abs(sand_df['ETo'] - df.et) / df.et) * 100
print(pdiff)

# plot the percent difference between ME and DRI
pdiff_GM = (abs(gridmet_df['ETo'] - df.et) / df.et) * 100

fig, ax = plt.subplots(2, 1, sharex=True)

ax[0].plot(df.index, df.et, color='black', label='DRI ASCE RefET')
ax[0].plot(sand_df.index, sand_df.ETo, color='green', label='Gabe')
ax[0].plot(gridmet_df.index, gridmet_df.ETo, color='blue', label='Gridmet ETo')
ax[0].set(xlabel='Date', ylabel='mm of ETo',
              title='Monthly Cumulative Station ETo Sand Spring Valley')
ax[0].legend()

ax[1].plot(pdiff.index, pdiff, label='percent difference Gabe-DRI')
ax[1].plot(pdiff_GM.index, pdiff_GM, label='percent difference Gridmet-DRI')
ax[1].legend()
ax[1].set(xlabel='Date', ylabel='% error assuming DRI is correct',
              title='Monthly Cumulative Station ETo % difference Sand Spring Valley')


# TODO - Calculate ET percent difference


plt.legend()
plt.show()