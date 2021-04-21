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
import math
import numpy as np
from numpy.polynomial.polynomial import polyfit
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import yaml
from matplotlib import pyplot as plt
from matplotlib.dates import date2num
from refet_scripts.statistics_library import calc_kge, calc_mbe, calc_sde
# import seaborn as sns
# ============= standard library imports ========================
from refet_scripts.drought_USDM_timeseries import Drought_USDM

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

def get_USDM_drought_from_file(dpath):
    """"""
    # todo
    pass
def smooth_and_interpolate_ndvi(ndvi_vals, ndvi_dates, daily_station_ts, daily_station_eto, daily_gm_eto):

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

    # print('El Gran Verde\n', big_green.head())
    return big_green

# meteorological data for selected sites.
metdata_root = r'Z:\Users\Gabe\refET\deliverable_june18\analysis_dec1_2020\united_sites\true_reference_metdata'
# precipitation climatology comes in here
metclims = r'Z:\Users\Gabe\refET\deliverable_june18\analysis_dec1_2020\united_sites\true_reference_metclims'
# high and low threshold for NDVI work.
NDVI_high_thresh = 0.7
NDVI_low_thresh = 0.35
# Location for the NDVI timeseries
combined_root = r'Z:\Users\Gabe\refET\deliverable_june18\analysis_MarchMay_2021\merged_ndvi_timeseries'
# where the plots go
plot_output = r'Z:\Users\Gabe\refET\deliverable_june18\analysis_dec1_2020\united_sites\plot_out_II'

# two lists associating the correct site with correct filenames
snames = ['YumaSouthAZ', 'PalomaAZ', 'HarquahalaAZ', 'DeKalbIL', 'BondvilleIL', 'MonmouthIL', 'AntelopeValleyNV', 'CloverValleyNV', 'SnakeValleyNV']
ns_names = ['AZ1', 'AZ2', 'AZ3', 'IL1', 'IL2', 'IL3', 'NV1', 'NV2', 'NV3']
modis_files_list = [os.path.join(combined_root, f'{i}_modis_ndvi.csv') for i in ns_names]

