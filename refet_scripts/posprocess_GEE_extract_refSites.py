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
from numpy.polynomial.polynomial import polyfit
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from matplotlib import pyplot as plt
from matplotlib.dates import date2num
# import seaborn as sns
# ============= standard library imports ========================

"""
Pulling out NDVI values extracted by GEE surrounding weather stations, 
then plotting the timeseries.
"""

def yearly_data_extract(metpath, var='Ppt'):

    print('path is {}'.format(metpath))

    metcsv = pd.read_csv(metpath, header=0, parse_dates=True)

    metcsv['dt'] = metcsv.apply(lambda x: datetime.strptime(x['dt'], '%Y-%m-%d'), axis=1)
    metcsv.set_index('dt', inplace=True)

    # Do not take Zeros for Solar
    metcsv.loc[metcsv['Solar'] == 0] = np.nan
    # don't take zeros for ETo
    metcsv.loc[metcsv['ETo_Station'] == 0] = np.nan
    metcsv.loc[metcsv['ETo_Station'] == 0] = np.nan

    # get rid of nodata values so that nodata sets of time aren't evaluated to be zero...
    metcsv.dropna(inplace=True)

    # way to get climatologies for DAILY
    daily_clim_df = metcsv.groupby(metcsv.index.dayofyear).mean()

    # outputting daily mean climatologies to a file
    fname = os.path.split(metpath)[1]

    daily_ts = metcsv.index
    daily_station_eto = metcsv.ETo_Station
    daily_gm_eto = metcsv.EToGM

    yearly_ts = metcsv.groupby(pd.Grouper(freq="A")).agg(MaxAir=pd.NamedAgg(column='MaxAir', aggfunc=np.mean),
                                                          MinAir=pd.NamedAgg(column='MinAir', aggfunc=np.mean),
                                                          AvgAir=pd.NamedAgg(column='AvgAir', aggfunc=np.mean),
                                                          Solar=pd.NamedAgg(column='Solar', aggfunc=np.sum),
                                                          Ppt=pd.NamedAgg(column='Ppt', aggfunc=np.sum),
                                                          MaxRelHum=pd.NamedAgg(column='MaxRelHum', aggfunc=np.mean),
                                                          MinRelHum=pd.NamedAgg(column='MinRelHum', aggfunc=np.mean),
                                                          ScWndMg=pd.NamedAgg(column='ScWndMg', aggfunc=np.mean),
                                                          ETo_Station=pd.NamedAgg(column='ETo_Station', aggfunc=np.sum),
                                                          EToGM=pd.NamedAgg(column='EToGM', aggfunc=np.sum))

    # outputting monthly mean or mean cumulative climatologies to a file
    timeseries = yearly_ts.index
    dt_list = [datetime(year=i.year, month=1, day=1) for i in timeseries]
    var_series = yearly_ts[var].to_list()

    return dt_list, var_series, daily_ts, daily_station_eto, daily_gm_eto


def get_yearly_climatol(monthly_clim_path):
    """"""

    df = pd.read_csv(monthly_clim_path, header=0)

    annual_ppt_mm = df.Ppt.sum()

    return annual_ppt_mm

def extract_reference_times(ndvi_vals, ndvi_dates, daily_station_ts, daily_station_eto, daily_gm_eto):

    # assemble the station data into a dataframe
    station_df = pd.DataFrame({'daily_station_ts': daily_station_ts,
                  'daily_station_eto': daily_station_eto, 'daily_gm_eto': daily_gm_eto}, columns=['daily_station_ts',
                                                                                                  'daily_station_eto',
                                                                                                  'daily_gm_eto']).set_index('daily_station_ts')
    satellite_df = pd.DataFrame({'ndvi_vals': ndvi_vals, 'ndvi_dates': ndvi_dates}, columns=['ndvi_vals',
                                                                                                  'ndvi_dates']).set_index('ndvi_dates')

    daily_modis = satellite_df.resample('D').mean()
    daily_modis['linear_ndvi'] = daily_modis['ndvi_vals'].interpolate()
    daily_modis['smooth_ndvi'] = daily_modis['linear_ndvi'].rolling('10D').mean()

    big_green = pd.merge(daily_modis, station_df, how='outer', left_index=True, right_index=True)

    print('El Gran Verde\n', big_green.head())
    return big_green


# precipital climatol comes in here
metdata_root = r'Z:\Users\Gabe\refET\deliverable_june18\analysis_dec1_2020\united_sites\true_reference_metdata'
metclims = r'Z:\Users\Gabe\refET\deliverable_june18\analysis_dec1_2020\united_sites\true_reference_metclims'
NDVI_thresh = 0.7
# combined_root = r'Z:\Users\Gabe\refET\deliverable_june18\analysis_dec1_2020\united_sites\trueRef_MODIS_NDVI_test\combined'
combined_root = r'Z:\Users\Gabe\refET\deliverable_june18\analysis_MarchMay_2021\merged_ndvi_timeseries'

# plot_output = r'Z:\Users\Gabe\refET\deliverable_june18\analysis_dec1_2020\united_sites\plot_out'
plot_output = r'Z:\Users\Gabe\refET\deliverable_june18\analysis_dec1_2020\united_sites\plot_out_II'

snames = ['YumaSouthAZ', 'PalomaAZ', 'HarquahalaAZ', 'DeKalbIL', 'BondvilleIL', 'MonmouthIL', 'AntelopeValleyNV', 'CloverValleyNV', 'SnakeValleyNV']
ns_names = ['AZ1', 'AZ2', 'AZ3', 'IL1', 'IL2', 'IL3', 'NV1', 'NV2', 'NV3']
modis_files_list = [os.path.join(combined_root, f'{i}_modis_ndvi.csv') for i in ns_names]

