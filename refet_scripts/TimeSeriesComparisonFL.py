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
from datetime import datetime
import pandas as pd
import numpy as np
# ============= standard library imports ========================
from SEEBop_os.raster_utils import gridmet_eto_reader
from ETref_tools.dataframe_calc_daily_ETr import metdata_df_uniformat, calc_daily_ETo_uniformat

"""Here we compare a bunch of extracted (see BulkComparisonFL_GM_extract) FAWN sites to
 Extracted Gridmet via plotting with matplotlib. The script also outputs some files useful for analysis like accumulated
 monthly and yearly ETo. Prior to this script the function florida_separate.py was used to 
 separate files from a data request mega-file into individual files that can be dealt with individually and that 
 correspond to extracted GRIDMET files."""


gridmet_root = r'Z:\Users\Gabe\refET\FAWN\FAWN_GM_extract'
mesonet_root = r'C:\Users\gparrish\Desktop\mfile_out\florida_csvs'

yearly_output = r'Z:\Users\Gabe\refET\FAWN\FAWN_GRIDMET_yearly_compare'
monthly_output = r'Z:\Users\Gabe\refET\FAWN\FAWN_GRIDMET_monthly_compare'
daily_output = r'Z:\Users\Gabe\refET\FAWN\FAWN_GRIDMET_daily_compare'
if not os.path.exists(daily_output):
    os.mkdir(daily_output)

fig_output = r'Z:\Users\Gabe\refET\Delaware\FAWN_figs'

metpaths = []
mesonet_filenames = []
gmet_filenames = []

#================== A TIME SERIES COMPARISON =======================
for f in os.listdir(mesonet_root):
    # getting the paths to files
    metpath = os.path.join(mesonet_root, f)
    metpaths.append(metpath)
    # get the filename
    fn = f.split('.')[0]
    mesonet_filenames.append(fn)

for r in os.listdir(gridmet_root):
    gm_name = r.split('.')[0]
    gmet_filenames.append(gm_name)

# print('metpaths and filenames \n', metpaths, '\n', az_filenames, '\n', gmet_filenames)

gridmet_paths = []
mesonet_paths = []
names_in_common = []

for fname in mesonet_filenames:
    if fname in gmet_filenames:
        print('site name :', fname)
        gridmet_paths.append(os.path.join(gridmet_root, "{}.csv".format(fname)))
        mesonet_paths.append(os.path.join(mesonet_root, "{}.csv".format(fname)))
        names_in_common.append(fname)
for i, j in zip(gridmet_paths, mesonet_paths):
    print('gm: ', i)
    print('site: ', j)

