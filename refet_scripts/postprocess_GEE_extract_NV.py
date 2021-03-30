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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from matplotlib import pyplot as plt
from matplotlib.dates import date2num
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

    # get rid of nodata values so that nodata sets of time aren't evaluated to be zero...
    metcsv.dropna(inplace=True)

    # way to get climatologies for DAILY
    daily_clim_df = metcsv.groupby(metcsv.index.dayofyear).mean()

    # outputting daily mean climatologies to a file
    fname = os.path.split(metpath)[1]

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

    print(timeseries)
    print(var_series)
    print(dt_list)


    return dt_list, var_series



    # # Bizzarre stuff I have to do for the files from ICN. I have no idea why they behave differently.
    # if len(fname.split('.')[0])< 4:
    #     print('=========================\nJEZUZ\n===================\n')
    #     lines = []
    #     with open(os.path.join(monthly_outpath, fname), 'r') as rfile:
    #         for i, l in enumerate(rfile):
    #             line = l.split(',')
    #             if i == 1:
    #                 header2 = line[1:40]
    #                 header2 = ','.join(header2)
    #             elif i == 2:
    #                 header = f'dt,{header2}\n'
    #                 lines.append(header)
    #             elif i >=3:
    #                 regline = line[0:40]
    #                 regline = ','.join(regline)
    #                 regline = f'{regline}\n'
    #                 lines.append(regline)
    #
    #
    #     with open(os.path.join(monthly_outpath, fname), 'w') as wfile:
    #
    #         for i in lines:
    #             wfile.write(i)
    #


def get_yearly_climatol(monthly_clim_path):
    """"""

    df = pd.read_csv(monthly_clim_path, header=0)

    annual_ppt_mm = df.Ppt.sum()

    return annual_ppt_mm

# precipital climatol comes in here
metdata_root = r'Z:\Users\Gabe\refET\deliverable_june18\PRISM-independent_metdata'
metclims = r'Z:\Users\Gabe\refET\deliverable_june18\metclims\monthly'


# terra_path_NV = r'Z:\Users\Gabe\refET\deliverable_june18\analysis_dec1_2020\terra_aqua_NDVI_GEE\NICE_Net_Terra_NDVI_750_buffer.csv'
# aqua_path_NV = r'Z:\Users\Gabe\refET\deliverable_june18\analysis_dec1_2020\terra_aqua_NDVI_GEE\NICE_Net_Aqua_NDVI_750_buffer.csv'
terra_path_NV = r'Z:\Users\Gabe\refET\deliverable_june18\analysis_dec1_2020\terra_aqua_NDVI_GEE\NV_Terra_NDVI_750_buffer_00_10.csv'
aqua_path_NV = r'Z:\Users\Gabe\refET\deliverable_june18\analysis_dec1_2020\terra_aqua_NDVI_GEE\NV_Aqua_NDVI_750_buffer_00_10.csv'

# NV_names = ['Antelope Valley', 'Bridgeport Valley', 'Carson Valley', 'Clover Valley', 'Hualapai Flat', 'Mason Valley WMA',
#             'North Spring Valley', 'Pahranagat NWR', 'Paradise Valley', 'Reese River Valley', 'Rogers Spring',
#             'Sand Spring Valley', 'Smith Valley', 'Snake Valley', 'Steptoe Valley North',
#             'Steptoe Valley WMA']
# NV_names_extract = ['Antelope Valley', 'Bridgeport Valley', 'Carson Valley', 'Clover Valley', 'Hualapai Flat',
#                     'Mason Valley WMA', 'North Spring Valley', 'Pahranagat NWR', 'Paradise Valley', 'Reese River Valley',
#                     'Rogers Spring', 'Sand Spring Valley', 'Smith Valley', 'Snake Valley',
#                     'Steptoe Valley North',  'Steptoe Valley WMA']
NV_names = ['Antelope Valley', 'Clover Valley', 'Snake Valley']
NV_names_extract = ['Antelope Valley', 'Clover Valley', 'Snake Valley']


files_list = [terra_path_NV, aqua_path_NV]
fnames = ['terra', 'aqua']
ddict = {}

names = NV_names
site_names = NV_names_extract

