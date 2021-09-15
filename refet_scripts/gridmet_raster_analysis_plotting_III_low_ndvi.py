import os
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime as dt
from matplotlib.dates import date2num
import matplotlib.dates as mdates
import rasterio
import math
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


def get_common_dates(drought_dt_lst, nondrought_dt_lst, drought_plist, nondrought_plist, drought_levle=None, testout=None):
    """"""

    drought_common_date_indices = []
    nondrought_common_date_indices = []
    common_date_lst = []
    test_common_date_lst = []
    for i, d in enumerate(drought_dt_lst):
        for ii, nd in enumerate(nondrought_dt_lst):
            if d == nd:
                drought_common_date_indices.append(i)
                nondrought_common_date_indices.append(ii)
                common_date_lst.append(nd)

    out_drought = [drought_plist[x] for x in drought_common_date_indices]
    out_nondrought = [nondrought_plist[y] for y in nondrought_common_date_indices]

    # testing -- Make a text file for the drought level dates that are in the common dates
    with open(os.path.join(testout, f'test_{drought_levle}.txt'), 'w') as wfile:
        wfile.write('---common date--- ---out drought--- ---out nondrought ----\n')
        for cdate, od, ond in zip(common_date_lst, out_drought, out_nondrought):
            wfile.write(f'| {cdate} | {od} | {ond} |\n')



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


