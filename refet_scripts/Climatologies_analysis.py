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
from datetime import datetime
import numpy as np
# ============= standard library imports ========================
from SEEBop_os.raster_utils import gridmet_eto_reader
from ETref_tools.dataframe_calc_daily_ETr import metdata_df_uniformat, calc_daily_ETo_uniformat


# ===== Keys to the uniform format dataframe ====
# new_df['MaxAir'] = df[max_air]
# new_df['MinAir'] = df[min_air]
# new_df['AvgAir'] = df[avg_air]
# new_df['Solar'] = df[solar]
# new_df['Ppt'] = df[ppt]
# new_df['MaxRelHum'] = df[maxrelhum]
# new_df['MinRelHum'] = df[minrelhum]
# new_df['RelHum'] = df[avgrelhum]
# new_df['ScWndMg'] = df[sc_wind_mg]
# new_df['doy'] = df[doy]

def climatology_calc(std_met_fpath, output_path):

    print('path is {}'.format(std_met_fpath))

    metcsv = pd.read_csv(std_met_fpath, header=0, parse_dates=True)

    metcsv['dt'] = metcsv.apply(lambda x: datetime.strptime(x['dt'], '%Y-%m-%d'), axis=1)
    metcsv.set_index('dt', inplace=True) #, drop=True

    # print(pd.isna(metcsv['Solar']))
    # print(metcsv['Solar'])

    # Do not take Zeros for Solar
    metcsv.loc[metcsv['Solar'] == 0] = np.nan

    # get rid of nodata values so that nodata sets of time aren't evaluated to be zero...
    metcsv.dropna(inplace=True)

    # way to get climatologies for DAILY
    daily_clim_df = metcsv.groupby(metcsv.index.dayofyear).mean()

    # outputting daily mean climatologies to a file
    fname = os.path.split(std_met_fpath)[1]
    daily_outpath = os.path.join(output_path, 'daily')
    if not os.path.exists(daily_outpath):
        os.mkdir(daily_outpath)
    daily_clim_df.to_csv(os.path.join(daily_outpath, fname))

    # the monthly climatologies (first get the monthly mean or cumulative of each month in the timeseries)
    # monthly_ts = metcsv.resample('1M').agg({'MaxAir': np.mean, 'MinAir': np.mean, 'AvgAir': np.mean, 'Solar': np.sum,
    #                                'Ppt': np.sum, 'MaxRelHum': np.mean, 'MinRelHum': np.mean, 'RelHum': np.mean,
    #                                'ScWndMg': np.mean}) ## OLD WAY

    # NEW WAY
    monthly_ts = metcsv.groupby(pd.Grouper(freq="M")).agg(MaxAir=pd.NamedAgg(column='MaxAir', aggfunc=np.mean),
                                                          MinAir=pd.NamedAgg(column='MinAir', aggfunc=np.mean),
                                                          AvgAir=pd.NamedAgg(column='AvgAir', aggfunc=np.mean),
                                                          Solar=pd.NamedAgg(column='Solar', aggfunc=np.sum),
                                                          Ppt=pd.NamedAgg(column='Ppt', aggfunc=np.sum),
                                                          MaxRelHum=pd.NamedAgg(column='MaxRelHum', aggfunc=np.mean),
                                                          MinRelHum=pd.NamedAgg(column='MinRelHum', aggfunc=np.mean),
                                                          ScWndMg=pd.NamedAgg(column='ScWndMg', aggfunc=np.mean),
                                                          ETo_Station=pd.NamedAgg(column='ETo_Station', aggfunc=np.sum),
                                                          EToGM=pd.NamedAgg(column='EToGM', aggfunc=np.sum))
    #RelHum=pd.NamedAgg(column='RelHum', aggfunc=np.mean),

    # print('testing monthlyts \n', monthly_ts.head())
    # now grab the mean cumulative or the mean scalar value for each month in the time-series for an appropriate
    # monthly climatology
    monthly_clim_df = monthly_ts.groupby(monthly_ts.index.month).mean()

    # print('testing clim df \n', monthly_clim_df.head())

    # outputting monthly mean or mean cumulative climatologies to a file
    fname = os.path.split(std_met_fpath)[1]
    monthly_outpath = os.path.join(output_path, 'monthly')
    if not os.path.exists(monthly_outpath):
        os.mkdir(monthly_outpath)
    monthly_clim_df.to_csv(os.path.join(monthly_outpath, fname))






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


daily_root = r'Z:\Users\Gabe\refET\deliverable_june18\PRISM-dependent_metdata'
output_root = os.path.join(r'Z:\Users\Gabe\refET\deliverable_june18', 'metclims_PRISMDependent')
if not os.path.exists(output_root):
    os.mkdir(output_root)

for f in os.listdir(daily_root):
    # path to the metfile.
    fpath = os.path.join(daily_root, f)

    # calculate the climatology
    climatology_calc(fpath, output_root)
