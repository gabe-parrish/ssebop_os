import os
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime as dt
from matplotlib.dates import date2num
import matplotlib.dates as mdates
import rasterio
from dateutil import relativedelta
from glob import glob
from progressbar import progressbar
import pandas as pd

def get_tif_arr(tiff_path):

    with rasterio.open(tiff_path) as src:
        arr = src.read(1)
        return arr


def accumulate_arrays(p_list):
    """"""
    for i, p in progressbar(enumerate(p_list)):
        if i == 0:
            print('zeroth path: ', p)
            zeroth_arr = get_tif_arr(p)
            print('zeroth arr here \n', zeroth_arr.shape)
            orig_arr = zeroth_arr[~np.isnan(zeroth_arr)]
            print('shape of orig arr \n', orig_arr.shape)
            orig_arr = orig_arr.flatten()
            print('shape shape flatten', orig_arr.shape)
        else:
            ith_arr = get_tif_arr(p)
            ith_arr = ith_arr[~np.isnan(ith_arr)]
            orig_arr = np.append(orig_arr, ith_arr)

    return orig_arr


def average_arrays(p_list):
    mean_vals = []
    for i, p in progressbar(enumerate(p_list)):
        zeroth_arr = get_tif_arr(p)
        orig_arr = zeroth_arr[~np.isnan(zeroth_arr)]
        try:
            my_mean = np.nanmean(orig_arr)
            mean_vals.append(my_mean)
        except:
            print('was an error getting mean')
            mean_vals.append(float('nan'))

    return mean_vals


def get_common_dates(drought_dt_lst, nondrought_dt_lst, drought_plist, nondrought_plist):
    """"""

    drought_common_date_indices = []
    nondrought_common_date_indices = []
    common_date_lst = []
    for i, d in enumerate(drought_dt_lst):
        for ii, nd in enumerate(nondrought_dt_lst):
            if d == nd:
                drought_common_date_indices.append(i)
                nondrought_common_date_indices.append(ii)
                common_date_lst.append(nd)

    out_drought = [drought_plist[x] for x in drought_common_date_indices]
    out_nondrought = [nondrought_plist[y] for y in nondrought_common_date_indices]
    return out_drought, out_nondrought, common_date_lst


def make_intervals(season_start, season_end, startyear=None, endyear=None):
    smonth, sday = season_start
    emonth, eday = season_end

    year_delta = endyear-startyear
    int_lst = []
    for i in range(year_delta + 1):
        y = startyear + i
        int_lst.append((dt(year=y, month=smonth, day=sday), dt(year=y, month=emonth, day=eday)))

    return int_lst


def dt_from_file(fpath):
    fname = os.path.split(fpath)[-1]
    dt_tif_string = fname.split('_')[-1]
    dt_string = dt_tif_string.strip('.tif')
    dt_obj = dt.strptime(dt_string, '%Y%j')
    return dt_obj


def return_eto_study_files(root, intervals, wildcard):
    eto_files = sorted(glob(os.path.join(root, wildcard)))
    print('eto files \n', eto_files)
    valid_files = []
    dates = []
    for i in intervals:
        s, e = i

        for eto in eto_files:
            eto_dt = dt_from_file(fpath=eto)
            if s <= eto_dt <= e:
                valid_files.append(eto)
                dates.append(eto_dt)
            else:
                pass

    print(f'len of eto files {len(eto_files)} and  len of valid files {len(valid_files)}')
    print('eto dts \n ', [f'{e.year}-{e.month}-{e.day}' for e in dates])
    return valid_files, dates


# start of the growing season
gs_startmonth = 5
gs_startday = 1
# end of the growing season
gs_endmonth = 9
gs_endday = 30
# year interval
start_year = 2011
end_year = 2013