def student_t_test(array1, array2, level=0.05, outputloc=None, equal_variance=False, ttype='lower_tailed'):
    """
    Two-sample student t-test.
    https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm
    :param array1:
    :param array2:
    :param level:
    :param outputloc:
    :param equal_variance:
    :param ttype:
    :return:
    """

    ttest_types = ['two_tailed', 'upper_tailed', 'lower_tailed']
    if ttype not in ttest_types:
        print('error')

    # calculate test statistic =
    # means
    y_1 = np.nanmean(array1)
    y_2 = np.nanmean(array2)

    # medians - for the paper
    m_1 = np.nanmedian(array1)
    m_2 = np.nanmedian(array2)
    #mins - for the paper
    min_1 = np.nanmin(array1)
    min_2 = np.nanmin(array2)
    # maxs - for the paper
    max_1 = np.nanmax(array1)
    max_2 = np.nanmax(array2)
    # std devs - for the paper
    std_1 = np.nanstd(array1)
    std_2 = np.nanstd(array2)

    # sample 1 variance
    s_1 = np.nanvar(array1)
    s_2 = np.nanvar(array2)

    # Sample sizes
    #https://stackoverflow.com/questions/21778118/counting-the-number-of-non-nan-elements-in-a-numpy-ndarray-in-python
    n_1 = np.count_nonzero(~np.isnan(array1))
    n_2 = np.count_nonzero(~np.isnan(array2))

    # calculate the t-statistic
    t = (y_1 - y_2) / math.sqrt((((s_1**2)/n_1) + ((s_2**2)/n_2)))

    # calculate the degrees of freedom (when you assume that the variances are not the same)
    v = (((s_1/n_1) + (s_2/n_2))**2)/(((s_1/n_1)**2/(n_1 - 1)) + ((s_2/n_2) ** 2/(n_2 - 1)))

    # alternate degrees of freedom if variances were the same
    v_alt = (n_1 + n_2) - 2

    with open(outputloc, 'w') as wfile:
        wfile.write('='*20)
        wfile.write('\n')

        wfile.write('Student T Statistic: \n')
        wfile.write(f'== {t} ==\n')
        wfile.write('\n \n')
        wfile.write('Degrees of Freedom (Assuming the Variances of the two samples are not the same): \n')
        wfile.write(f'== {v} ==\n')
        wfile.write('\n \n')
        wfile.write('Alternate Degrees of Freedom (Assuming the Variances of the two samples ARE the same): \n')
        wfile.write(f'== {v_alt} ==\n')
        wfile.write('\n \n')

        wfile.write('='*20)
        wfile.write('\n')

        wfile.write('Nondrought Array (Array 1) Mean: \n')
        wfile.write(f'== {y_1} ==\n')
        wfile.write('Drought Array (Array 2) Mean: \n')
        wfile.write(f'== {y_2} ==\n')
        wfile.write('\n \n')

        wfile.write('='*20)
        wfile.write('\n')


        wfile.write('Nondrought Array (Array 1) Variance: \n')
        wfile.write(f'== {s_1} ==\n')
        wfile.write('Drought Array (Array 2) Variance: \n')
        wfile.write(f'== {s_2} ==\n')
        wfile.write('\n \n')

        wfile.write('Nondrought Array (Array 1) N1: \n')
        wfile.write(f'== {n_1} ==\n')
        wfile.write('Drought Array (Array 2) N2: \n')
        wfile.write(f'== {n_2} ==\n')
        wfile.write('\n \n')

        wfile.write('Nondrought Array (Array 1) Median: \n')
        wfile.write(f'== {m_1} ==\n')
        wfile.write('Drought Array (Array 2) Median: \n')
        wfile.write(f'== {m_2} ==\n')
        wfile.write('\n \n')

        wfile.write('Nondrought Array (Array 1) Std Dev: \n')
        wfile.write(f'== {std_1} ==\n')
        wfile.write('Drought Array (Array 2) Std Dev: \n')
        wfile.write(f'== {std_2} ==\n')
        wfile.write('\n \n')

        wfile.write('Nondrought Array (Array 1) Min: \n')
        wfile.write(f'== {min_1} ==\n')
        wfile.write('Drought Array (Array 2) Min: \n')
        wfile.write(f'== {min_2} ==\n')
        wfile.write('\n \n')

        wfile.write('Nondrought Array (Array 1) Max: \n')
        wfile.write(f'== {max_1} ==\n')
        wfile.write('Drought Array (Array 2) Max: \n')
        wfile.write(f'== {max_2} ==\n')
        wfile.write('\n \n')

        wfile.write('='*20)
        wfile.write('\n')

        if ttype == 'lower_tailed':
            wfile.write('Referring To: \n https://www.itl.nist.gov/div898/handbook/eda/section3/eda3672.htm\n\n')
            wfile.write('For a lower, one-sided test,\n find the column corresponding to 1-rho and reject the null'
                        ' hypothesis\n if the test statistic is less than\n the negative of the table value.')
        elif ttype == 'upper_tailed':
            wfile.write('Referring To: \n https://www.itl.nist.gov/div898/handbook/eda/section3/eda3672.htm\n\n')
            wfile.write('For an upper, one-sided test, find the column corresponding to 1-α \nand reject the null'
                        ' hypothesis if \nthe test statistic is greater than the table value.')
        elif ttype == 'two_tailed':
            wfile.write('Referring To: \n https://www.itl.nist.gov/div898/handbook/eda/section3/eda3672.htm\n\n')
            wfile.write('For a two-sided test, find the column corresponding to 1-rho/2 and reject the \nnull hypothesis '
                        'if the absolute value of the test statistic \nis greater than the'
                        ' value of t1-rho/2,ν in the table below.')

def chi_square_test():
    """"""
    pass


# start of the growing season
gs_startmonth = 5
gs_startday = 1
# end of the growing season
gs_endmonth = 9
gs_endday = 30
# # year interval
# # IL
# start_year = 2010
# end_year = 2014
# # AZ
# start_year = 2014
# end_year = 2017
# OK
start_year = 2008
end_year = 2012


drought_root = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\preprocessing_III\OKwest_low_NDVI_LVL1_rasters'
non_drought_root = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\preprocessing_III\OKwest_low_NDVI_nondrought_rasters'
study_area = 'OKwest'
drought_lvl = '1'
plot_output = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\histograms_III'
intervals = make_intervals(season_start=(gs_startmonth, gs_endmonth), season_end=(gs_endmonth, gs_endday),
                           startyear=start_year, endyear=end_year)


