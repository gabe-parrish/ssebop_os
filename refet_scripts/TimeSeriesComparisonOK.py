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
import datetime
import pandas as pd
import numpy as np
# ============= standard library imports ========================
from SEEBop_os.raster_utils import gridmet_eto_reader
from ETref_tools.dataframe_calc_daily_ETr import metdata_df_uniformat, calc_daily_ETo_uniformat
from ETref_tools.metdata_preprocessor import okmesonet_preprocess

"""Here we compare a bunch of extracted (see BulkComparisonOK_GM_extract) Oklahoma Mesonet sites to
 Extracted Gridmet via plotting with matplotlib. The script also outputs some files useful for analysis like accumulated
 monthly and yearly ETo. Prior to this script the function metdata_preprocesor.okmesonet_preprocess() in 
 metdata_preprocessor.py was used to separate files from a data request mega-file into individual files that can be 
 dealt with individually and that correspond to extracted GRIDMET files."""


gridmet_root = r'Z:\Users\Gabe\refET\OKMesonet_GridMet'
okmesonet_root = r'Z:\Users\Gabe\refET\OK_Mesonet'

yearly_output = r'Z:\Users\Gabe\refET\OKMESONET_GRIDMET_yearly_compare'
monthly_output = r'Z:\Users\Gabe\refET\OKMESONET_GRIDMET_monthly_compare'

fig_output = r'Z:\Users\Gabe\refET\ok_figs'

metpaths = []
ok_filenames = []
gmet_filenames = []

#================== A TIME SERIES COMPARISON =======================
for f in os.listdir(okmesonet_root):
    # getting the paths to files
    az_metpath = os.path.join(okmesonet_root, f)
    metpaths.append(az_metpath)
    # get the filename
    fn = f.split('.')[0]
    ok_filenames.append(fn)

for r in os.listdir(gridmet_root):
    gm_name = r.split('.')[0]
    gmet_filenames.append(gm_name)

# print('metpaths and filenames \n', metpaths, '\n', az_filenames, '\n', gmet_filenames)

gridmet_paths = []
azmet_paths = []
names_in_common = []

for ok_name in ok_filenames:
    if ok_name in gmet_filenames:
        print('ok name :', ok_name)
        gridmet_paths.append(os.path.join(gridmet_root, "{}.csv".format(ok_name)))
        azmet_paths.append(os.path.join(okmesonet_root, "{}.csv".format(ok_name)))
        names_in_common.append(ok_name)
for i, j in zip(gridmet_paths, azmet_paths):
    print('gm: ', i)
    print('ok: ', j)

