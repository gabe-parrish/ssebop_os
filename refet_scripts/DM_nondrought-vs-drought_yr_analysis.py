
from rasterstats import zonal_stats


# file = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\2012figs\annual_analysis\pet2012_minus_medpet_0115_annual.tif'
file = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\IL_2009_vs_2012_diff_ETo_mm.tif'
shapefile = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\IL_BNDY_State\IL_BNDY_State_Py_4326.shp'

# https://kodu.ut.ee/~kmoch/geopython2019/L4/raster.html#calculating-zonal-statistics
stats = zonal_stats(shapefile, file, stats=['mean', 'median', 'sum', 'count'])

print(stats)