for f, n, sn in zip(files_list, fnames, site_names):
    print(f)
    data_dictionary = {}

    avg_annual_precip = get_yearly_climatol(os.path.join(metclims, f'{sn}.csv'))
    print(f'average precip for {sn} is {avg_annual_precip}')
    # todo - calculate a timeseries of the percent above or below average precip each year is.
    ts, yearly_precip = yearly_data_extract(metpath=os.path.join(metdata_root, f'{sn}.csv'), var='Ppt')

    percent_from_avg = [((j - avg_annual_precip) / (avg_annual_precip)) * 100 for j in yearly_precip]
    print(percent_from_avg)

    drought_brackets = []
    for t, p in zip(ts, percent_from_avg):
        if p <= -5.0:
            # if it's a drought put it in timebrackets
            drought_brackets.append((t, (t + relativedelta(years=+1) - relativedelta(days=+1))))

    print(drought_brackets)
    with open(f, 'r') as rfile:
        # in this file, the topline is the timeseries, and each other line is unique to
        for i, line in enumerate(rfile):
            vals = []
            params = []
            # strip out unwanted characters
            line = line.strip('\n')
            # split into a list
            lst = line.split(',')
            # print('134', lst[134])
            if i == 0:
                timeline_headers = []
                datelist = []
                # if it's the first entry, try to convert it into a date and if it's not store it as something else
                for inx, entry in enumerate(lst):
                    try:
                        date = datetime.strptime(entry, '%Y-%m-%d')
                        datelist.append(date)
                    except:
                        try:
                            date = datetime.strptime(entry, '%m/%d/%Y')
                            datelist.append(date)
                        except ValueError:
                            print('exception for entry', entry)
                            if entry.startswith('Station Na'):
                                # I'll be damned if it isn't one off from the headers
                                name_indx = inx
                            else:
                                timeline_headers.append(entry)
                data_dictionary['property_headers'] = timeline_headers
                data_dictionary['timeline'] = datelist
            elif i != 0:
                nvals = []
                name = lst[name_indx]
                params = []
                for inx, entry in enumerate(lst):
                    if inx == 0:
                        params.append(entry)
                    elif entry.startswith('{NDVI='):
                        entry = entry.strip('{NDVI=')
                        entry = entry.strip('}')
                        # print('entry: ', entry)
                        # print('indx', inx)
                        if entry != 'null':
                            print('one was null')
                            vals.append(float(entry))
                        else:
                            vals.append(float(-9999.0))

                    else:
                        params.append(entry)

                print('name', name)
                data_dictionary['{}_values'.format(name)] = vals
                data_dictionary['{}_params'.format(name)] = params
    ddict[n] = data_dictionary

print('the data dictionary\n', ddict)

metdata_root = r'Z:\Users\Gabe\refET\deliverable_june18\PRISM-independent_metdata'
metclims = r'Z:\Users\Gabe\refET\deliverable_june18\metclims\monthly'

# output the data to a file
for n in names:
    sv_dates = ddict['terra']['timeline']
    print('sv dates', sv_dates)
    sv_ndvi = ddict['terra'][f'{n}_values']
    print('sv_ndvi', sv_ndvi)
    sv_aqua_dates = ddict['aqua']['timeline']
    print('aqua dates', sv_aqua_dates)
    sv_aqua_ndvi = ddict['aqua'][f'{n}_values']

    print(len(sv_dates), len(sv_ndvi), len(sv_aqua_dates), len(sv_aqua_ndvi))

    with open(os.path.join(r'Z:\Users\Gabe\refET\deliverable_june18\analysis_dec1_2020\united_sites\trueRef_MODIS_NDVI_test\early', f'{n}_nevada_ndvi.csv'), 'w') as wfile:
        wfile.write('terra_date,aqua_date,terra_ndvi,aqua_ndvi\n')
        for td, ad, tn, an in zip(sv_dates, sv_aqua_dates, sv_ndvi, sv_aqua_ndvi):
            wfile.write(f'{td},{ad},{tn},{an}\n')

# for n in names:
#     sv_dates = ddict['terra']['timeline']
#     sv_ndvi = ddict['terra'][f'{n}_values']
#     sv_aqua_dates = ddict['aqua']['timeline']
#     sv_aqua_ndvi = ddict['aqua'][f'{n}_values']
#
#     fig, ax = plt.subplots()
#
#     ax.plot(sv_dates, sv_ndvi, color='brown', label='Terra MODIS NDVI')
#     ax.scatter(sv_dates, sv_ndvi, marker='s', edgecolor='brown', facecolor='none')
#     ax.plot(sv_aqua_dates, sv_aqua_ndvi, color='blue', label='Aqua MODIS NDVI')
#     ax.scatter(sv_aqua_dates, sv_aqua_ndvi, marker='D', edgecolor='blue', facecolor='none')
#     # highlight the drought periods
#     for drought in drought_brackets:
#         ax.axvspan(date2num(drought[0]), date2num(drought[1]), color='red', alpha=0.3)
#
#     ax.grid(True)
#     ax.legend(loc='lower right')
#     ax.set_title(f'MODIS NDVI for {n} Nevada')
#     ax.set_xlabel('Date')
#     ax.set_ylabel('NDVI')
#     plt.show()