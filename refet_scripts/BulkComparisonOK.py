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
from matplotlib import pyplot as plt
import pandas as pd
# ============= standard library imports ========================

"""Here we compare a bunch of extracted (see BulkComparisonNV_GM_extract) DRI agrimet sites in Nevada to
 Extracted Gridmet via plotting with matplotlib"""

shape = r'Z:\Users\Gabe\refET\OK_Mesonet\mesonet_sites_shape\mesonet_sites_shape\ok_mesonet_sites_all_20181031.shp'
yearly_output = r'Z:\Users\Gabe\refET\OKMESONET_GRIDMET_yearly_compare'
monthly_output = r'Z:\Users\Gabe\refET\OKMESONET_GRIDMET_monthly_compare'

fig_output = r'Z:\Users\Gabe\refET\ok_figs_yearly'
# fig_output = r'Z:\Users\Gabe\refET\ok_figs_monthly'

xbound_yr = 0 #500
ybound_yr =1800

xbound_mo = 0
ybound_mo = 400

metpaths = []
filenames = []

# # ============================== Plotting on 1 to 1 line.=====================================

# NOTE: The files in the yearly and monthly folder are created by code in TimeSeriesComparisonNV.py that used to be
# here in THIS script.
yearly_folder = r'Z:\Users\Gabe\refET\OKMESONET_GRIDMET_yearly_compare'
monthly_folder = r'Z:\Users\Gabe\refET\OKMESONET_GRIDMET_monthly_compare'

 # ================ YEARLY BULK ======================
for i in os.listdir(yearly_folder):
    sitename = i.split('.')[0]
    print('path:', os.path.join(yearly_folder, i))
    yr_df = pd.read_csv(os.path.join(yearly_folder, i))
    # yr_df.dropna(inplace=True)

    plt.plot((xbound_yr, ybound_yr), (xbound_yr, ybound_yr), color='red')
    plt.scatter(yr_df['ETo_Station'], yr_df['EToGM'], edgecolors='blue', facecolor='none')
    plt.title('{}, Yearly Cumulative Gabe Calc ETo'.format(sitename))
    plt.xlabel('ETo Mesonet (mm)')
    plt.ylabel('ETo Gridmet (mm)')
    plt.grid()
    plt.savefig(os.path.join(fig_output, '{}_Gabe_Calc_ETo_yearly.png'.format(sitename)))
    plt.close()


# ================ MONTHLY BULK ======================
for i in os.listdir(monthly_folder):
    sitename = i.split('.')[0]
    m_df = pd.read_csv(os.path.join(monthly_folder, i))

    # m_df = m_df[(m_df[])]

    plt.plot((xbound_mo, ybound_mo), (xbound_mo, ybound_mo), color='red')
    plt.scatter(m_df['ETo_Station'], m_df['EToGM'], edgecolors='blue', facecolor='none')
    plt.title('{}, Monthly Cumulative Gabe Calc ETo'.format(sitename))
    plt.xlabel('ETo AZMET (mm)')
    plt.ylabel('ETo Gridmet (mm)')
    plt.grid()
    # plt.show()
    plt.savefig(os.path.join(fig_output, '{}_Gabe_Calc_ETo_monthly.png'.format(sitename)))
    plt.close()


# # ================================= plot the Gabe ETo ========================================
# PLOT the full monthly dataset on a scatter
plt.plot((xbound_mo, ybound_mo), (xbound_mo, ybound_mo), color='red')
# 19 colors for 19 sites
color_list = ['black', 'grey', 'red', 'brown', 'tomato', 'darkorange', 'goldenrod', 'olive', 'olivedrab', 'fuchsia',
              'green', 'turquoise', 'teal', 'dodgerblue', 'blue', 'purple', 'plum', 'deeppink', 'crimson', 'tan', 'yellow', 'navy']
