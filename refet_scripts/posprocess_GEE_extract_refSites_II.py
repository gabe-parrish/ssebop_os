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
from itertools import groupby, count
from dateutil.relativedelta import relativedelta
import yaml
from matplotlib import pyplot as plt
from matplotlib.dates import date2num
from refet_scripts.statistics_library import calc_kge, calc_mbe, calc_sde
# import seaborn as sns
# ============= standard library imports ========================
from refet_scripts.drought_USDM_timeseries import drought_USDM


# Is there an inherent weakness if the site is not irrigated? <-
# at many sites. (Fixed MATH ERROR in metdata_preprocessor.py)
# GET more irrigated sites (DONE)

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

    try:
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
    except KeyError:
        print('could not get it to go with precipitation')
        yearly_ts = metcsv.groupby(pd.Grouper(freq="A")).agg(MaxAir=pd.NamedAgg(column='MaxAir', aggfunc=np.mean),
                                                             MinAir=pd.NamedAgg(column='MinAir', aggfunc=np.mean),
                                                             AvgAir=pd.NamedAgg(column='AvgAir', aggfunc=np.mean),
                                                             Solar=pd.NamedAgg(column='Solar', aggfunc=np.sum),
                                                             MaxRelHum=pd.NamedAgg(column='MaxRelHum', aggfunc=np.mean),
                                                             MinRelHum=pd.NamedAgg(column='MinRelHum', aggfunc=np.mean),
                                                             ScWndMg=pd.NamedAgg(column='ScWndMg', aggfunc=np.mean),
                                                             ETo_Station=pd.NamedAgg(column='ETo_Station', aggfunc=np.sum),
                                                             EToGM=pd.NamedAgg(column='EToGM', aggfunc=np.sum))

    # outputting monthly mean or mean cumulative climatologies to a file
    timeseries = yearly_ts.index
    dt_list = [datetime(year=i.year, month=1, day=1) for i in timeseries]

    return dt_list, daily_ts, daily_station_eto, daily_gm_eto

def get_USDM_drought_from_file(dpath, thresh=3):
    """
    :param thresh: greater than or equal to the drought designation 0-4
    :param dpath: path on the system to a csv file.
    :return: [(droughtstart, droughtend), (,)] of drought above a certain threshold, i.e. 3
    """
    print(f'getting the continuous drought indices from {dpath}')

    # first, we'll determine if there is a extreme drought on a given date.
    ddates = []
    drought_des = []
    # also if it's a non drought, we want that too.

    with open(dpath, 'r') as rfile:
        for i, line in enumerate(rfile):
            if i == 0:
                print('this is the header so skip')
                pass
            else:
                line = line.strip('\n')
                lst = line.split(',')
                try:
                    drought_val = int(lst[1])
                except ValueError:
                    # Note: abnormal dryness is also 0, so could add confusion to analysis.
                    drought_val = 0
                date_val = datetime.strptime(lst[0], '%Y%m%d')

                # append to the lists.
                ddates.append(date_val)
                drought_des.append(drought_val)


    print(ddates)
    # then determine, based on the dates and the drought designation, which periods are continuous droughts.
    # a list of tuples to track continuous drought. To be returned by the function.
    # This was pretty dang hard. I referred to this:
    # https://stackoverflow.com/questions/30993182/how-to-get-the-index-range-of-a-list-that-the-values-satisfy-some-criterion-in-p
    drought_l = [idx for idx, value in enumerate(drought_des) if value >= thresh]
    drought_indices = [list(g) for _, g in groupby(drought_l, key=lambda n, c=count():n-next(c))]
    non_drought_l = [idx for idx, value in enumerate(drought_des) if value < thresh]
    non_drought_indices = [list(g) for _, g in groupby(non_drought_l, key=lambda n, c=count():n-next(c))]

    print('drought index\n', drought_indices)



    # convert the drought indices and non drought indices into tuple lists
    ### ==== TEST =====
    for ii in drought_indices:
        print('drought indices')
        print(ii)

    for ii in drought_indices:
        print('le index:', ii)
        print('index tuple', (ii[0], ii[-1]))
        print(ddates[ii[0]], ddates[ii[-1]])
    drought_tup_lst = [(ddates[ii[0]], ddates[ii[-1]]) for ii in drought_indices]
    non_drought_tup_lst = [(ddates[ii[0]], ddates[ii[-1]]) for ii in non_drought_indices]

    # print(f'drought tups \n {drought_tup_lst} \n non drought tups \n {non_drought_tup_lst}')
    return drought_tup_lst, non_drought_tup_lst

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
    daily_modis['smooth_ndvi'] = daily_modis['linear_ndvi'] #.rolling('3D').mean()

    big_green = pd.merge(daily_modis, station_df, how='outer', left_index=True, right_index=True)

    # print('El Gran Verde\n', big_green.head())
    return big_green

