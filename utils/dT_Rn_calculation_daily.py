#-------------------------------------------------------------------------
# Created: September 2019
# VERSION: ArcGIS 10.6.1
# AUTHOR: Stefanie Kagone
# TOOL DESCRIPTION: calculates the Rn and dT for ET model V5
# ---------------------------------------------------------------------------

# Import system modules
import arcpy
import os
import sys
import time
import traceback
from arcpy.sa import *
import requests
import logging
import datetime

arcpy.CheckOutExtension("Spatial")
#Overwriting the Output
arcpy.OverwriteOutput = True
arcpy.pyramid = "NONE"
arcpy.rasterstatistics = "STATISTICS" #"NONE"
arcpy.loghistory = True

# determine cell size this way because of a bug that wouldnt allow to use a raster path as input
# sourcefile = r'C:\WaterSmart\Users\Stefanie\Projects\dT_GOES\01-07-2018\Rs2018_182.tif'
# cellsize = '{0}'.format(arcpy.Describe(sourcefile).meanCellWidth, arcpy.Describe(sourcefile).meanCellHeight)
# print(cellsize)
# arcpy.env.cellSize = cellsize  #0.009 #"MINOF" #NV0.0025
#arcpy.env.extent = "MAXOF"
#arcpy.env.snapRaster = 'M:\\WaterSmart\\operational\\US_operational\\USA\\misc_DATA\\snap.tif'

OutputPath = os.path.join(r'C:\WaterSmart\Users\Stefanie\Projects\dT_GOES\daily_dT')
if not os.path.exists(OutputPath):
    os.makedirs(OutputPath)

time_stamp = time.strftime('%Y.%m.%d_%H.%M.%S', (time.localtime(time.time())))
strFile = OutputPath + os.sep + "Log_%s.txt" %time_stamp #OutputPath +
logfile = open(strFile, "a")
logfile.write('ETa calculation Version RdT \n')
logfile.write("\n")
logfile.write("Calculation has following steps: " + "\n")
logfile.write("1. determine Net Radiation (Rn) " + "\n")
logfile.write("Equations according to FAO Irrigation and Drainage Paper No. 56, Allen et al. " + "\n")
logfile.write("Rn = Rns - Rnl " + " (Equation 40 - page 53)" + "\n")
logfile.write("where:" + "\n")
logfile.write("Rns      - incoming net shortwave radiation using GOES satellite data" + "\n")
logfile.write("Rnl      - outgoing net longwave radiation using GOES satellite data" + "\n")
logfile.write("\n")
logfile.write("2. determine Temperature difference (dT) " + "\n")
logfile.write("dT = (Rn * cofrs) / (den * cp * 86400) " + "\n")
logfile.write("where:" + "\n")
logfile.write("Rn       - Net Radiation" + "\n")
logfile.write("crfrs    - crop restistence factor" + "\n")
logfile.write("den      - density" + "\n")
logfile.write("cp       - specific heat at constant pressure" + "\n")
logfile.write("\n")
logfile.write("General Input data: " + "\n")
logfile.write("Output path:" + str(OutputPath) + "\n")

logfile.write("Start dT/Rn process" + "\n") 
logfile.write("\n")

year = 2018  #  input("Enter year(yyyy): ")
logfile.write("Enter year(yyyy): " + str(year) + "\n")

try:
    OutputPath_sdt = os.path.join(OutputPath, str(year))
    if not os.path.exists(OutputPath):
        os.makedirs(OutputPath)
    dem = arcpy.Raster(r'C:\WaterSmart\Data\Elevation\mn30_grd\mn30_grd_usa')
    logfile.write('Elevation file: ' + str(dem) + '\n')
    alb_value = 0.23
    cofrs = 110

    TempAvg_path = r'C:\WaterSmart\Data\Temperature\USA\Daymet\daymetV3\Tavg_19852014\daily'
    arcpy.env.workspace = TempAvg_path
    tempavgs = arcpy.ListRasters()
    tempavgs.sort()
    logfile.write("TempAvg: " + str(TempAvg_path) + '\n')

    Rnl_path = r'C:\WaterSmart\Users\Stefanie\Projects\dT_GOES\Rnl_median0418'
    arcpy.env.workspace = Rnl_path
    rnls = arcpy.ListRasters()
    rnls.sort()
    logfile.write("Rnl: " + str(Rnl_path) + '\n')

    Rs_path = r'C:\WaterSmart\Users\Stefanie\Projects\dT_GOES\Rs_median0418'
    arcpy.env.workspace = Rs_path
    rss = arcpy.ListRasters()
    rss.sort()
    logfile.write("Rnl: " + str(Rs_path) + '\n')

    for temp_avg in tempavgs:
        for Rnl in rnls:
            for Rs in rss:
                if Rs.split('.')[0][-3:] == Rnl.split('.')[0][-3:] == temp_avg.split('.')[0][-3:]:
                    jdate = temp_avg.split('.')[0][-3:]
                    print('Computing dT for day ' + jdate)
                    logfile.write('Computing dT for day ' + jdate + '\n')
                    print(Rnl, Rs)

                    #Calculate Rns, Rn
                    Rns = (1 - alb_value) * arcpy.Raster(os.path.join(Rs_path, Rs))
                    # Rns.save(os.path.join(OutputPath, 'Rns' + jdate))
                    Rn = Rns - abs(arcpy.Raster(os.path.join(Rnl_path, Rnl)))   # use abs since RNl is minus (minus minus = plus)
                    Rn.save(os.path.join(OutputPath, 'Rn' + jdate))

                    # dT
                    print('here now')
                    varf = 0.0065 * dem
                    vare = (293.0 - varf) / 293.0
                    P = 101.3 * Power(vare, 5.26)
                    # T in K
                    Tkv = 1.01 * arcpy.Raster(os.path.join(TempAvg_path, temp_avg))
                    den = 3.486 * (P/Tkv)
                    # den.save(OutputPath + os.sep + 'den' + jdate)
                    cp = 1.013 / 1000

                    lowerf = (den * cp * 86400)
                    # lowerf.save(os.path.join(OutputPath, 'lowerf' + jdate))
                    dT = (Rn * cofrs) / lowerf
                    dTc = arcpy.sa.Int(arcpy.sa.Con(dT < 1, 1, dT) + 0.5)
                    dTc = arcpy.sa.Con(dT < 1, 1, dT)
                    dTc.save(os.path.join(OutputPath_sdt, 'dT' + jdate + '.tif'))
                    print('dT' + jdate)

    logfile.close()
    os.startfile(strFile)


except Exception as exc:
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    pymsg = ('PYTHON ERRORS:\nTraceback Info:\n' + tbinfo + '\nError Info:\n       ' + str(exc))
    arcpy.AddError(pymsg)