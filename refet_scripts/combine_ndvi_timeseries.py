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
from matplotlib import pyplot as plt
# ============= standard library imports ========================

root = r'Z:\Users\Gabe\refET\deliverable_june18\analysis_dec1_2020\united_sites\trueRef_MODIS_NDVI_test'
output_location = os.path.join(root, 'combined')

early_root = os.path.join(root, 'early')
late_root = os.path.join(root, 'late')

names_list = ['Antelope Valley_nevada_ndvi.csv', 'BVL_illinois_ndvi.csv', 'Clover Valley_nevada_ndvi.csv',
              'DEK_illinois_ndvi.csv', 'Harquahala_arizona_ndvi.csv', 'MON_illinois_ndvi.csv',
              'Paloma_arizona_ndvi.csv', 'Snake Valley_nevada_ndvi.csv', 'Yuma South_arizona_ndvi.csv']
std_names = ['AntelopeValleyNV', 'BondvilleIL', 'CloverValleyNV',
              'DeKalbIL', 'HarquahalaAZ', 'MonmouthIL',
              'PalomaAZ', 'SnakeValleyNV', 'YumaSouthAZ']

for n, sn in zip(names_list, std_names):
    early_file = os.path.join(early_root, n)
    late_file = os.path.join(late_root, n)
    print(early_file, '\n', late_file, '\n\n')

    # get aqua and terra from early and aqua and terra from late

    early_df = pd.read_csv(early_file, header=0, parse_dates=True)
    late_df = pd.read_csv(late_file, header=0, parse_dates=True)

    # print(early_df.head())
    # print(late_df.head())

    early_df['terra_date_dt'] = early_df.apply(lambda x: datetime.strptime(x['terra_date'], '%Y-%m-%d %H:%M:%S'), axis=1)
    late_df['terra_date_dt'] = late_df.apply(lambda x: datetime.strptime(x['terra_date'], '%Y-%m-%d %H:%M:%S'), axis=1)
    early_df['aqua_date_dt'] = early_df.apply(lambda x: datetime.strptime(x['aqua_date'], '%Y-%m-%d %H:%M:%S'), axis=1)
    late_df['aqua_date_dt'] = late_df.apply(lambda x: datetime.strptime(x['aqua_date'], '%Y-%m-%d %H:%M:%S'), axis=1)
    #
    # plt.plot(early_df.terra_date_dt, early_df.terra_ndvi, color='red')
    # plt.plot(early_df.aqua_date_dt, early_df.aqua_ndvi, color='blue')
    # plt.plot(late_df.terra_date_dt, late_df.terra_ndvi, color='red')
    # plt.plot(late_df.aqua_date_dt, late_df.aqua_ndvi, color='blue')
    # plt.title(n)
    #
    # plt.show()

    # todo - combine timeseries and split out Aqua and Terra NDVI
    # save the files in combined
    # also output times when the fields were relatively high NDVI .rolling('10D').mean()

    early_terra = pd.concat([early_df.terra_date_dt, early_df.terra_ndvi], axis=1).set_index('terra_date_dt')
    late_terra = pd.concat([late_df.terra_date_dt, late_df.terra_ndvi], axis=1).set_index('terra_date_dt')

    # do an outer merge on the indexes of both dataframes
    terra_df = pd.merge(early_terra, late_terra, how='outer', left_index=True, right_index=True)
    # the terra_ndvi column was a duplicate so it gets x for left and y for right by default. Replace the NaNs
    terra_df['terra_ndvi_x'].fillna(terra_df['terra_ndvi_y'], inplace=True)
    # make a more chill name
    terra_df['terra_ndvi'] = terra_df['terra_ndvi_x']
    # drop the columns you dont want
    terra_df = terra_df.drop(['terra_ndvi_x', 'terra_ndvi_y'], axis=1)

   # Do the same procedure for aqua

    early_aqua = pd.concat([early_df.aqua_date_dt, early_df.aqua_ndvi], axis=1).set_index('aqua_date_dt')
    late_aqua = pd.concat([late_df.aqua_date_dt, late_df.aqua_ndvi], axis=1).set_index('aqua_date_dt')

    aqua_df = pd.merge(early_aqua, late_aqua, how='outer', left_index=True, right_index=True)

    aqua_df['aqua_ndvi_x'].fillna(aqua_df['aqua_ndvi_y'], inplace=True)
    aqua_df['aqua_ndvi'] = aqua_df['aqua_ndvi_x']
    aqua_df = aqua_df.drop(['aqua_ndvi_x', 'aqua_ndvi_y'], axis=1)

    print(aqua_df.head())

    # do an ALL time NDVI join and use to determine high NDVI periods.

    modis_df = pd.merge(terra_df, aqua_df, how='outer', left_index=True, right_index=True)

    modis_df['terra_ndvi'].fillna(modis_df['aqua_ndvi'], inplace=True)

    modis_df['modis_ndvi'] = modis_df['terra_ndvi']
    modis_df = modis_df.drop(['terra_ndvi', 'aqua_ndvi'], axis=1)

    # plt.plot(modis_df.index, modis_df.modis_ndvi)
    # plt.show()
    modis_df.to_csv(os.path.join(output_location, f'{sn}_modis_ndvi.csv'))