# data dictionary (a dictionary of data_dictonaries)
ddict = {}
# statistics dictionary
stat_dict = {}
# looping through two sets of files
for modis_f, sn in zip(modis_files_list, snames):
    # The dictionary holding the data for a given site.
    data_dictionary = {}

    # getting a precipitation climatology.
    avg_annual_precip = get_yearly_climatol(os.path.join(metclims, f'{sn}.csv'))

    # get annual aggregated timeseries and annual aggregated precip,
    # also daily timeseries, daily eto and daily gridmet eto
    ts, yearly_precip, daily_ts, daily_station_eto, daily_gm_eto = yearly_data_extract(metpath=os.path.join(metdata_root, f'{sn}.csv'), var='Ppt')
    # adding NDVI, Gridmet ETo and Station ETo timeseries to a dictionary.
    data_dictionary[f'{sn}_daily_ts'] = daily_ts
    data_dictionary[f'{sn}_daily_gmeto'] = daily_gm_eto
    data_dictionary[f'{sn}_daily_eto'] = daily_station_eto

    # calculating drought years as calendar years where precipitation is less than or equal to 20% of the annual mean
    drought_brackets = []
    # get the non-drought periods too.
    non_drought_brackets = []
    # TODO - for the analysis, make a function that returns a drought bracket and non drought bracket list(s) for a given site.
    percent_from_avg = [((j-avg_annual_precip)/(avg_annual_precip))*100 for j in yearly_precip]
    for t, p in zip(ts, percent_from_avg):
        if p <= -20.0:
            # if it's a drought put it in timebrackets
            drought_brackets.append((t, (t + relativedelta(years=+1) - relativedelta(days=+1))))
        else:
            # if p is not a drought condition, then append the year to a non-drought list
            non_drought_brackets.append((t, (t + relativedelta(years=+1) - relativedelta(days=+1))))
    # add the drought dates to the data dictionary
    data_dictionary['{}_droughts'.format(sn)] = drought_brackets

    print('droughts \n', drought_brackets)
    print('non droughts \n', non_drought_brackets)

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
        smoothed_ts_df = smooth_and_interpolate_ndvi(vals, dates, daily_ts, daily_station_eto, daily_gm_eto)

        # Pull out data from drought and non_drought periods.
        # useful stack for this https://stackoverflow.com/questions/29441243/pandas-time-series-multiple-slice
        drought_df = pd.DataFrame()
        for start_time, end_time in drought_brackets:
            selection = smoothed_ts_df[(smoothed_ts_df.index >= start_time) & (smoothed_ts_df.index <= end_time)]
            print('drought_selector \n', selection)
            drought_df = drought_df.append(selection)
        non_drought_df = pd.DataFrame()
        for start_time, end_time in non_drought_brackets:
            selection = smoothed_ts_df[(smoothed_ts_df.index >= start_time) & (smoothed_ts_df.index <= end_time)]
            print('non_drought_selector \n', selection)
            non_drought_df = non_drought_df.append(selection)

        # print(f'drought_df {sn} \n', drought_df['smooth_ndvi'].head())
        # print(f'non_drought_df {sn}\n', non_drought_df['smooth_ndvi'].head())

        # plot drought eto where ndvi is greater or less than the threshold
        drought_df['drought_high_ndvi'] = (drought_df['smooth_ndvi'] >= NDVI_high_thresh)
        drought_df['drought_low_ndvi'] = (drought_df['smooth_ndvi'] <= NDVI_low_thresh)

        # plot daily eto where ndvi is greater/less than a threshold
        smoothed_ts_df['veg_ref'] = (smoothed_ts_df['smooth_ndvi'] >= NDVI_high_thresh)
        smoothed_ts_df['veg_nonref'] = (smoothed_ts_df['smooth_ndvi'] <= NDVI_low_thresh)

        # ================================================================================
        # ================================================================================
        # ================================================================================

        x_green = smoothed_ts_df[smoothed_ts_df['veg_ref']]['daily_station_eto']
        y_green = smoothed_ts_df[smoothed_ts_df['veg_ref']]['daily_gm_eto']
        x_brown = smoothed_ts_df[smoothed_ts_df['veg_nonref']]['daily_station_eto']
        y_brown = smoothed_ts_df[smoothed_ts_df['veg_nonref']]['daily_gm_eto']
        # === drought sensitivity ===
        x_green_drought = drought_df[drought_df['drought_high_ndvi']]['daily_station_eto']
        y_green_drought = drought_df[drought_df['drought_high_ndvi']]['daily_gm_eto']
        x_brown_drought = drought_df[drought_df['drought_low_ndvi']]['daily_station_eto']
        y_brown_drought = drought_df[drought_df['drought_low_ndvi']]['daily_gm_eto']
        x_all_drought = drought_df['daily_station_eto']
        y_all_drought = drought_df['daily_gm_eto']
        # Non Drought Sensitivity ======
        x_non_drought = non_drought_df['daily_station_eto']
        y_non_drought = non_drought_df['daily_gm_eto']

        # process x and y datasets to calculate bias statistics
        xg_list = x_green.to_list()
        yg_list = y_green.to_list()
        xb_list = x_brown.to_list()
        yb_list = y_brown.to_list()
        # == drought ==
        xgd_list = x_green_drought.to_list()
        ygd_list = y_green_drought.to_list()
        xbd_list = x_brown_drought.to_list()
        ybd_list = y_brown_drought.to_list()
        xd_list = x_all_drought.to_list()
        yd_list = y_all_drought.to_list()
        # === Non drought ===
        xnd_list = x_non_drought.to_list()
        ynd_list = y_non_drought.to_list()

        def do_stats(xlst, ylst, text):
            x_data = []
            y_data = []
            for l, m in zip(xlst, ylst):
                # if either l or m is nan, drop both
                if not math.isnan(l) and not math.isnan(m):
                    x_data.append(l)
                    y_data.append(m)
            # for x and y, calculate the Kling-Gupta Efficiency, Mean Bias Error (MBE) and Standard Dev of Error (SDE)
            if not len(x_data) == 0:
                kge, alpha, beta, pearson_r = calc_kge(y_o=x_data, y_m=y_data)
                mbe = calc_mbe(y_o=x_data, y_m=y_data)
                sde = calc_sde(y_o=x_data, y_m=y_data)
                print(f'Site, {sn}, kge {kge}, alpha {alpha}, beta {beta}, pearson r {pearson_r}, mbe {mbe}, sde {sde}')
                site_dict = {'site': sn, 'kge': kge, 'alpha': alpha, 'beta': beta,
                             'pearson_r': pearson_r, 'mbe': mbe, 'sde': sde, 'nx': len(x_data), 'ny': len(y_data)}
                stat_dict[f'{sn}_{text}'] = site_dict

        # # === for High NDVI (greater than 0.7) ===
        do_stats(xlst=xg_list, ylst=yg_list, text='highNDVI')

        # # === for LOW NDVI ===
        do_stats(xlst=xb_list, ylst=yb_list, text='lowNDVI')

        # === for drought
        do_stats(xlst=xgd_list, ylst=ygd_list, text='highNDVIdrought')
        do_stats(xlst=xbd_list, ylst=ybd_list, text='lowNDVIdrought')
        do_stats(xlst=xd_list, ylst=yd_list, text='drought')
        # === for non-drought
        do_stats(xlst=xnd_list, ylst=ynd_list, text='NONdrought')


    try:
        txt_high_ndvi = f"MBE: {round(stat_dict[f'{sn}_highNDVI']['mbe'], 4)} KGE: {round(stat_dict[f'{sn}_highNDVI']['kge'], 4)}"
        txt_low_ndvi = f"MBE: {round(stat_dict[f'{sn}_lowNDVI']['mbe'], 4)} KGE: {round(stat_dict[f'{sn}_lowNDVI']['kge'], 4)}"
        txt_drought = f"MBE: {round(stat_dict[f'{sn}_drought']['mbe'], 4)} KGE: {round(stat_dict[f'{sn}_drought']['kge'], 4)}"
        txt_non_drought = f"MBE: {round(stat_dict[f'{sn}_NONdrought']['mbe'], 4)} KGE: {round(stat_dict[f'{sn}_NONdrought']['kge'], 4)}"
    except:
        txt_high_ndvi = ''
        txt_low_ndvi = ''
        txt_drought = ''
        txt_non_drought = ''

    # === plot drought timeseries ===
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

    # ..... HIGH NDVI occurences.....
    fig, ax = plt.subplots()
    ax.scatter(smoothed_ts_df[smoothed_ts_df['veg_ref']]['daily_station_eto'],
               smoothed_ts_df[smoothed_ts_df['veg_ref']]['daily_gm_eto'], edgecolor='blue', facecolor='none', label='ETo (mm)')
    ax.plot(smoothed_ts_df[smoothed_ts_df['veg_ref']]['daily_station_eto'],
            smoothed_ts_df[smoothed_ts_df['veg_ref']]['daily_station_eto'], color='black', label='line of agreement')
    ax.grid(True)
    ax.legend(loc='lower right')
    ax.set_title(f'{sn} - Comparing ETo on days where NDVI >= {NDVI_high_thresh} \n {txt_high_ndvi}')
    ax.set_xlabel('Daily Station ETo (mm) ')
    ax.set_ylabel('Daily GRIDMET ETo (mm)')
    plt.savefig(os.path.join(plot_output, f'highNDVI_comparison_{sn}.png'))
    # plt.show()

    # ..... Low NDVI occurences.....
    fig, ax = plt.subplots()
    ax.scatter(smoothed_ts_df[smoothed_ts_df['veg_nonref']]['daily_station_eto'],
               smoothed_ts_df[smoothed_ts_df['veg_nonref']]['daily_gm_eto'],
               edgecolor='blue', facecolor='none', label='ETo (mm)')
    ax.plot(smoothed_ts_df[smoothed_ts_df['veg_nonref']]['daily_station_eto'],
            smoothed_ts_df[smoothed_ts_df['veg_nonref']]['daily_station_eto'],
            color='black', label='line of agreement')

    ax.grid(True)
    ax.legend(loc='lower right')
    ax.set_title(f'{sn} - Comparing ETo on days where NDVI <= {NDVI_low_thresh}\n {txt_low_ndvi}')
    ax.set_xlabel('Daily Station ETo (mm) ')
    ax.set_ylabel('Daily GRIDMET ETo (mm)')
    plt.savefig(os.path.join(plot_output, f'lowNDVI_comparison_{sn}.png'))
    # plt.show()

    # ===Drought===
    fig, ax = plt.subplots()
    ax.scatter(drought_df['daily_station_eto'],
               drought_df['daily_gm_eto'],
               edgecolor='blue', facecolor='none', label='ETo (mm)')
    # the one-to-one line
    ax.plot(drought_df['daily_station_eto'],
            drought_df['daily_station_eto'],
            color='black', label='line of agreement')
    ax.grid(True)
    ax.legend(loc='lower right')
    ax.set_title(f'{sn} - - Comparing daily ETo during drought periods. \n {txt_drought}')
    ax.set_xlabel('Daily Station ETo (mm)')
    ax.set_ylabel('Daily GRIDMET ETo (mm)')
    plt.savefig(os.path.join(plot_output, f'drought_comparison_{sn}.png'))
    # plt.show()

    # ===NonDrought===
    fig, ax = plt.subplots()
    ax.scatter(non_drought_df['daily_station_eto'],
               non_drought_df['daily_gm_eto'],
               edgecolor='blue', facecolor='none', label='ETo (mm)')
    # the one-to-one line
    ax.plot(non_drought_df['daily_station_eto'],
            non_drought_df['daily_station_eto'],
            color='black', label='line of agreement')
    ax.grid(True)
    ax.legend(loc='lower right')
    ax.set_title(f'{sn} - Comparing daily ETo during normal periods.\n {txt_non_drought}')
    ax.set_xlabel('Daily Station ETo (mm)')
    ax.set_ylabel('Daily GRIDMET ETo (mm)')
    plt.savefig(os.path.join(plot_output, f'nondrought_comparison_{sn}.png'))
    # plt.show()

# dump stats as a yml file
with open(os.path.join(plot_output, 'et_ref_stats.yml'), 'w') as wfile:
    yaml.dump(stat_dict, wfile)