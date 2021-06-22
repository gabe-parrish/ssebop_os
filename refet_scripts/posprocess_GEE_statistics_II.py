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
from refet_scripts.statistics_library import calc_kge, calc_mbe, calc_sde, calc_variance
# ============= standard library imports ========================

"""
Pulling out NDVI values extracted by GEE surrounding weather stations, 
then plotting the timeseries.
"""

# #============== get_USDM_drought_from_file ====================
# print('testing USDM extractor')
drought_path = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\USDM_Drought_timeseries'
# value at which we consider the drought to be large enough to warrant comparison
USDM_drought_threshhold = 1
# meteorological data for selected sites.
metdata_root = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\selected_timeseries_comparisons'
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
modis_files_list = [os.path.join(combined_root, f'{i}_modis_ndvi.csv') for i in ns_names]

# looping through two sets of files
for modis_f, sn in zip(modis_files_list, snames):
    print(f'doing {sn}')

    ts_df = pd.read_csv(os.path.join(metdata_root, f'{sn}.csv'))
    # print(ts_df.head(10))
    ts_df['dt'] = ts_df.apply(lambda x: datetime.strptime(x['dt'], '%Y-%m-%d'), axis=1)
    ts_df.set_index('dt', inplace=True)

    # # Do not take Zeros for Solar
    # ts_df.loc[ts_df['Solar'] == 0] = np.nan
    # # don't take zeros for ETo
    # ts_df.loc[ts_df['ETo_Station'] == 0] = np.nan
    # ts_df.loc[ts_df['ETo_Station'] == 0] = np.nan

    # # linearly interpolate station ETo to assure full coverage.
    # # https://towardsdatascience.com/how-to-interpolate-time-series-data-in-apache-spark-and-python-pandas-part-1-pandas-cff54d76a2ea
    # # crates a group-by object, no missing dates can exist, and gaps are filled with NAN
    # daily_ts_df = ts_df.resample('D').mean()
    # daily_ts_df['ETo_Station_Linear'] = daily_ts_df['ETo_Station'].interpolate('linear')

    # drop all data where there is no ETo for stations after interpolation (GRIDMET goes back into the past)
    continuous_df = ts_df[ts_df['ETo_Station'].notnull()]

    # TODO - Yearly cumulative ETo for stations + # TODO - Yearly Cumulative ETo for Gridmet
    # aggregate the ETo for stations and gridmet annually
    # TODO yearly ETo variability for stations + # TODO yearly ETo variability for GRIDMET.
    # variability within each year
    try:
        yearly_ts = continuous_df.groupby(pd.Grouper(freq="AS")).agg(MaxAir=pd.NamedAgg(column='MaxAir', aggfunc=np.nanmean),
                                                                    MinAir=pd.NamedAgg(column='MinAir', aggfunc=np.nanmean),
                                                                    AvgAir=pd.NamedAgg(column='AvgAir', aggfunc=np.nanmean),
                                                                    Solar=pd.NamedAgg(column='Solar', aggfunc=np.nansum),
                                                                    Ppt=pd.NamedAgg(column='Ppt', aggfunc=np.nansum),
                                                                    MaxRelHum=pd.NamedAgg(column='MaxRelHum', aggfunc=np.nanmean),
                                                                    MinRelHum=pd.NamedAgg(column='MinRelHum', aggfunc=np.nanmean),
                                                                    ScWndMg=pd.NamedAgg(column='ScWndMg', aggfunc=np.nanmean),
                                                                    ETo_Station=pd.NamedAgg(column='ETo_Station',
                                                                                                   aggfunc=np.nansum),
                                                                    ETo_Station_Var=pd.NamedAgg(column='ETo_Station',
                                                                                                aggfunc=np.nanvar),
                                                                    EToGM=pd.NamedAgg(column='EToGM', aggfunc=np.nansum),
                                                                    EToGM_Var=pd.NamedAgg(column='EToGM', aggfunc=np.nanvar))
    except KeyError:
        print('some stations do not have precip data')
        yearly_ts = continuous_df.groupby(pd.Grouper(freq="AS")).agg(MaxAir=pd.NamedAgg(column='MaxAir', aggfunc=np.nanmean),
                                                                    MinAir=pd.NamedAgg(column='MinAir', aggfunc=np.nanmean),
                                                                    AvgAir=pd.NamedAgg(column='AvgAir', aggfunc=np.nanmean),
                                                                    Solar=pd.NamedAgg(column='Solar', aggfunc=np.nansum),
                                                                    MaxRelHum=pd.NamedAgg(column='MaxRelHum', aggfunc=np.nanmean),
                                                                    MinRelHum=pd.NamedAgg(column='MinRelHum', aggfunc=np.nanmean),
                                                                    ScWndMg=pd.NamedAgg(column='ScWndMg', aggfunc=np.nanmean),
                                                                    ETo_Station_Linear=pd.NamedAgg(column='ETo_Station',
                                                                                                   aggfunc=np.nansum),
                                                                    ETo_Station_Var=pd.NamedAgg(column='ETo_Station',
                                                                                                aggfunc=np.nanvar),
                                                                    EToGM=pd.NamedAgg(column='EToGM', aggfunc=np.nansum),
                                                                    EToGM_Var=pd.NamedAgg(column='EToGM', aggfunc=np.nanvar))

    print('yearly!\n', yearly_ts.head())

    # Plot annual cumulative ETo timeseries.
    plt.plot(yearly_ts.index, yearly_ts['EToGM'], color='blue', label='Cumulative Gridmet ETo')
    plt.scatter(yearly_ts.index, yearly_ts['EToGM'], color='blue', facecolor=None)
    plt.plot(yearly_ts.index, yearly_ts['ETo_Station'], color='green', label='Cumulative Station ETo')
    plt.scatter(yearly_ts.index, yearly_ts['ETo_Station'], color='green', facecolor=None)
    plt.title(f'{sn} Cumulative ETo')
    plt.legend(loc='upper right', prop={'size': 6})
    plt.grid()
    #===
    plt.savefig(os.path.join(plot_output, f'CumETo_ts_{sn}.jpeg'))
    plt.close()
    # plt.show()

    # Plot annual variability timeseries.
    plt.plot(yearly_ts.index, yearly_ts['EToGM_Var'], color='blue', label='Gridmet ETo Variance')
    plt.scatter(yearly_ts.index, yearly_ts['EToGM_Var'], color='blue', facecolor=None)
    plt.plot(yearly_ts.index, yearly_ts['ETo_Station_Var'], color='green', label='Station ETo Variance')
    plt.scatter(yearly_ts.index, yearly_ts['ETo_Station_Var'], color='green', facecolor=None)
    plt.title(f'{sn} ETo Variance')
    plt.legend(loc='upper right', prop={'size': 6})
    plt.savefig(os.path.join(plot_output, f'Var_ETo_{sn}.jpeg'))
    # plt.show()
    plt.close()