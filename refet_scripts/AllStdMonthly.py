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
from matplotlib import pyplot as plt
# ============= standard library imports ========================

# ======== testy testy test ======
root = r'Z:\Users\Gabe\refET\AA_standardized\standardized_monthly'
site = 'ARD2.csv'

spath = os.path.join(root, site)
df = pd.read_csv(spath, header=0)

# get rid of months where there is zero ETo at the station. C'est stupid.
df[df['ETo_Station'] == 0] = np.nan
df = df.dropna(axis=0)
print('df', df.head())
ppt = df['Ppt']
rad = df['Solar']
eto_station = df['ETo_Station']
eto_gm = df['EToGM']
date = df['dt']
dtlist = []

for d in date:
    print(d)
    datelist = d.split('/')
    dstring = f'{datelist[2]}{datelist[0]}{datelist[1]}'
    dayt = datetime.strptime(dstring, '%Y%m%d')
    dtlist.append(dayt)
date = dtlist

# What is a wet month vs dry month?
# Median monthly climatological precip at the gage.
# =================================================
fig, ax1 = plt.subplots()
ax1.plot(date, eto_station, color='black', label='Station ETo (mm)')
ax1.plot(date, eto_gm, color='red', label='GRIDMET ETo (mm)')
ax1.set_ylabel('ETo (mm)')
ax1.set_xlabel('Month')
ax1.legend()
# =================================================
ax2 = ax1.twinx()
ax2.bar(date, ppt, color='blue', label='precip (mm)')
ax2.set_ylabel('Precip (mm)')
ax2.legend()
plt.show()

# plot (GRIDMET_monthly - Station_monthly) vs Precip_monthly: Is there a linear relationship