# drought days within growing season over the time period
drought_files, drought_days = return_eto_study_files(root=drought_root, intervals=intervals, wildcard='eto_*.tif')
# non drought days within growing season over the time period
non_drought_files, non_drought_days = return_eto_study_files(root=non_drought_root, intervals=intervals,
                                                             wildcard='eto_*.tif')


# TODO - is this part working correctly at increasing drought intervals?
# drought and nondrought matching dates
drought_match, nondrought_match, common_dates = get_common_dates(drought_dt_lst=drought_days,
                                                                 nondrought_dt_lst=non_drought_days,
                                                                 drought_plist=drought_files,
                                                                 nondrought_plist=non_drought_files,
                                                                 drought_levle=f'{study_area}_{drought_lvl}',
                                                                 testout=plot_output)



print('drought match \n', drought_match)
print('nondrought match \n', nondrought_match)
print('common dates \n', common_dates)


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
print('running the t test')
student_t_test(array1=non_drought_study_values, array2=drought_study_values, level=0.05,
               outputloc=os.path.join(plot_output, f'{study_area}_LVL{drought_lvl}_stats.txt'), equal_variance=False, ttype='lower_tailed')

fig = plt.figure(figsize=(17, 12))
# todo - Make cols same width: https://stackoverflow.com/questions/41080028/how-to-make-the-width-of-histogram-columns-all-the-same
ax3 = plt.subplot(2, 1, 1)
ax3.hist(drought_study_values,
         bins=50, alpha=0.5,
         color='blue', label=f"Drought GRIDMET ETo")

ax3.set_xlim([0, 22])
ax3.axvline(gm_drought_mean, color='red', label='Gridmet Drought Mean', lw=3)
ax3.axvline(gm_drought_median, color='yellow', label='Gridmet Drought Median', lw=3)
ax3.tick_params(axis='x', labelsize=22)
ax3.tick_params(axis='y', labelsize=22)
ax3.legend(loc='upper right', prop={'size': 22})
# ax3.title.set_text(f'GRIDMET Drought Level {drought_lvl}+ Growing Season ({start_year}-{end_year}), NDVI > 0.7', fontsize=20)
ax3.set_title(f'GRIDMET Drought Level {drought_lvl}+ Growing Season ({start_year}-{end_year}), NDVI < 0.4',
              fontdict={'fontsize': 30, 'fontweight': 'medium'})

ax4 = plt.subplot(2, 1, 2)
ax4.hist(non_drought_study_values,
         bins=50, alpha=0.5, color='green',
         label=f"Non Drought GRIDMET ETo")

ax4.set_xlim([0, 22])
ax4.axvline(gm_nondrought_mean, color='red', label='Gridmet Non Drought Mean', lw=3)
ax4.axvline(gm_nondrought_median, color='yellow', label='Gridmet Non Drought Median', lw=3)
ax4.tick_params(axis='x', labelsize=22)
ax4.tick_params(axis='y', labelsize=22)
ax4.legend(loc='upper right', prop={'size': 22})  # fontsize=18
# ax4.title.set_text(f'GRIDMET Non Drought Growing Season ({start_year}-{end_year}), NDVI > 0.7', fontsize=20)
ax4.set_title(f'GRIDMET Non Drought Growing Season ({start_year}-{end_year}), NDVI < 0.4',
              fontdict={'fontsize': 30, 'fontweight': 'medium'})
ax4.set_xlabel('ETo in mm', fontsize=26)
plt.tight_layout()
plt.savefig(os.path.join(plot_output, f'GM_histo_{study_area}_USDMlvl{drought_lvl}_matching_days_{start_year}_{end_year}_low_ndvi.jpeg'))
plt.close()

print(f'GM_histo_{study_area}_USDMlvl{drought_lvl}_matching_days, ({start_year}-{end_year}), NDVI < 0.4')
print(gm_drought_mean, gm_drought_median)
print(f'GRIDMET {study_area} Non Drought Growing Season ({start_year}-{end_year}), NDVI > 0.7')
print((gm_nondrought_mean, gm_nondrought_median))
