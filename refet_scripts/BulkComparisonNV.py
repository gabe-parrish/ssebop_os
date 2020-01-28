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
from utils.os_utils import windows_path_fix
from SEEBop_os.raster_utils import gridmet_eto_reader
from ETref_tools.dataframe_calc_daily_ETr import metdata_df_uniformat, calc_daily_ETo_uniformat
from ETref_tools.metdata_preprocessor import  dri_preprocess

"""Here we compare a bunch of extracted (see BulkComparisonNV_GM_extract) DRI agrimet sites in Nevada to
 Extracted Gridmet via plotting with matplotlib"""

DRI_gridmet_root = r'Z:\Users\Gabe\refET\DRI_Agrimet_GridMet'
DRI_agrimet_root = r'Z:\Users\Gabe\refET\DRI_Agrimet_Metfiles\data_even_years'

shape = r'Z:\Users\Gabe\refET\refET_geo_files\DRI_agrimet_sites.shp'
yearly_output = r'Z:\Users\Gabe\refET\DRI_Grid_yearly_compare'
monthly_output = r'Z:\Users\Gabe\refET\DRI_Grid_monthly_compare'

fig_output = r'Z:\Users\Gabe\refET\nevada_figs_II_yearly'
# fig_output = r'Z:\Users\Gabe\refET\nevada_figs_II_monthly'

xbound_yr = 0 #500
ybound_yr =1800

xbound_mo = 0
ybound_mo = 400

metpaths = []
filenames = []

# # ============================== Plotting on 1 to 1 line.=====================================

# NOTE: The files in the yearly and monthly folder are created by code in TimeSeriesComparisonNV.py that used to be
# here in THIS script.
yearly_folder = r'Z:\Users\Gabe\refET\DRI_Grid_yearly_compare'
monthly_folder = r'Z:\Users\Gabe\refET\DRI_Grid_monthly_compare'

# # ================ YEARLY BULK ======================
for i in os.listdir(yearly_folder):
    sitename = i.split('.')[0]
    print('path:', os.path.join(yearly_folder, i))
    yr_df = pd.read_csv(os.path.join(yearly_folder, i))
    # yr_df.dropna(inplace=True)

    print('lengths of all 5 time series for site {}'.format(sitename))
    print(len(yr_df['EToDRI'].to_list()), len(yr_df['EToGM'].to_list()))
    print(len(yr_df['ET_total_ASCE'].to_list()), len(yr_df['EToGM'].to_list()))
    print(len(yr_df['ET_Penman_total'].to_list()), len(yr_df['EToGM'].to_list()))
    print(len(yr_df['ET_Penman_total'].to_list()), len(yr_df['EToDRI'].to_list()))

    plt.plot((xbound_yr, ybound_yr), (xbound_yr, ybound_yr), color='red')
    plt.scatter(yr_df['EToDRI'], yr_df['EToGM'], edgecolors='blue', facecolor='none')
    plt.title('{}, Yearly Cumulative Gabe Calc ETo'.format(sitename))
    plt.xlabel('ETo DRI (mm)')
    plt.ylabel('ETo Gridmet (mm)')
    plt.grid()
    plt.savefig(os.path.join(fig_output, '{}_Gabe_Calc_ETo_yearly.png'.format(sitename)))
    plt.close()

    plt.plot((xbound_yr, ybound_yr), (xbound_yr, ybound_yr), color='red')
    plt.scatter(yr_df['ET_total_ASCE'], yr_df['EToGM'], edgecolors='blue', facecolor='none')
    plt.title('{}, Yearly Cumulative DRI ASCE calc ETo'.format(sitename))
    plt.xlabel('ETo DRI (mm)')
    plt.ylabel('ETo Gridmet (mm)')
    plt.grid()
    plt.savefig(os.path.join(fig_output, '{}_DRI_ASCE_ETo_yearly.png'.format(sitename)))
    plt.close()

    plt.plot((xbound_yr, ybound_yr), (xbound_yr, ybound_yr), color='red')
    plt.scatter(yr_df['ET_Penman_total'], yr_df['EToGM'], edgecolors='blue', facecolor='none')
    plt.title('{}, Yearly Cumulative DRI Penman ETo'.format(sitename))
    plt.xlabel('ETo DRI (mm)')
    plt.ylabel('ETo Gridmet (mm)')
    plt.grid()
    plt.savefig(os.path.join(fig_output, '{}_DRI_Penman_calc_ETo_yearly.png'.format(sitename)))
    plt.close()

    plt.plot((xbound_yr, ybound_yr), (xbound_yr, ybound_yr), color='red')
    plt.scatter(yr_df['ET_Penman_total'], yr_df['EToDRI'], edgecolors='blue', facecolor='none')
    plt.title('{}, Yearly Cumulative DRI Gabe vs DRI PenmanET'.format(sitename))
    plt.xlabel('ET_Penman_total DRI (mm)')
    plt.ylabel('EToDRI Gabe (mm)')
    plt.grid()
    plt.savefig(os.path.join(fig_output, '{}_DRI_Gabe_vs_penman_ETo_yearly.png'.format(sitename)))
    plt.close()

    plt.plot((xbound_yr, ybound_yr), (xbound_yr, ybound_yr), color='red')
    plt.scatter(yr_df['ET_total_ASCE'], yr_df['EToDRI'], edgecolors='blue', facecolor='none')
    plt.title('{}, Yearly Cumulative DRI Gabe vs DRI ASCE ETo'.format(sitename))
    plt.xlabel('ET_ASCE DRI (mm)')
    plt.ylabel('EToDRI Gabe (mm)')
    plt.grid()
    plt.savefig(os.path.join(fig_output, '{}_DRI_Gabe_vs_ASCE_ETo_yearly.png'.format(sitename)))
    plt.close()