drought_root = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\preprocessing\IL_high_NDVI_Drought_LVL2_plus_rasters'
non_drought_root = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\preprocessing\illinois_high_NDVI_nondrought_rasters'
study_area = 'IL'
drought_lvl = '2'
plot_output = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\histograms'
intervals = make_intervals(season_start=(gs_startmonth, gs_endmonth), season_end=(gs_endmonth, gs_endday),
                           startyear=start_year, endyear=end_year)


# drought days within growing season over the time period
drought_files, drought_days = return_eto_study_files(root=drought_root, intervals=intervals, wildcard='eto_*.tif')
# non drought days within growing season over the time period
non_drought_files, non_drought_days = return_eto_study_files(root=non_drought_root, intervals=intervals, wildcard='eto_*.tif')


# drought and nondrought matching dates
drought_match, nondrought_match, common_dates = get_common_dates(drought_dt_lst=drought_days,
                                                                 nondrought_dt_lst=non_drought_days,
                                                                 drought_plist=drought_files,
                                                                 nondrought_plist=non_drought_files)


print('drought match \n', drought_match[:3])
print('nondrought match \n', nondrought_match[:3])
print('common dates \n', common_dates[:3])

# accumulate arrays:
drought_study_values = accumulate_arrays(drought_match)
print('shape of huge arr \n', drought_study_values.shape)
non_drought_study_values = accumulate_arrays(nondrought_match)

# get means and medians
gm_drought_mean = np.nanmean(drought_study_values)
gm_drought_median = np.nanmedian(drought_study_values)
gm_nondrought_mean = np.nanmean(non_drought_study_values)
gm_nondrought_median = np.nanmedian(non_drought_study_values)

# todo - do a student's t-test
#   https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm
# mu1 = Nondrought mean, mu2 = drought mean
# Null Hypothesis: mu1 = mu2, Alternative Hypothesis, mu1<mu2; Rejection region where T<T_{sgma,v}
# lower tailed critical value ?? Depends on degrees of freedom, and sigma 0.05




fig = plt.figure(figsize=(11, 8))
# todo - Make cols same width: https://stackoverflow.com/questions/41080028/how-to-make-the-width-of-histogram-columns-all-the-same
ax3 = plt.subplot(2, 1, 1)
ax3.hist(drought_study_values,
         bins=50, alpha=0.5, color='blue', label=f"Drought GRIDMET ETo")

ax3.set_xlim([0, 22])
ax3.axvline(gm_drought_mean, color='red', label='Gridmet Drought Mean')
ax3.axvline(gm_drought_median, color='yellow', label='Gridmet Drought Median')
ax3.legend(loc='upper right', prop={'size': 6})
ax3.title.set_text(f'GRIDMET Drought Level {drought_lvl}+ Growing Season ({start_year}-{end_year}), NDVI > 0.7')

ax4 = plt.subplot(2, 1, 2)
ax4.hist(non_drought_study_values,
         bins=50, alpha=0.5, color='green',
         label=f"Non Drought GRIDMET ETo")

ax4.set_xlim([0, 22])
ax4.axvline(gm_nondrought_mean, color='red', label='Gridmet Non Drought Mean')
ax4.axvline(gm_nondrought_median, color='yellow', label='Gridmet Non Drought Median')
ax4.legend(loc='upper right', prop={'size': 6})
ax4.title.set_text(f'GRIDMET Non Drought Growing Season ({start_year}-{end_year}), NDVI > 0.7')
ax4.set_xlabel('ETo in mm')
plt.tight_layout()
plt.savefig(os.path.join(plot_output, f'GM_histo_{study_area}_USDMlvl{drought_lvl}_matching_days.jpeg'))
plt.close()

print(f'GM_histo_{study_area}_USDMlvl{drought_lvl}_matching_days, ({start_year}-{end_year}), NDVI > 0.7')
print(gm_drought_mean, gm_drought_median)
print(f'GRIDMET {study_area} Non Drought Growing Season ({start_year}-{end_year}), NDVI > 0.7')
print((gm_nondrought_mean, gm_nondrought_median))