# #============== get_USDM_drought_from_file ====================
# print('testing USDM extractor')
drought_path = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\USDM_Drought_timeseries'
# value at which we consider the drought to be large enough to warrant comparison
USDM_drought_threshhold = 1
# meteorological data for selected sites.
metdata_root = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\selected_timeseries_comparisons'
# high and low threshold for NDVI work.
NDVI_high_thresh = 0.5
NDVI_low_thresh = 0.35
# Location for the NDVI timeseries
combined_root = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\terra_aqua_ndvi_merged'
# where the plots go
plot_output = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\script-generated_plots'

# two lists associating the correct site with correct filenames
snames = ['YumaSouthAZ', 'PalomaAZ', 'HarquahalaAZ',
          'WilcoxBenchAZ', 'QueenCreekAZ',
          'RollAZ', 'CoolidgeAZ', # Kansas Settlement, 'YumaNorthGilaAZ'
          'DeKalbIL', 'BondvilleIL', 'MonmouthIL',
          'AntelopeValleyNV', 'CloverValleyNV', 'SnakeValleyNV',
          'SandSpringValleyNV', 'SmithValleyNV', 'HualapaiFlatNV',
          'ParadiseValleyNV', 'ReeseRiverValleyNV', # MoapaValleyNV, blah blah WMA
          'LANEOK', 'RINGOK', 'EVAXOK',
          'BOISOK', 'HOLLOK', 'ALTUOK',
          'TIPTOK', 'GOODOK']
ns_names = ['AZ1', 'AZ2', 'AZ3',
            'AZ5', 'AZ6',
            'AZ8', 'AZ9',  # 'AZ4', 'AZ7',
            'IL1', 'IL2', 'IL3',
            'NV1', 'NV2', 'NV3',
            'NV4',  'NV6', 'NV7',
            'NV8', 'NV9',  # 'NV5', 'NV10',
            'OK1', 'OK2', 'OK3',
            'OK4', 'OK5', 'OK6',
            'OK7', 'OK8']
growing_season_months = [4, 5, 6, 7, 8, 9]

modis_files_list = [os.path.join(combined_root, f'{i}_modis_ndvi.csv') for i in ns_names]

# DONE: 0) Made sure that GEE script produced same yearly cumulatives as I got with pandas, fixed the way the
# yearly cum plots looked: (The cumulative number was dt-indexed to the end of each month, and not the start.)
# Done: 1) filter for growing season April-Oct (but not AZ sites?!?!)
# Done: 2) compare gridmet to gridmet during droughts (still controlling for field NDVI and growing season) see
# posprocess_GEE_extract_refsotes_III.py