# ================ MONTHLY BULK ======================
for i in os.listdir(monthly_folder):
    sitename = i.split('.')[0]
    m_df = pd.read_csv(os.path.join(monthly_folder, i))

    print('lengths of all 5 time series for site {}'.format(sitename))
    print(len(m_df['EToDRI'].to_list()), len(m_df['EToGM'].to_list()))
    print(len(m_df['ET_total_ASCE'].to_list()), len(m_df['EToGM'].to_list()))
    print(len(m_df['ET_Penman_total'].to_list()), len(m_df['EToGM'].to_list()))
    print(len(m_df['ET_Penman_total'].to_list()), len(m_df['EToDRI'].to_list()))



    plt.plot((xbound_mo, ybound_mo), (xbound_mo, ybound_mo), color='red')
    plt.scatter(m_df['EToDRI'], m_df['EToGM'], edgecolors='blue', facecolor='none')
    plt.title('{}, Monthly Cumulative'.format(sitename))
    plt.xlabel('ETo DRI (mm)')
    plt.ylabel('ETo Gridmet (mm)')
    plt.grid()
    plt.savefig(os.path.join(fig_output, '{}_Gabe_Calc_ETo_monthly.png'.format(sitename)))
    plt.close()

    plt.plot((xbound_mo, ybound_mo), (xbound_mo, ybound_mo), color='red')
    plt.scatter(m_df['ET_total_ASCE'], m_df['EToGM'], edgecolors='blue', facecolor='none')
    plt.title('{}, Monthly Cumulative'.format(sitename))
    plt.xlabel('ETo DRI (mm)')
    plt.ylabel('ETo Gridmet (mm)')
    plt.grid()
    plt.savefig(os.path.join(fig_output, '{}_DRI_ASCE_ETo_monthly.png'.format(sitename)))
    plt.close()

    plt.plot((xbound_mo, ybound_mo), (xbound_mo, ybound_mo), color='red')
    plt.scatter(m_df['ET_Penman_total'], m_df['EToGM'], edgecolors='blue', facecolor='none')
    plt.title('{}, Monthly Cumulative'.format(sitename))
    plt.xlabel('ETo DRI (mm)')
    plt.ylabel('ETo Gridmet (mm)')
    plt.grid()
    plt.savefig(os.path.join(fig_output, '{}_DRI_Penman_calc_ETo_monthly.png'.format(sitename)))
    plt.close()

    plt.plot((xbound_mo, ybound_mo), (xbound_mo, ybound_mo), color='red')
    plt.scatter(m_df['ET_Penman_total'], m_df['EToDRI'], edgecolors='blue', facecolor='none')
    plt.title('{}, Monthly Cumulative'.format(sitename))
    plt.xlabel('ETo DRI (mm)')
    plt.ylabel('ETo Gridmet (mm)')
    plt.grid()
    plt.savefig(os.path.join(fig_output, '{}_DRI_Gabe_vs_penman_ETo_monthly.png'.format(sitename)))
    plt.close()

    plt.plot((xbound_mo, ybound_mo), (xbound_mo, ybound_mo), color='red')
    plt.scatter(m_df['ET_total_ASCE'], m_df['EToDRI'], edgecolors='blue', facecolor='none')
    plt.title('{}, Monthly Cumulative'.format(sitename))
    plt.xlabel('ETo DRI (mm)')
    plt.ylabel('ETo Gridmet (mm)')
    plt.grid()
    plt.savefig(os.path.join(fig_output, '{}_DRI_Gabe_vs_ASCE_ETo_monthly.png'.format(sitename)))
    plt.close()