#======================================================
#============= OK MEsonets'S OWN ETo ==================
#======================================================
# read in the corresponding DRI file and the gridmet file.
for gmp, mp, okn in zip(gridmet_paths, azmet_paths, names_in_common):
    print('TODAYS OK name {}'.format(okn))
    gm = gridmet_eto_reader(gridmet_eto_loc=gmp, smoothing=False)

    # get the longitude and latitude from the point shapefile of the AZMet tower locations that you used to extract...
    lon = gm['Lon'].tolist()[0]
    lat = gm['Lat'].tolist()[0]
    lonlat = (lon, lat)
    print('lonlat: ', lonlat)
    meters_abv_sl = gm['elevation_m'].tolist()[0]
    print(meters_abv_sl, '\n sealevel')

    m_df = okmesonet_preprocess(mp)



    # m_df['dt'] = m_df.apply(lambda x: datetime.strptime("{}-{:02d}-{:02d}".format(int(x['YEAR']), int(x['MONTH']), int(x['DAY'])), '%Y-%m-%d'), axis=1)
    # # set the index to the datetime IN place
    # m_df.set_index('dt', inplace=True)

    m_df['Year'] = m_df.apply(lambda x: int(x['YEAR']), axis=1)

    max_year = max(m_df['Year'].to_list())
    min_year = min(m_df['Year'].to_list())
    print(max_year, min_year)
    # we only want complete years as part of the data-set so get rid of 2020 (or the maximum year)...
    # ...and the earliest year in the dataset.
    m_df_complete_yrs = m_df[(m_df['Year'] != max_year) & (m_df['Year'] != min_year)] # & (m_df['Year'] <= 2017)

    print('mp path {} \n'.format(mp))
    print(m_df_complete_yrs.head(n=15))

    # rename the complete dataset m_df but getting the daily ETo from the avg calculations
    m_df = metdata_df_uniformat(m_df_complete_yrs, max_air='TMAX', min_air='TMIN', avg_air='TAVG',
                         solar='ATOT',
                         ppt='RAIN', maxrelhum='HMAX', minrelhum='HMIN',
                         avgrelhum='HAVG',
                         sc_wind_mg='WSPD', doy='DOY')


    m_df = calc_daily_ETo_uniformat(m_df, meters_abv_sealevel=meters_abv_sl, lonlat=lonlat, smoothing=False)

    gm['EToGM'] = gm['ETo']
    m_df['ETo_Station'] = m_df['ETo']
    m_df_daily = m_df.resample('1D').sum()
    gm_daily = gm.resample('1D').sum()
    daily_merge = pd.concat([m_df_daily, gm_daily], axis=1)
    daily_output = r'Z:\Users\Gabe\refET\OK_daily'
    daily_merge.to_csv(os.path.join(daily_output, '{}.csv'.format(okn)))

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

    # Change the heading of the ETo for gridmet and for DRI
    gm_monthly['EToGM'] = gm_monthly['ETo']
    m_df_monthly['ETo_Station'] = m_df_monthly['ETo']
    gm_yearly['EToGM'] = gm_yearly['ETo']
    m_df_yearly['ETo_Station'] = m_df_yearly['ETo']

    # Combine Monthly
    monthly_merge = pd.concat([m_df_monthly, gm_monthly], axis=1)
    print('outputing Monthly {}\{}.csv'.format(monthly_output, okn))
    monthly_merge.to_csv(os.path.join(monthly_output, '{}.csv'.format(okn)))

    # COMBINE YEARLY
    yearly_merge = pd.concat([m_df_yearly, gm_yearly], axis=1)
    print('outputing yearly {}\{}.csv'.format(yearly_output, okn))
    yearly_merge.to_csv(os.path.join(yearly_output, '{}.csv'.format(okn)))

    # # 3) Apply Smoothing
    # m_df_smoothed = m_df.rolling('10D').mean()
    # gm_smoothed = gm.rolling('10D').mean()
    # # === dates ===
    # m_smooth = m_df_smoothed.index
    # gm_smooth = gm_smoothed.index
    # # === values ===
    # m_vals_smooth = m_df_smoothed['ETo']
    # gm_vals_smooth = gm_smoothed['ETo']
    #
    #
    # # 4) Plot Monthly, Yearly, Smoothing
    # fig, ax = plt.subplots(4, 1, sharex=True)
    #
    # ax[0].plot(m_month, m_vals_month, color='green', label='AZMET ETo (mm)')
    # ax[0].scatter(m_month, m_vals_month, color='green', facecolor='none')
    # ax[0].plot(gm_month, gm_vals_month, color='black', label='GRIDMET ETo (mm)')
    # ax[0].scatter(gm_month, gm_vals_month, color='black', facecolor='none')
    # ax[0].set(xlabel='Date', ylabel='mm of ETo',
    #           title='{} Monthly Arizona Reference Vs Gridmet'.format(az_name))
    # ax[0].legend()
    #
    # ax[1].plot(m_year, m_vals_year, color='green', label='AZMET ETo (mm)')
    # ax[1].scatter(m_year, m_vals_year, color='green', facecolor='none')
    # ax[1].plot(gm_year, gm_vals_year, color='black', label='GRIDMET ETo (mm)')
    # ax[1].scatter(gm_year, gm_vals_year, color='black', facecolor='none')
    # ax[1].set(xlabel='Date', ylabel='mm of ETo',
    #           title='{} Yearly Arizona Reference Vs Gridmet'.format(az_name))
    # ax[1].legend()
    #
    # ax[2].plot(m_smooth, m_vals_smooth, color='green', label='AZMET ETo (mm)')
    # ax[2].scatter(m_smooth, m_vals_smooth, color='green', facecolor='none')
    # ax[2].plot(gm_smooth, gm_vals_smooth, color='black', label='GRIDMET ETo (mm)')
    # ax[2].scatter(gm_smooth, gm_vals_smooth, color='black', facecolor='none')
    # ax[2].set(xlabel='Date', ylabel='mm of ETo',
    #           title='{} Smoothed Daily Arizona Reference Vs Gridmet'.format(az_name))
    # ax[2].legend()
    #
    # ax[3].plot(m_df.index, m_df.ETo, color='green', label='{} ETo not smooth'.format(az_name))
    # ax[3].plot(gm.index, gm.ETo, color='black', label='Gridmet ETo (mm)')
    # ax[3].set(xlabel='Date', ylabel='mm ETo', title='{} UN-Smoothed Daily AZ Reference Vs Gridmet'.format(az_name))
    # ax[3].legend()
    #
    # ax[0].grid()
    # ax[1].grid()
    # ax[2].grid()
    # ax[3].grid()
    #
    # # plt.ylim((0, 16))
    # plt.tight_layout()
    # plt.legend()
    # # plt.show()
    #
    # # 5) plot monthly and yearly percent differences
    #
    # pdiff_month = (abs(m_vals_month - gm_vals_month) / gm_vals_month) * 100
    # pdiff_year = (abs(m_vals_year - gm_vals_year)/ gm_vals_year) * 100
    #
    # fig2, ax2 = plt.subplots(4, 1, sharex=True)
    #
    # ax2[0].plot(m_month, m_vals_month, color='green', label='AZMET ETo (mm)')
    # ax2[0].scatter(m_month, m_vals_month, color='green', facecolor='none')
    # ax2[0].plot(gm_month, gm_vals_month, color='black', label='GRIDMET ETo (mm)')
    # ax2[0].scatter(gm_month, gm_vals_month, color='black', facecolor='none')
    # ax2[0].set(xlabel='Date', ylabel='mm of ETo',
    #           title='{} Monthly Arizona Reference Vs Gridmet'.format(az_name))
    # ax2[0].legend()
    #
    # ax2[1].plot(pdiff_month.index, pdiff_month, color='blue', label='pdiff %')
    # ax2[1].scatter(pdiff_month.index, pdiff_month, color='blue', facecolor='none')
    # ax2[1].set(xlabel='Date', ylabel='percent difference',
    #           title='{} Monthly Arizona Reference Vs Gridmet'.format(az_name))
    # ax2[1].legend()
    #
    # ax2[2].plot(m_year, m_vals_year, color='green', label='Agrimet ETo (mm)')
    # ax2[2].scatter(m_year, m_vals_year, color='green', facecolor='none')
    # ax2[2].plot(gm_year, gm_vals_year, color='black', label='GRIDMET ETo (mm)')
    # ax2[2].scatter(gm_year, gm_vals_year, color='black', facecolor='none')
    # ax2[2].set(xlabel='Date', ylabel='mm of ETo',
    #           title='{} Yearly Arizona Reference Vs Gridmet'.format(az_name))
    # ax2[2].legend()
    #
    # ax2[3].plot(pdiff_year.index, pdiff_year, color='blue', label='pdiff %')
    # ax2[3].scatter(pdiff_year.index, pdiff_year, color='blue', facecolor='none')
    # ax2[3].set(xlabel='Date', ylabel='percent difference',
    #           title='{} Yearly Arizona Reference Vs Gridmet'.format(az_name))
    # ax2[3].legend()
    #
    # ax2[0].grid()
    # ax2[1].grid()
    # ax2[2].grid()
    # ax2[3].grid()
    # # ax[3].grid()
    #
    # # plt.ylim((0, 16))
    # plt.tight_layout()
    # plt.legend()
    # plt.show()