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
import numpy as np
from datetime import datetime
import seaborn
from matplotlib import pyplot as plt
from scipy import stats
# ============= standard library imports ========================


def compare_climatology(ts, clim):
    pass

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

# output_root = r'Z:\Users\Gabe\refET\deliverable_june18\prism_independent_analysis'
output_root = r'Z:\Users\Gabe\refET\deliverable_june18\PRISM_dependent_analysis'
# climatology_root = r'Z:\Users\Gabe\refET\deliverable_june18\metclims'
climatology_root = r'Z:\Users\Gabe\refET\deliverable_june18\metclims_PRISMDependent'

metdata_root = r'Z:\Users\Gabe\refET\deliverable_june18\PRISM-dependent_metdata'


# TODO - plot the timeseries for each analyzed site

# ==== making paths for analysis outputs ====
precip_output = os.path.join(output_root, 'precip_analysis')
if not os.path.exists(precip_output):
    os.mkdir(precip_output)

for f in os.listdir(metdata_root):
    # if f == 'Rogers Spring.csv' or f == 'Pahranagat NWR.csv':

    try:
        metpath = os.path.join(metdata_root, f)
        print(metpath)

        metcsv = pd.read_csv(metpath, header=0)

        # set up time indexing for daily timeseries
        metcsv['dt'] = metcsv.apply(lambda x: datetime.strptime(x['dt'], '%Y-%m-%d'), axis=1)
        metcsv.set_index('dt', inplace=True)



        # Do not take Zeros for Solar
        metcsv.loc[metcsv['Solar'] == 0] = np.nan

        # get rid of the NaN values
        metcsv.dropna(inplace=True)



        # the daily timeseries is the met csv. We rename for conventions only. To be compared to daily clim
        daily_ts = metcsv
        # make sure there is a day column to reference
        daily_ts['day'] = daily_ts.index.dayofyear
        # make a monthly timeseries to compare to the monthly climatology
        print(f'resampling for site!')
        # metcsv['month'] = metcsv.index.month # Does not work
        monthly_ts = metcsv.groupby(pd.Grouper(freq="M")).agg(MaxAir=pd.NamedAgg(column='MaxAir', aggfunc=np.mean),
                                                            MinAir=pd.NamedAgg(column='MinAir', aggfunc=np.mean),
                                                            AvgAir=pd.NamedAgg(column='AvgAir', aggfunc=np.mean),
                                                            Solar=pd.NamedAgg(column='Solar', aggfunc=np.sum),
                                                            Ppt=pd.NamedAgg(column='Ppt', aggfunc=np.sum),
                                                            MaxRelHum=pd.NamedAgg(column='MaxRelHum', aggfunc=np.mean),
                                                            MinRelHum=pd.NamedAgg(column='MinRelHum', aggfunc=np.mean),
                                                            ScWndMg=pd.NamedAgg(column='ScWndMg', aggfunc=np.mean),
                                                            ETo_Station=pd.NamedAgg(column='ETo_Station', aggfunc=np.sum),
                                                            EToGM=pd.NamedAgg(column='EToGM', aggfunc=np.sum),
                                                            )
        #month=pd.NamedAgg(column='month', aggfunc=np.mean)
        #month=pd.NamedAgg(column='month', aggfunc='median')




        # Get the daily climatologies and monthly climatologies
        daily_clim_path = os.path.join(climatology_root, 'daily', f)
        monthly_clim_path = os.path.join(climatology_root, 'monthly', f)
        daily_clim = pd.read_csv(daily_clim_path, header=0)
        daily_clim.set_index('dt', inplace=True)
        monthly_clim = pd.read_csv(monthly_clim_path, header=0)
        monthly_clim.set_index('dt', inplace=True)

        # make output folders for Precip, Humidity, Wind, Solar
        plotpath = os.path.join(output_root, 'figures_stddev')
        fname = f.split('.')[0]
        if not os.path.exists(plotpath):
            os.mkdir(plotpath)
        for i in ['Precip', 'Humidity', 'Wind', 'Solar']:
            temppath = os.path.join(plotpath, i)
            if not os.path.exists(temppath):
                os.mkdir(temppath)


        # ==== Precip Analysis Monthly (for precip only monthly makes sense) ====
        # Is the monthly precip for a given month high or low relative to the monthly climatology
        monthly_ts['month'] = monthly_ts.index.month # todo - why no work for FtMohave CA.csv????
        monthly_ts['Dry'] = monthly_ts.apply(lambda x: x['Ppt'] < (monthly_clim.loc[x['month'], 'Ppt'] -
                                                       (monthly_clim.loc[x['month'], 'Ppt'] * 0.15)), axis=1)
        # monthly_ts['Dry'] = monthly_ts.apply(lambda x: x['Ppt'] < monthly_clim.loc[x.index.month, 'Ppt'], axis=1)

        # print(monthly_ts['Dry'])
        monthly_ts['Wet'] = monthly_ts.apply(lambda x: not x['Dry'], axis=1)



        # monthly_ts.to_csv(os.path.join(testout, f))

        # Plotting PRECIP Analyses ========
        _tf = [True, False]
        fg = seaborn.FacetGrid(data=monthly_ts, hue='Dry', hue_order=_tf, aspect=1.61)
        fg.map(plt.scatter, 'ETo_Station', 'EToGM', facecolors='none').add_legend()
        plt.plot(monthly_ts['ETo_Station'], monthly_ts['ETo_Station'], label='one_to_one', color='red')
        fg.set_titles('{}, Monthly Precip'.format(f))
        plt.savefig(os.path.join(plotpath, 'Precip', f'{fname}MonthlyPrecip.png'))
        # plt.show()
        plt.close()


        # ===== Wind Analysis makes sense to do on a daily and monthly scale ======
        # DAILY ===
        # daily
        # daily_ts['Windy'] = daily_ts.apply(lambda x: x['ScWndMg'] > daily_clim.loc[x['day'], 'ScWndMg'], axis=1)
        daily_ts['Windy'] = daily_ts.apply(lambda x: x['ScWndMg'] > (daily_clim.loc[x['day'], 'ScWndMg'] +
                                                                     (daily_clim.loc[x['day'], 'ScWndMg'] * 0.15)), axis=1)
        _tf = [False, True]
        fg = seaborn.FacetGrid(data=daily_ts, hue='Windy', hue_order=_tf, aspect=1.61)
        fg.map(plt.scatter, 'ETo_Station', 'EToGM', facecolors='none').add_legend()
        plt.plot(daily_ts['ETo_Station'], daily_ts['ETo_Station'], label='one_to_one', color='red')
        fg.set_titles('{}, Daily Wind'.format(f))
        plt.savefig(os.path.join(plotpath, 'Wind', f'{fname}DailyWind.png'))
        # plt.show()
        plt.close()

        # # MONTHLY ===
        # monthly_ts['Windy'] = monthly_ts.apply(lambda x: x['ScWndMg'] > monthly_clim.loc[x['month'], 'ScWndMg'], axis=1)
        # _tf = [True, False]
        # fg = seaborn.FacetGrid(data=monthly_ts, hue='Windy', hue_order=_tf, aspect=1.61)
        # fg.map(plt.scatter, 'ETo_Station', 'EToGM', facecolors='none').add_legend()
        # fg.set_titles('{}, Monthly Wind'.format(f))
        # plt.savefig(os.path.join(plotpath, 'Wind', f'{fname}MonthlyWind.png'))
        # # plt.show()
        # plt.close()

        # ===== Humidity Analysis might be a better proxy for how well conditioned the soil is ======
        # DAILY ===
        # daily
        # daily_ts['Humid'] = daily_ts.apply(lambda x: x['MaxRelHum'] > daily_clim.loc[x['day'], 'MaxRelHum'], axis=1)
        daily_ts['Humid'] = daily_ts.apply(lambda x: x['MaxRelHum'] > (daily_clim.loc[x['day'], 'MaxRelHum'] +
                                                                     (daily_clim.loc[x['day'], 'MaxRelHum'] * .15)), axis=1)
        _tf = [False, True]
        fg = seaborn.FacetGrid(data=daily_ts, hue='Humid', hue_order=_tf, aspect=1.61)
        fg.map(plt.scatter, 'ETo_Station', 'EToGM', facecolors='none').add_legend()
        plt.plot(daily_ts['ETo_Station'], daily_ts['ETo_Station'], label='one_to_one', color='red')
        fg.set_titles('{}, Daily Maximum Relative Humidity'.format(f))
        plt.savefig(os.path.join(plotpath, 'Humidity', f'{fname}DailyHumidity.png'))
        # plt.show()
        plt.close()

        # # MONTHLY ===
        # monthly_ts['Humid'] = monthly_ts.apply(lambda x: x['MaxRelHum'] > monthly_clim.loc[x['month'], 'MaxRelHum'], axis=1)
        # _tf = [True, False]
        # fg = seaborn.FacetGrid(data=monthly_ts, hue='Humid', hue_order=_tf, aspect=1.61)
        # fg.map(plt.scatter, 'ETo_Station', 'EToGM', facecolors='none').add_legend()
        # fg.set_titles('{}, Monthly Wind'.format(f))
        # plt.savefig(os.path.join(plotpath, 'Humidity', f'{fname}MonthlyHumidity.png'))
        # # plt.show()
        # plt.close()

        # ===== Solar Analysis ======
        # DAILY ===
        # daily
        # daily_ts['HighRadiation'] = daily_ts.apply(lambda x: x['Solar'] > daily_clim.loc[x['day'], 'Solar'], axis=1)
        daily_ts['HighRadiation'] = daily_ts.apply(lambda x: x['Solar'] > (daily_clim.loc[x['day'], 'Solar'] +
                                                                     (daily_clim.loc[x['day'], 'Solar'] * 0.15)), axis=1)
        _tf = [False, True]
        fg = seaborn.FacetGrid(data=daily_ts, hue='HighRadiation', hue_order=_tf, aspect=1.61)
        fg.map(plt.scatter, 'ETo_Station', 'EToGM', facecolors='none').add_legend()
        plt.plot(daily_ts['ETo_Station'], daily_ts['ETo_Station'], label='one_to_one', color='red')
        fg.set_titles('{}, Daily Solar Radiation'.format(f))
        plt.savefig(os.path.join(plotpath, 'Solar', f'{fname}DailySolar.png'))
        # plt.show()
        plt.close()

        # # MONTHLY ===
        # monthly_ts['HighRadiation'] = monthly_ts.apply(lambda x: x['Solar'] > monthly_clim.loc[x['month'], 'Solar'],
        #                                        axis=1)
        # _tf = [True, False]
        # fg = seaborn.FacetGrid(data=monthly_ts, hue='HighRadiation', hue_order=_tf, aspect=1.61)
        # fg.map(plt.scatter, 'ETo_Station', 'EToGM', facecolors='none').add_legend()
        # fg.set_titles('{}, Monthly Solar Radiation'.format(f))
        # plt.savefig(os.path.join(plotpath, 'Solar', f'{fname}MonthlySolar.png'))
        # # plt.show()
        # plt.close()

        # Testing outputs
        testout = os.path.join(output_root, 'weather_variables_test')
        if not os.path.exists(testout):
            os.mkdir(testout)

        daily_ts.to_csv(os.path.join(testout, '{}_dailyTS.csv'.format(fname)))

    except:
        # raise
        print(f'could not do file {f}')
        continue