ddict = {}
for modis_f, sn in zip(modis_files_list, snames):
    print(modis_f)
    data_dictionary = {}

    avg_annual_precip = get_yearly_climatol(os.path.join(metclims, f'{sn}.csv'))
    print(f'average precip for {sn} is {avg_annual_precip}')

    # get annual aggregated timeseries and annual aggregated precip,
    # also daily timeseries, daily eto and daily gridmet eto
    ts, yearly_precip, daily_ts, daily_station_eto, daily_gm_eto = yearly_data_extract(metpath=os.path.join(metdata_root, f'{sn}.csv'), var='Ppt')
    print('daily_ts', daily_ts)
    print('daily gm', daily_gm_eto)
    data_dictionary[f'{sn}_daily_ts'] = daily_ts
    data_dictionary[f'{sn}_daily_gmeto'] = daily_gm_eto
    data_dictionary[f'{sn}_daily_eto'] = daily_station_eto



    # calculating drought years as calendar years where precipitation is less than or equal to 20% of the annual mean
    drought_brackets = []
    percent_from_avg = [((j-avg_annual_precip)/(avg_annual_precip))*100 for j in yearly_precip]
    for t, p in zip(ts, percent_from_avg):
        if p <= -20.0:
            # if it's a drought put it in timebrackets
            drought_brackets.append((t, (t + relativedelta(years=+1) - relativedelta(days=+1))))
    # add the drought dates to the data dictionary
    data_dictionary['{}_droughts'.format(sn)] = drought_brackets

    with open(modis_f, 'r') as rfile:
        vals = []
        dates = []
        for i, line in enumerate(rfile):
            # strip out unwanted characters
            line = line.strip('\n')
            # split into a list
            lst = line.split(',')
            if i == 0:
                cols = lst
                cols[0] = 'date'
            elif i != 0:
                date_string =  lst[0]
                dtime = datetime.strptime(lst[0], '%Y-%m-%d')
                dates.append(dtime)
                try:
                    ndvi_val = float(lst[1])
                except:
                    ndvi_val = np.nan
                vals.append(ndvi_val)
        # add the values and dates to the dictionary
        data_dictionary['{}_values'.format(sn)] = vals
        data_dictionary['{}_dates'.format(sn)] = dates

        # when is the area of interest green enough to be considered reference?
        green_df = extract_reference_times(vals, dates, daily_ts, daily_station_eto, daily_gm_eto)

        # plot daily eto where ndvi is greater than 0.6
        green_df['veg_ref'] = (green_df['smooth_ndvi']>=NDVI_thresh)

        x = green_df[green_df['veg_ref']]['daily_station_eto']
        y = green_df[green_df['veg_ref']]['daily_gm_eto']



        fig, ax = plt.subplots()
        ax.scatter(green_df[green_df['veg_ref']]['daily_station_eto'], green_df[green_df['veg_ref']]['daily_gm_eto'], edgecolor='blue', facecolor='none', label='ETo (mm)')
        ax.plot(green_df[green_df['veg_ref']]['daily_station_eto'], green_df[green_df['veg_ref']]['daily_station_eto'], color='black', label='line of agreement')

        # # plot the line of best fit
        # b, m = polyfit(x, y, 1)
        # ax.plot(x, b+m *x, color='green', label=f'y = {m}x + {b}')
        ax.grid(True)
        ax.legend(loc='lower right')
        ax.set_title(f'{sn} - Comparing ETo on days where NDVI >= {NDVI_thresh}')
        ax.set_xlabel('Daily Station ETo (mm) ')
        ax.set_ylabel('Daily GRIDMET ETo (mm)')
        plt.savefig(os.path.join(plot_output, f'highNDVI_comparison_{sn}.png'))
        # plt.show()

        # plot the other shit
        fig, ax = plt.subplots()
        ax.plot(dates, vals, color='green', label='Terra/Aqua MODIS NDVI')
        ax.scatter(dates, vals, marker='s', edgecolor='green', facecolor='none')
        # highlight the drought periods
        for drought in drought_brackets:
            ax.axvspan(date2num(drought[0]), date2num(drought[1]), color='red', alpha=0.3)
        ax.grid(True)
        ax.legend(loc='lower right')
        ax.set_title(f'MODIS NDVI Timeseries and Drought Years - {sn}')
        ax.set_xlabel('Date')
        ax.set_ylabel('NDVI')
        plt.savefig(os.path.join(plot_output, f'NDVI_drought_timeseries_{sn}.PNG'))
        # plt.show()

    ddict[sn] = data_dictionary

# # print('the data dictionary\n', ddict)
#
# for n in snames:
#     sv_dates = ddict[f'{n}'][f'{n}_dates']
#     sv_ndvi = ddict[f'{n}'][f'{n}_values']
#     sv_droughts = ddict[f'{n}'][f'{n}_droughts']
#
#     fig, ax = plt.subplots()
#
#     ax.plot(sv_dates, sv_ndvi, color='green', label='Terra/Aqua MODIS NDVI')
#     ax.scatter(sv_dates, sv_ndvi, marker='s', edgecolor='green', facecolor='none')
#
#     # highlight the drought periods
#     for drought in sv_droughts:
#         ax.axvspan(date2num(drought[0]), date2num(drought[1]), color='red', alpha=0.3)
#
#     ax.grid(True)
#     ax.legend(loc='lower right')
#     ax.set_title(f'MODIS NDVI for {n}')
#     ax.set_xlabel('Date')
#     ax.set_ylabel('NDVI')
#     plt.show()