import os
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime as dt
import rasterio
from dateutil import relativedelta
from glob import glob
from progressbar import progressbar

def get_tif_arr(tiff_path):

    with rasterio.open(tiff_path) as src:
        arr = src.read(1)
        return arr


def accumulate_arrays(p_list):
    """"""
    print('p list \n', p_list)
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
    return valid_files


# start of the growing season
gs_startmonth = 5
gs_startday = 1
# end of the growing season
gs_endmonth = 9
gs_endday = 30

start_year = 2008
end_year = 2012

drought_root = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\preprocessing\OKwest_high_NDVI_LVL3_rasters'
non_drought_root = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\preprocessing\OKwest_high_NDVI_nondrought_rasters'
study_area = 'OKWest'
drought_lvl = '3'
plot_output = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\histograms'

intervals = make_intervals(season_start=(gs_startmonth, gs_endmonth), season_end=(gs_endmonth, gs_endday),
                           startyear=start_year, endyear=end_year)

drought_files = return_eto_study_files(root=drought_root, intervals=intervals, wildcard='eto_*.tif')

# print('the drought files \n', drought_files)
non_drought_files = return_eto_study_files(root=non_drought_root, intervals=intervals, wildcard='eto_*.tif')

# print('non drought files \n', non_drought_files)

# accumulate arrays:
drought_study_values = accumulate_arrays(drought_files)
print('shape of huge arr \n', drought_study_values.shape)

# fig, ax = plt.subplots()
# ax.hist(drought_study_values, bins=25)
# plt.show()

non_drought_study_values = accumulate_arrays(non_drought_files)

# fig, ax = plt.subplots()
# ax.hist(non_drought_study_values, bins=25)
# plt.show()

# todo - Make cols same width: https://stackoverflow.com/questions/41080028/how-to-make-the-width-of-histogram-columns-all-the-same
ax3 = plt.subplot(2, 1, 1)
ax3.hist(drought_study_values,
         bins=25, alpha=0.5, color='blue', label=f"Drought GRIDMET ETo")
gm_drought_mean = np.nanmean(drought_study_values)
gm_drought_median = np.nanmedian(drought_study_values)

ax3.set_xlim([0, 22])
ax3.axvline(gm_drought_mean, color='red', label='Gridmet Drought Mean')
ax3.axvline(gm_drought_median, color='yellow', label='Gridmet Drought Median')
ax3.legend(loc='upper right', prop={'size': 6})
ax3.title.set_text(f'GRIDMET Drought Level {drought_lvl}+ Growing Season ({start_year}-{end_year}), NDVI > 0.7')

ax4 = plt.subplot(2, 1, 2)
ax4.hist(non_drought_study_values,
         bins=25, alpha=0.5, color='green',
         label=f"Non Drought GRIDMET ETo")
gm_nondrought_mean = np.nanmean(non_drought_study_values)
gm_nondrought_median = np.nanmedian(non_drought_study_values)

ax4.set_xlim([0, 22])
ax4.axvline(gm_nondrought_mean, color='red', label='Gridmet Non Drought Mean')
ax4.axvline(gm_nondrought_median, color='yellow', label='Gridmet Non Drought Median')
ax4.legend(loc='upper right', prop={'size': 6})
ax4.title.set_text(f'GRIDMET Non Drought Growing Season (2011-2013), NDVI > 0.7')
ax4.set_xlabel('ETo in mm')
plt.tight_layout()
plt.savefig(os.path.join(plot_output, f'GM_histo_{study_area}_USDMlvl{drought_lvl}.jpeg'))
# plt.show()
plt.close()