dirlist = os.listdir(monthly_folder)
for i, color in zip(sorted(dirlist), color_list):
    sitename = i.split('.')[0]
    print(sitename, color, monthly_folder)
    m_df = pd.read_csv(os.path.join(monthly_folder, i))
    plt.scatter(m_df['ETo_Station'], m_df['EToGM'], edgecolors=color, facecolor='none', label=sitename)

plt.title('All sites, Monthly Cumulative')
plt.xlabel('ETo AZMET (mm)')
plt.ylabel('ETo Gridmet (mm)')
plt.grid()
plt.legend()
plt.show()
plt.close()

# PLOT the full YEARLY dataset on a scatter
plt.plot((xbound_yr, ybound_yr), (xbound_yr, ybound_yr), color='red')

site_list = []
color_list = ['black', 'grey', 'red', 'brown', 'tomato', 'darkorange', 'goldenrod', 'olive', 'olivedrab', 'fuchsia',
              'green', 'turquoise', 'teal', 'dodgerblue', 'blue', 'purple', 'plum', 'deeppink', 'crimson', 'tan',
              'yellow', 'navy']
dirlist = os.listdir(yearly_folder)
for i, color in zip(sorted(dirlist), color_list):
    yr_df = pd.read_csv(os.path.join(yearly_folder, i))
    sitename = i.split('.')[0]
    site_list.append(sitename)
    plt.scatter(yr_df['ETo_Station'], yr_df['EToGM'], edgecolors=color, facecolor='none', label=sitename)
plt.title('All Sites, Yearly Cumulative')
plt.xlabel('ETo AZMET (mm)')
plt.ylabel('ETo Gridmet (mm)')
plt.grid()
plt.legend()
plt.show()
plt.close()

print(site_list)
print(len(site_list))
print(len(color_list))

# ================================= plot the AZMET ETo from AZMET ========================================
plt.plot((xbound_mo, ybound_mo), (xbound_mo, ybound_mo), color='red')
color_list = ['black', 'grey', 'red', 'brown', 'tomato', 'darkorange', 'goldenrod', 'olive', 'olivedrab', 'fuchsia',
              'green', 'turquoise', 'teal', 'dodgerblue', 'blue', 'purple', 'plum', 'deeppink', 'crimson', 'tan', 'yellow', 'navy']
dirlist = os.listdir(monthly_folder)
for i, color in zip(sorted(dirlist), color_list):
    sitename = i.split('.')[0]
    m_df = pd.read_csv(os.path.join(monthly_folder, i))
    plt.scatter(m_df['ETo_AZ'], m_df['EToGM'], edgecolors=color, facecolor='none', label=sitename)

plt.title('All sites, Monthly Cumulative')
plt.xlabel('ETo ASCE (mm)')
plt.ylabel('ETo Gridmet (mm)')
plt.grid()
plt.legend()
plt.show()
plt.close()

# PLOT the full YEARLY dataset on a scatter
plt.plot((xbound_yr, ybound_yr), (xbound_yr, ybound_yr), color='red')

site_list = []
color_list = ['black', 'grey', 'red', 'brown', 'tomato', 'darkorange', 'goldenrod', 'olive', 'olivedrab', 'fuchsia',
              'green', 'turquoise', 'teal', 'dodgerblue', 'blue', 'purple', 'plum', 'deeppink', 'crimson', 'tan', 'yellow', 'navy']
dirlist = os.listdir(yearly_folder)
for i, color in zip(sorted(dirlist), color_list):
    yr_df = pd.read_csv(os.path.join(yearly_folder, i))
    sitename = i.split('.')[0]
    site_list.append(sitename)
    plt.scatter(yr_df['ETo_AZ'], yr_df['EToGM'], edgecolors=color, facecolor='none', label=sitename)
plt.title('All Sites, Yearly Cumulative')
plt.xlabel('ETo AZMET (mm)')
plt.ylabel('ETo Gridmet (mm)')
plt.grid()
plt.legend()
plt.show()

print(site_list)
print(len(site_list))
print(len(color_list))