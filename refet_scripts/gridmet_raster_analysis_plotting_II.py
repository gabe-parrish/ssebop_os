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
import seaborn as sns


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

start_year = 2011
end_year = 2013

drought_root = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\preprocessing\OKeast_high_NDVI_drought_rasters'
non_drought_root = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\preprocessing\OKeast_high_NDVI_nondrought_rasters'
study_area = 'OK_East'
drought_lvl = '1'
plot_output = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\histograms'
intervals = make_intervals(season_start=(gs_startmonth, gs_endmonth), season_end=(gs_endmonth, gs_endday),
                           startyear=start_year, endyear=end_year)


print('drought intervals \n', intervals)


# for each interval,
drought_files, drought_days = return_eto_study_files(root=drought_root, intervals=intervals, wildcard='eto_*.tif')


print('the drought files \n', drought_files)
non_drought_files, non_drought_days = return_eto_study_files(root=non_drought_root, intervals=intervals, wildcard='eto_*.tif')


drought_match, nondrought_match, common_dates = get_common_dates(drought_dt_lst=drought_days,
                                                                 nondrought_dt_lst=non_drought_days,
                                                                 drought_plist=drought_files,
                                                                 nondrought_plist=non_drought_files)


print('drought match \n', drought_match[:3])
print('nondrought match \n', nondrought_match[:3])
print('common dates \n', common_dates[:3])


drought_means = average_arrays(p_list=drought_match)
nondrought_means = average_arrays(p_list=nondrought_match)


# # todo - take the common dates and plot the mean values against each other...
common_dates = [i.date() for i in common_dates]


# make an array of the difference between the drought mean and nondrought means.
drought_diff = [x-y for x, y in zip(drought_means, nondrought_means)]

# make an array of zeros to make the one to one line obvious
zeros = [0 for x in drought_diff]

# make a dataframe to make using seaborn easier...
df = pd.DataFrame({'ETo_drought': drought_means,
                   'ETo_nondrought': nondrought_means,
                   'Dates': common_dates, 'delta_ETo': drought_diff})

# plot a timeseries of drought differentials
fig, ax = plt.subplots(figsize=(11, 8))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax.bar(common_dates, drought_diff, color='red', label='Drought Difference (mm)')
ax.grid(True)
ax.legend(loc='lower right')
ax.set_title(f'Drought Difference in Mean ETo Timeseries')
ax.set_xlabel('Date')
ax.set_ylabel('Drought ETo - Non-Drought ETo (mm)')
# plt.show()
plt.savefig(os.path.join(plot_output, f'DeltaETo_TS_{study_area}_lvl{drought_lvl}.jpeg'))
plt.show()


# fig, ax = plt.subplots(figsize=(11, 8))
# ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
# ax.set_title(f'Drought Difference in Mean ETo Timeseries')
# ax.set_xlabel('Date')
# ax.set_ylabel('Drought ETo - Non-Drought ETo (mm)')
# sns.barplot(x='Dates', y='delta_ETo', data=df, ax=ax)
# plt.savefig(os.path.join(plot_output, f'DeltaETo_TS_{study_area}_lvl{drought_lvl}.jpeg'))


# fig, ax = plt.subplots(figsize=(11, 8))
# # fig.set_size_inches(11, 8)
# ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
# # ax.plot(common_dates, drought_means, color='red', label='Drought ETo Mean')
# # ax.scatter(common_dates, drought_means, edgecolor='red', facecolor=None)
# ax.bar(common_dates, drought_means, color='red', label='Drought ETo Mean')
# # ax.scatter(common_dates, drought_means, edgecolor='red', facecolor=None)
# # ax.plot(common_dates, nondrought_means, color='blue', label='Non Drought ETo Mean')
# ax.bar(common_dates, nondrought_means, color='blue', label='Non Drought ETo Mean')
# ax.grid(True)
# ax.legend(loc='lower right')
# ax.set_title(f'Drought and Nondrought Mean ETo Timeseries')
# ax.set_xlabel('Date')
# ax.set_ylabel('ETo (mm)')
# # plt.show()
# plt.savefig(os.path.join(plot_output, f'MeanETo_TS_{study_area}_lvl{drought_lvl}.jpeg'))