#======================================================
#================ Mesonets'S OWN ETo ==================
#======================================================
# read in the corresponding DRI file and the gridmet file.
for gmp, mp, mn in zip(gridmet_paths, mesonet_paths, names_in_common):
    print('TODAYS mesonet name {}'.format(mn))
    gm = gridmet_eto_reader(gridmet_eto_loc=gmp, smoothing=False)

    # get the longitude and latitude from the point shapefile of the AZMet tower locations that you used to extract...
    lon = gm['Lon'].tolist()[0]
    lat = gm['Lat'].tolist()[0]
    lonlat = (lon, lat)
    print('lonlat: ', lonlat)
    meters_abv_sl = gm['elevation_m'].tolist()[0]
    print(meters_abv_sl, '\n sealevel')

    m_df = pd.read_csv(mp, header=0, index_col=None)

    # Taking care of the Nodata Values
    m_df[(m_df == 999) | (m_df == 999.0) | (m_df == 0.0) | (m_df == 0) | (m_df == -996) | (m_df == -996.0) | (
            m_df == -999) | (m_df == -999.0) | (m_df == '----') | (m_df == '-----') | (m_df == '---') |
         (m_df == '---- ') | (m_df == '--- ') | (m_df == '0.00 M') | (m_df == '') | (m_df == ' ') | (m_df == -6999)
         | (m_df == -6999.0) | (m_df == '-6999')] = np.nan
    print('fkn thing')
    print(m_df['date'])
    # stupid and redundant
    m_df['dt'] = pd.to_datetime(m_df['date'])
    # m_df['dt'] = m_df.apply(lambda x: pd.to_datetime(x['date']))

    # # make the dataframe date indexed so you can do timeseries transformations
    m_df = m_df.set_index('dt')
    m_df['date'] = pd.to_datetime(m_df.index)
    m_df['Year'] = m_df.apply(lambda x: int(x['date'].year), axis=1)
    m_df['DOY'] = m_df.apply(lambda x: x['date'].timetuple().tm_yday, axis=1)

    # FLORIDA only has average rel humidity so we just make max and min be the avg. (Comes out similarly in equation)
    # rel h = (Max + Min) / 2
    m_df['max_rh'] = m_df.apply(lambda x: float(x['avg_rh_2m_pct']), axis=1)
    m_df['min_rh'] = m_df.apply(lambda x: float(x['avg_rh_2m_pct']), axis=1)

    # at 2m. 10m and 60 cm measurements are also available. May be interesting to look at H somehow?
    m_df['trf_2m_MJm2'] = m_df.apply(lambda x: (float(x['trf_2m_MJm2'])), axis=1)
    m_df['avg_temp_air_2m_C'] = m_df.apply(lambda x: float(x['avg_temp_air_2m_C']), axis=1)
    m_df['max_temp_air_2m_C'] = m_df.apply(lambda x: float(x['max_temp_air_2m_C']), axis=1)
    m_df['min_temp_air_2m_C'] = m_df.apply(lambda x: float(x['min_temp_air_2m_C']), axis=1)

    # Taken @ 10m not 2m. Conflicting info on website. see refet station notes. Convert MPH to MPS
    m_df['avg_wind_speed_10m_mps'] = m_df.apply(lambda x: float(x['avg_wind_speed_10m_mph']) * 0.44704, axis=1)
    # convert inches to cm for RAINFALL
    m_df['sum_rain_2m_mm'] = m_df.apply(lambda x: float(x['sum_rain_2m_inches']) * 25.4, axis=1)


    max_year = max(m_df['Year'].to_list())
    min_year = min(m_df['Year'].to_list())
    print(max_year, min_year)
    # we only want complete years as part of the data-set so get rid of 2020 (or the maximum year)...
    # ...and the earliest year in the dataset.
    m_df_complete_yrs = m_df[(m_df['Year'] != max_year) & (m_df['Year'] != min_year)] # & (m_df['Year'] <= 2017)

    print('mp path {} \n'.format(mp))
    print(m_df_complete_yrs.head(n=15))

    # === NOTE === No precipitation for NC and original solar rad was average solar rad flux and has been converted to
    # daily total by preprocessing script.
    m_df = metdata_df_uniformat(m_df_complete_yrs, max_air='max_temp_air_2m_C', min_air='min_temp_air_2m_C', avg_air='avg_temp_air_2m_C',
                         ppt='sum_rain_2m_mm', solar='trf_2m_MJm2', maxrelhum='max_rh', minrelhum='min_rh',
                         avgrelhum='max_rh', sc_wind_mg='avg_wind_speed_10m_mps', doy='DOY', agency_eto=True, agency_eto_key='ETo_grass_mm')


    m_df = calc_daily_ETo_uniformat(m_df, meters_abv_sealevel=meters_abv_sl, lonlat=lonlat, smoothing=False)

    # === make daily outputs to be sure that  the values are good.
    # Change the heading of the ETo for gridmet and for DRI
    gm['EToGM'] = gm['ETo']
    m_df['ETo_Station'] = m_df['ETo']
    m_df_daily = m_df.resample('1D').sum()
    gm_daily = gm.resample('1D').sum()
    daily_merge = pd.concat([m_df_daily, gm_daily], axis=1)
    daily_merge.to_csv(os.path.join(daily_output, '{}.csv'.format(mn)))


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
    print('outputing Monthly {}\{}.csv'.format(monthly_output, mn))
    monthly_merge.to_csv(os.path.join(monthly_output, '{}.csv'.format(mn)))

    # COMBINE YEARLY
    yearly_merge = pd.concat([m_df_yearly, gm_yearly], axis=1)
    print('outputing yearly {}\{}.csv'.format(yearly_output, mn))
    yearly_merge.to_csv(os.path.join(yearly_output, '{}.csv'.format(mn)))