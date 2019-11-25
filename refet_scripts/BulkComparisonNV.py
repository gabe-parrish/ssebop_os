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
from matplotlib import pyplot as plt
# ============= standard library imports ========================
from utils.os_utils import windows_path_fix
from SEEBop_os.raster_utils import gridmet_eto_reader
from ETref_tools.dataframe_calc_daily_ETr import metdata_df_uniformat, calc_daily_ETo_uniformat
from ETref_tools.metdata_preprocessor import  dri_preprocess

"""Here we compare a bunch of extracted (see BulkComparisonNV_GM_extract) DRI agrimet sites in Nevada to
 Extracted Gridmet"""

DRI_gridmet_root = r'Z:\Users\Gabe\refET\DRI_Agrimet_GridMet'
DRI_agrimet_root = r'Z:\Users\Gabe\refET\DRI_Agrimet_Metfiles'

shape = r'Z:\Users\Gabe\refET\refET_geo_files\DRI_agrimet_sites.shp'

output_ = r'Z:\Users\Gabe\refET\DRI_test'

metpaths = []
filenames = []
for f in os.listdir(DRI_agrimet_root):
    # getting the paths to files
    gm_metpath = os.path.join(DRI_agrimet_root, f)
    metpaths.append(gm_metpath)
    # get the filename
    fn = f.split('.')[0]
    filenames.append(fn)

print('metpaths and filenames \n', metpaths , '\n', filenames)

gridmet_path = []
agrimet_path = []
common_names = []
for mp, fn in zip(metpaths, filenames):
    print(mp)

    for gridmet_f in os.listdir(DRI_gridmet_root):
        # print(gridmet_f)
        # print('fn:', fn)
        if fn in gridmet_f and fn == 'Sand Spring Valley':
            print('fn:', fn)
            print('gmp:', gridmet_f)
            gmp = os.path.join(DRI_gridmet_root, gridmet_f)
            gridmet_path.append(gmp)
            agrimet_path.append(mp)
            common_names.append(fn)

print(agrimet_path, '\n', gridmet_path, '\n', common_names)
# read in the corresponding DRI file and the gridmet file.
for mp, gmp, cn in zip(metpaths, gridmet_path, common_names):
    # print(gmp)
    gm = gridmet_eto_reader(gridmet_eto_loc=gmp, smoothing=False)
    lon = gm['Lon'].tolist()[0]
    lat = gm['Lat'].tolist()[0]
    lonlat = (lon, lat)
    print('lonlat: ', lonlat)
    meters_abv_sl = gm['elevation_m'].tolist()[0]
    print(meters_abv_sl, '\n sealevel')


    print('gm head\n', gm.columns)

    # smoothing is false because we want to aggregate so keep original data
    m_df = dri_preprocess(mp)

    # uniformat to format the DF (this df is in the correct format, but we do it anyway for propriety)
    m_df = metdata_df_uniformat(m_df, max_air='max_air_temp', min_air='min_air_temp', avg_air='mean_air_temp',
                                  solar='Solar',
                                  ppt='precip', maxrelhum='max_rel_hum', minrelhum='min_rel_hum',
                                  avgrelhum='mean_rel_hum',
                                  sc_wind_mg='aveSpeed', doy='DOY')
    # calculate Rogers Spring ETo
    m_df = calc_daily_ETo_uniformat(dfr=m_df, meters_abv_sealevel=meters_abv_sl, lonlat=lonlat, smoothing=False)

    plt.plot(m_df.index, m_df.ETo)
    plt.show()

    # 1) Aggregate to Monthly
    m_df_monthly = m_df.resample('1M').sum()
    gm_monthly = gm.resample('1M').sum()
    # === dates ===
    m_month = m_df_monthly.index
    gm_month = gm_monthly.index
    # === values ===
    m_vals_month = m_df_monthly['ETo']
    gm_vals_month = gm_monthly['ETo']

    # 2) Aggregate to Yearly
    m_df_yearly = m_df.resample('1A').sum()
    gm_yearly = gm.resample('1A').sum()
    # === dates ===
    m_year = m_df_yearly.index
    gm_year = gm_yearly.index
    # === values ===
    m_vals_year = m_df_yearly['ETo']
    gm_vals_year = gm_yearly['ETo']


    # 3) Apply Smoothing
    m_df_smoothed = m_df.rolling('10D').mean()
    gm_smoothed = gm.rolling('10D').mean()
    # === dates ===
    m_smooth = m_df_smoothed.index
    gm_smooth = gm_smoothed.index
    # === values ===
    m_vals_smooth = m_df_smoothed['ETo']
    gm_vals_smooth = gm_smoothed['ETo']


    # 4) Plot Monthly, Yearly, Smoothing

    fig, ax = plt.subplots(4, 1, sharex=True)

    ax[0].plot(m_month, m_vals_month, color='green', label='Agrimet ETo (mm)')
    ax[0].scatter(m_month, m_vals_month, color='green', facecolor='none')
    ax[0].plot(gm_month, gm_vals_month, color='black', label='GRIDMET ETo (mm)')
    ax[0].scatter(gm_month, gm_vals_month, color='black', facecolor='none')
    ax[0].set(xlabel='Date', ylabel='mm of ETo',
              title='{} Monthly Nevada Reference Vs Gridmet'.format(cn))

    ax[1].plot(m_year, m_vals_year, color='green', label='Agrimet ETo (mm)')
    ax[1].scatter(m_year, m_vals_year, color='green', facecolor='none')
    ax[1].plot(gm_year, gm_vals_year, color='black', label='GRIDMET ETo (mm)')
    ax[1].scatter(gm_year, gm_vals_year, color='black', facecolor='none')
    ax[1].set(xlabel='Date', ylabel='mm of ETo',
              title='{} Yearly Nevada Reference Vs Gridmet'.format(cn))

    ax[2].plot(m_smooth, m_vals_smooth, color='green', label='Agrimet ETo (mm)')
    ax[2].scatter(m_smooth, m_vals_smooth, color='green', facecolor='none')
    ax[2].plot(gm_smooth, gm_vals_smooth, color='black', label='GRIDMET ETo (mm)')
    ax[2].scatter(gm_smooth, gm_vals_smooth, color='black', facecolor='none')
    ax[2].set(xlabel='Date', ylabel='mm of ETo',
              title='{} Smoothed Daily Nevada Reference Vs Gridmet'.format(cn))



    ax[3].plot(m_df.index, m_df.ETo, color='green', label='Sand Spring ETo not smooth')
    ax[3].plot(gm.index, gm.ETo)
    ax[3].set(xlabel='Date', ylabel='mm ETo')

    ax[0].grid()
    ax[1].grid()
    ax[2].grid()
    ax[3].grid()
    # ax[3].grid()

    # plt.ylim((0, 16))
    plt.tight_layout()
    plt.legend()
    plt.show()