# data dictionary (a dictionary of data_dictonaries)
ddict = {}
# statistics dictionary
stat_dict = {}
# looping through two sets of files
for modis_f, sn in zip(modis_files_list, snames):
    print(f'doing {sn}')
    # The dictionary holding the data for a given site.
    data_dictionary = {}

    # get annual aggregated timeseries and annual aggregated precip,
    # also daily timeseries, daily eto and daily gridmet eto
    ts, daily_ts, daily_station_eto, daily_gm_eto = yearly_data_extract(metpath=os.path.join(metdata_root, f'{sn}.csv'), var='Ppt')
    # adding NDVI, Gridmet ETo and Station ETo timeseries to a dictionary.
    data_dictionary[f'{sn}_daily_ts'] = daily_ts
    data_dictionary[f'{sn}_daily_gmeto'] = daily_gm_eto
    data_dictionary[f'{sn}_daily_eto'] = daily_station_eto

    # print('droughts \n', drought_brackets)
    # print('non droughts \n', non_drought_brackets)

    # USDM drought time periods as a list of tuple dates.
    USDM_drought_brackets, USDM_nonDrought_brackets = \
        get_USDM_drought_from_file(dpath=os.path.join(drought_path,
                                                      f'drought_timeline_{sn}.csv'), thresh=USDM_drought_threshhold)
    # #testing drought brackets
    # with open(r'C:\Users\gparrish\Documents\{}test.txt'.format(sn), 'w') as wfile:
    #     wfile.write('droughtstart, droughtend\n')
    #     for drought in USDM_drought_brackets:
    #         wfile.write(f'{drought[0]},{drought[1]}\n')

    if len(USDM_drought_brackets) == 0:
        print(f'{sn} has 0 droughts')
    if len(USDM_nonDrought_brackets) == 0:
        print(f'{sn} has 0 non Drought periods... Really?')
    # # if there's no brackets, forget it and move on:
    # if len(USDM_drought_brackets)==0 or len(USDM_nonDrought_brackets) == 0:
    #     continue

    # data_dictionary[f'{sn}_USDM_droughts'] = USDM_drought_brackets

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
                date_string = lst[0]
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
        def drought_data_grab(brackets):
            """"""
            df = pd.DataFrame()
            for start_time, end_time in brackets:
                selection = smoothed_ts_df[(smoothed_ts_df.index >= start_time) & (smoothed_ts_df.index <= end_time)]
                # print('selector \n', selection)
                df = df.append(selection)
            return df

        # grab the drought ETo datasets.
        USDM_drought_df = drought_data_grab(brackets=USDM_drought_brackets)
        USDM_nonDrought_df = drought_data_grab(brackets=USDM_nonDrought_brackets)

        # filter for growing season
        apr_mask = USDM_drought_df.index.map(lambda x: x.month) == 4
        may_mask = USDM_drought_df.index.map(lambda x: x.month) == 5
        june_mask = USDM_drought_df.index.map(lambda x: x.month) == 6
        jul_mask = USDM_drought_df.index.map(lambda x: x.month) == 7
        aug_mask = USDM_drought_df.index.map(lambda x: x.month) == 8
        sept_mask = USDM_drought_df.index.map(lambda x: x.month) == 9
        # filter for growing season (nodrought)
        apr_mask_nodrought = USDM_nonDrought_df.index.map(lambda x: x.month) == 4
        may_mask_nodrought = USDM_nonDrought_df.index.map(lambda x: x.month) == 5
        june_mask_nodrought = USDM_nonDrought_df.index.map(lambda x: x.month) == 6
        jul_mask_nodrought = USDM_nonDrought_df.index.map(lambda x: x.month) == 7
        aug_mask_nodrought = USDM_nonDrought_df.index.map(lambda x: x.month) == 8
        sept_mask_nodrought = USDM_nonDrought_df.index.map(lambda x: x.month) == 9

        # now control drought for NDVI
        if 'AZ' in sn:
            USDM_drought_df['drought_veg_ref'] = (USDM_drought_df['smooth_ndvi'] >= NDVI_high_thresh)
            # filter for growing season
            # redundant but i don't care
            USDM_drought_df['drought_veg_ref_gs'] = (USDM_drought_df['drought_veg_ref'])
            USDM_nonDrought_df['nondrought_veg_ref'] = (USDM_nonDrought_df['smooth_ndvi'] >= NDVI_high_thresh)
            # redundant but i don't care
            USDM_nonDrought_df['nondrought_veg_ref_gs'] = (USDM_nonDrought_df['nondrought_veg_ref'])
        else:
            USDM_drought_df['drought_veg_ref'] = (USDM_drought_df['smooth_ndvi'] >= NDVI_high_thresh)
            # filter for growing season
            USDM_drought_df['drought_veg_ref_gs'] = ((USDM_drought_df['drought_veg_ref']) & (apr_mask | may_mask
                                                     | june_mask | jul_mask | aug_mask | sept_mask))
            USDM_nonDrought_df['nondrought_veg_ref'] = (USDM_nonDrought_df['smooth_ndvi'] >= NDVI_high_thresh)
            USDM_nonDrought_df['nondrought_veg_ref_gs'] = ((USDM_nonDrought_df['nondrought_veg_ref']) & ( apr_mask_nodrought
                                                       | may_mask_nodrought | june_mask_nodrought | jul_mask_nodrought
                                                       | aug_mask_nodrought | sept_mask_nodrought))



        # plot daily eto where ndvi is greater/less than a threshold
        smoothed_ts_df['veg_ref'] = (smoothed_ts_df['smooth_ndvi'] >= NDVI_high_thresh)
        smoothed_ts_df['veg_nonref'] = (smoothed_ts_df['smooth_ndvi'] <= NDVI_low_thresh)

        # ================================================================================
        # ================================================================================
        # comparing and contrasting modeled and observed datasets based on NDVI, local/regional(USDM) droughts
        # ================================================================================
        # ================================================================================
        x_green = smoothed_ts_df[smoothed_ts_df['veg_ref']]['daily_station_eto']
        y_green = smoothed_ts_df[smoothed_ts_df['veg_ref']]['daily_gm_eto']
        x_brown = smoothed_ts_df[smoothed_ts_df['veg_nonref']]['daily_station_eto']
        y_brown = smoothed_ts_df[smoothed_ts_df['veg_nonref']]['daily_gm_eto']
        # === drought sensitivity ===
        if len(USDM_drought_brackets) > 0:
            x_usdm_drought = USDM_drought_df['daily_station_eto']
            y_usdm_drought = USDM_drought_df['daily_gm_eto']
        if len(USDM_nonDrought_brackets) > 0:
            x_usdm_nonDrought = USDM_nonDrought_df['daily_station_eto']
            y_usdm_nonDrought = USDM_nonDrought_df['daily_gm_eto']
        else:
            pass

        # process x and y datasets to calculate bias statistics
        xg_list = x_green.to_list()
        yg_list = y_green.to_list()
        xb_list = x_brown.to_list()
        yb_list = y_brown.to_list()
        # ===== USDM Drought and non =====
        if len(USDM_drought_brackets) > 0:
            x_usdm_d_list = x_usdm_drought.to_list()
            y_usdm_d_list = y_usdm_drought.to_list()
        if len(USDM_nonDrought_brackets) > 0:
            x_usdm_non_list = x_usdm_nonDrought.to_list()
            y_usdm_non_list = y_usdm_nonDrought.to_list()
        else:
            pass



        # doing all the required statistics.
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
                print(f'Site, {sn}, kge {kge}, alpha {alpha}, beta {beta}, '
                      f'pearson r {pearson_r}, mbe {mbe}, sde {sde}')
                site_dict = {'site': sn, 'kge': kge, 'alpha': alpha, 'beta': beta,
                             'pearson_r': pearson_r, 'mbe': mbe, 'sde': sde, 'nx': len(x_data), 'ny': len(y_data)}
                stat_dict[f'{sn}_{text}'] = site_dict

        # # === for High NDVI (greater than 0.7) ===
        do_stats(xlst=xg_list, ylst=yg_list, text='highNDVI')
        # # === for LOW NDVI ===
        do_stats(xlst=xb_list, ylst=yb_list, text='lowNDVI')
        # ======= For ALL station drought ======
        if len(USDM_drought_brackets) > 0:
            do_stats(xlst=x_usdm_d_list, ylst=y_usdm_d_list, text='USDMDrought')
        if len(USDM_nonDrought_brackets) > 0:
            do_stats(xlst=x_usdm_non_list, ylst=y_usdm_non_list, text='USDMnonDrought')
        else:
            pass

    try:
        txt_high_ndvi = f"MBE: {round(stat_dict[f'{sn}_highNDVI']['mbe'], 4)} KGE: {round(stat_dict[f'{sn}_highNDVI']['kge'], 4)}"
    except:
        txt_high_ndvi = ''
    try:
        txt_low_ndvi = f"MBE: {round(stat_dict[f'{sn}_lowNDVI']['mbe'], 4)} KGE: {round(stat_dict[f'{sn}_lowNDVI']['kge'], 4)}"
    except:
        txt_low_ndvi = ''
    try:
        txt_drought = f"MBE: {round(stat_dict[f'{sn}_drought']['mbe'], 4)} KGE: {round(stat_dict[f'{sn}_drought']['kge'], 4)}"
    except:
        txt_drought = ''
    try:
        txt_non_drought = f"MBE: {round(stat_dict[f'{sn}_NONdrought']['mbe'], 4)} KGE: {round(stat_dict[f'{sn}_NONdrought']['kge'], 4)}"
    except:
        txt_non_drought = ''
    try:
        txt_USDM_drought = f"MBE: {round(stat_dict[f'{sn}_USDMDrought']['mbe'], 4)} KGE: {round(stat_dict[f'{sn}_USDMDrought']['kge'], 4)}"
    except:
        txt_USDM_drought = ''
    try:
        txt_USDM_nondrought = f"MBE: {round(stat_dict[f'{sn}_USDMnonDrought']['mbe'], 4)} KGE: {round(stat_dict[f'{sn}_USDMnonDrought']['kge'], 4)}"
    except:
        txt_USDM_nondrought = ''

    # === plot drought timeseries ===
    fig, ax = plt.subplots()
    ax.plot(dates, vals, color='green', label='Terra/Aqua MODIS NDVI')
    ax.scatter(dates, vals, marker='s', edgecolor='green', facecolor='none')
    # highlight the drought periods
    for drought in USDM_drought_brackets:
        ax.axvspan(date2num(drought[0]), date2num(drought[1]), color='red', alpha=0.3)
    ax.grid(True)
    ax.legend(loc='lower right')
    ax.set_title(f'MODIS NDVI Timeseries and Drought Years level {USDM_drought_threshhold}+ : {sn}')
    ax.set_xlabel('Date')
    ax.set_ylabel('NDVI')
    # plt.show()
    plt.savefig(os.path.join(plot_output, f'NDVI_drought_timeseries_{sn}_USDMlvl{USDM_drought_threshhold}.jpeg'))

    # make a dataframe that contains values, only where valid station data exists.
    smoothed_ndvi_hist_df = smoothed_ts_df[smoothed_ts_df['daily_station_eto'].notnull()]
    drought_hist_df = USDM_drought_df[USDM_drought_df['daily_station_eto'].notnull()]
    non_drought_hist_df = USDM_nonDrought_df[USDM_nonDrought_df['daily_station_eto'].notnull()]

    # ====== PLOT high NDVI superimposed GRIDMET and Station Histograms, and BELOW on shared axis, plot low NDVI =======

    ax1 = plt.subplot(2, 1, 1)
    ax1.hist(smoothed_ndvi_hist_df[smoothed_ndvi_hist_df['veg_ref']]['daily_station_eto'], bins=15, alpha=0.5, color='blue', label='High NDVI Station ETo')
    ax1.hist(smoothed_ndvi_hist_df[smoothed_ndvi_hist_df['veg_ref']]['daily_gm_eto'], bins=15, alpha=0.5, color='green', label='High NDVI GRIDMET ETo')
    ax1.set_xlim([0, 12])
    ax1.legend(loc='upper right', prop={'size': 6})
    ax1.title.set_text(f'{sn} Reference, NDVI > {NDVI_high_thresh}')

    ax2 = plt.subplot(2, 1, 2)
    ax2.hist(smoothed_ndvi_hist_df[smoothed_ndvi_hist_df['veg_nonref']]['daily_station_eto'], bins=15, alpha=0.5, color='blue', label='Low NDVIStation ETo')
    ax2.hist(smoothed_ndvi_hist_df[smoothed_ndvi_hist_df['veg_nonref']]['daily_gm_eto'], bins=15, alpha=0.5, color='green', label='Low NDVIGRIDMET ETo')
    ax2.set_xlim([0, 12])
    ax2.legend(loc='upper right', prop={'size': 6})
    ax2.title.set_text(f'{sn} Non Reference, NDVI < {NDVI_low_thresh}')
    ax2.set_xlabel('ETo in mm')
    # plt.title(f'{sn} Reference/Non Reference Condtions')
    plt.tight_layout()
    plt.savefig(os.path.join(plot_output, f'Histo_NDVI_{sn}.jpeg'))
    # plt.show()
    plt.close()

    # === PLOT superimposed Drought Gridmet and Station Histograms, and BELOW, plot nondrought, Control for NDVI =======
    # todo - Make cols same width: https://stackoverflow.com/questions/41080028/how-to-make-the-width-of-histogram-columns-all-the-same
    ax3 = plt.subplot(2, 1, 1)
    ax3.hist(drought_hist_df[drought_hist_df['drought_veg_ref_gs']]['daily_station_eto'],
             bins=15, alpha=0.5, color='blue', label=f"Drought Station ETo (n={len(drought_hist_df[drought_hist_df['drought_veg_ref']]['daily_station_eto'])})")
    ax3.hist(drought_hist_df[drought_hist_df['drought_veg_ref_gs']]['daily_gm_eto'],
             bins=15, alpha=0.5, color='green', label=f"Drought GRIDMET ETo (n={len(drought_hist_df[drought_hist_df['drought_veg_ref']]['daily_gm_eto'])})")
    ax3.set_xlim([0, 12])
    ax3.legend(loc='upper right', prop={'size': 6})
    ax3.title.set_text(f'{sn} Drought Level {USDM_drought_threshhold}+ Growing season, NDVI > {NDVI_high_thresh}')

    ax4 = plt.subplot(2, 1, 2)
    ax4.hist(non_drought_hist_df[non_drought_hist_df['nondrought_veg_ref_gs']]['daily_station_eto'],
             bins=15, alpha=0.5, color='blue', label=f"Non Drought Station ETo (n={len(non_drought_hist_df[non_drought_hist_df['nondrought_veg_ref']]['daily_station_eto'])})")
    ax4.hist(non_drought_hist_df[non_drought_hist_df['nondrought_veg_ref_gs']]['daily_gm_eto'],
             bins=15, alpha=0.5, color='green', label=f"Non Drought GRIDMET ETo (n={len(non_drought_hist_df[non_drought_hist_df['nondrought_veg_ref']]['daily_gm_eto'])}")
    ax4.set_xlim([0, 12])
    ax4.legend(loc='upper right', prop={'size': 6})
    ax4.title.set_text(f'{sn} Non Drought Growing season, NDVI > {NDVI_high_thresh}')
    ax4.set_xlabel('ETo in mm')
    # plt.title(f'{sn} USDM Drought >{USDM_drought_threshhold} under Reference Condtions (NDVI>{NDVI_high_thresh})')
    plt.tight_layout()
    plt.savefig(os.path.join(plot_output, f'Histo_drought_{sn}_USDMlvl{USDM_drought_threshhold}.jpeg'))
    # plt.show()
    plt.close()


    # ... HIGH NDVI occurences ...
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
    plt.savefig(os.path.join(plot_output, f'highNDVI_comparison_{sn}.jpeg'))
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
    plt.savefig(os.path.join(plot_output, f'lowNDVI_comparison_{sn}.jpeg'))
    # plt.show()

    # ..... All Data.....
    fig, ax = plt.subplots()
    ax.scatter(smoothed_ts_df['daily_station_eto'],
               smoothed_ts_df['daily_gm_eto'],
               edgecolor='blue', facecolor='none', label='ETo (mm)')
    ax.plot(smoothed_ts_df['daily_station_eto'],
            smoothed_ts_df['daily_station_eto'],
            color='black', label='line of agreement')

    ax.grid(True)
    ax.legend(loc='lower right')
    ax.set_title(f'{sn} - ETo all Valid Dates')
    ax.set_xlabel('Daily Station ETo (mm) ')
    ax.set_ylabel('Daily GRIDMET ETo (mm)')
    plt.savefig(os.path.join(plot_output, f'FullDailyComparison_{sn}.jpeg'))
    # plt.show()

    if len(USDM_drought_brackets)>0:
        # ================= USDM Drought =====================
        fig, ax = plt.subplots()
        ax.scatter(USDM_drought_df[USDM_drought_df['drought_veg_ref_gs']]['daily_station_eto'],
                   USDM_drought_df[USDM_drought_df['drought_veg_ref_gs']]['daily_gm_eto'],
                   edgecolor='blue', facecolor='none', label='ETo (mm)')
        # the one-to-one line
        ax.plot(USDM_drought_df[USDM_drought_df['drought_veg_ref_gs']]['daily_station_eto'],
                USDM_drought_df[USDM_drought_df['drought_veg_ref_gs']]['daily_station_eto'],
                color='black', label='line of agreement')
        ax.grid(True)
        ax.legend(loc='lower right')
        ax.set_title(f'{sn} - Growing Season ETo during USDM level {USDM_drought_threshhold}+ Drought.\n {txt_USDM_drought}; NDVI >= {NDVI_high_thresh}')
        ax.set_xlabel('Daily Station ETo (mm)')
        ax.set_ylabel('Daily GRIDMET ETo (mm)')
        plt.savefig(os.path.join(plot_output, f'USDM_drought_comparison_{sn}_USDMlvl{USDM_drought_threshhold}.jpeg'))
        # plt.show()
    else:
        pass
    if len(USDM_nonDrought_brackets)>0:
        # ================= USDM NON Drought =====================
        fig, ax = plt.subplots()
        ax.scatter(USDM_nonDrought_df[USDM_nonDrought_df['nondrought_veg_ref_gs']]['daily_station_eto'],
                   USDM_nonDrought_df[USDM_nonDrought_df['nondrought_veg_ref_gs']]['daily_gm_eto'],
                   edgecolor='blue', facecolor='none', label='ETo (mm)')
        # the one-to-one line
        ax.plot(USDM_nonDrought_df[USDM_nonDrought_df['nondrought_veg_ref_gs']]['daily_station_eto'],
                USDM_nonDrought_df[USDM_nonDrought_df['nondrought_veg_ref_gs']]['daily_station_eto'],
                color='black', label='line of agreement')
        ax.grid(True)
        ax.legend(loc='lower right')
        ax.set_title(
            f'{sn} - Growing Season ETo with USDM level < {USDM_drought_threshhold}.\n {txt_USDM_nondrought}; NDVI >= {NDVI_high_thresh}')
        ax.set_xlabel('Daily Station ETo (mm)')
        ax.set_ylabel('Daily GRIDMET ETo (mm)')
        plt.savefig(os.path.join(plot_output, f'USDM_non_drought_comparison_{sn}_USDMlvl{USDM_drought_threshhold}.jpeg'))
        # plt.show()

# dump stats as a yml file
with open(os.path.join(plot_output, f'et_ref_stats.yml_USDMlvl{USDM_drought_threshhold}'), 'w') as wfile:
    yaml.dump(stat_dict, wfile)