# # ================================= plot the Gabe ETo ========================================
# PLOT the full monthly dataset on a scatter
plt.plot((xbound_mo, ybound_mo), (xbound_mo, ybound_mo), color='red')
color_list = ['black', 'grey', 'red', 'brown', 'tomato', 'darkorange', 'goldenrod', 'olive', 'olivedrab', 'fuchsia', 'green', 'turquoise', 'teal', 'dodgerblue', 'blue', 'purple']
dirlist = os.listdir(monthly_folder)
for i, color in zip(sorted(dirlist), color_list):
    sitename = i.split('.')[0]
    m_df = pd.read_csv(os.path.join(monthly_folder, i))
    plt.scatter(m_df['EToDRI'], m_df['EToGM'], edgecolors=color, facecolor='none', label=sitename)

plt.title('All sites, Monthly Cumulative')
plt.xlabel('ETo DRI (mm)')
plt.ylabel('ETo Gridmet (mm)')
plt.grid()
plt.legend()
plt.show()
plt.close()

# PLOT the full YEARLY dataset on a scatter
plt.plot((xbound_yr, ybound_yr), (xbound_yr, ybound_yr), color='red')

site_list = []
color_list = ['black', 'grey', 'red', 'brown', 'tomato', 'darkorange', 'goldenrod', 'olive', 'olivedrab', 'fuchsia', 'green', 'turquoise', 'teal', 'dodgerblue', 'blue', 'purple']
dirlist = os.listdir(yearly_folder)
for i, color in zip(sorted(dirlist), color_list):
    yr_df = pd.read_csv(os.path.join(yearly_folder, i))
    sitename = i.split('.')[0]
    site_list.append(sitename)
    plt.scatter(yr_df['ET_total_ASCE'], yr_df['EToGM'], edgecolors=color, facecolor='none', label=sitename)
plt.title('All Sites, Yearly Cumulative')
plt.xlabel('ETo DRI (mm)')
plt.ylabel('ETo Gridmet (mm)')
plt.grid()
plt.legend()
plt.show()

print(site_list)
print(len(site_list))
print(len(color_list))

# ================================= plot the ASCE ETo form DRI ========================================
plt.plot((xbound_mo, ybound_mo), (xbound_mo, ybound_mo), color='red')
color_list = ['black', 'grey', 'red', 'brown', 'tomato', 'darkorange', 'goldenrod', 'olive', 'olivedrab', 'fuchsia', 'green', 'turquoise', 'teal', 'dodgerblue', 'blue', 'purple']
dirlist = os.listdir(monthly_folder)
for i, color in zip(sorted(dirlist), color_list):
    sitename = i.split('.')[0]
    m_df = pd.read_csv(os.path.join(monthly_folder, i))
    plt.scatter(m_df['ET_total_ASCE'], m_df['EToGM'], edgecolors=color, facecolor='none', label=sitename)

plt.title('All sites, Monthly Cumulative')
plt.xlabel('ETo DRI (mm)')
plt.ylabel('ETo Gridmet (mm)')
plt.grid()
plt.legend()
plt.show()
plt.close()

# PLOT the full YEARLY dataset on a scatter
plt.plot((xbound_yr, ybound_yr), (xbound_yr, ybound_yr), color='red')

site_list = []
color_list = ['black', 'grey', 'red', 'brown', 'tomato', 'darkorange', 'goldenrod', 'olive', 'olivedrab', 'fuchsia', 'green', 'turquoise', 'teal', 'dodgerblue', 'blue', 'purple']
dirlist = os.listdir(yearly_folder)
for i, color in zip(sorted(dirlist), color_list):
    yr_df = pd.read_csv(os.path.join(yearly_folder, i))
    sitename = i.split('.')[0]
    site_list.append(sitename)
    plt.scatter(yr_df['EToDRI'], yr_df['EToGM'], edgecolors=color, facecolor='none', label=sitename)
plt.title('All Sites, Yearly Cumulative')
plt.xlabel('ETo DRI (mm)')
plt.ylabel('ETo Gridmet (mm)')
plt.grid()
plt.legend()
plt.show()

print(site_list)
print(len(site_list))
print(len(color_list))






