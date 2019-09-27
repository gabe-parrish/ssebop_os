# ===============================================================================
# Copyright 2019 Gabriel Parrish, Matt Schauer and Gabriel Senay
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
import gdal
from gdalconst import *
import numpy as np
import glob, os
import tarfile
import math
import shutil
from datetime import datetime
# ============= standard library imports ========================
from utils.os_utils import windows_path_fix

# # Establish the ESRI environmental settings
# arcpy.CheckOutExtension("spatial")
# arcpy.env.overwriteOutput = True

# NEED to register the GDAL driver to read/write ESRI, etc.

# Choose the directory where the Landsat '.tar.gz.' files are located
# directory = input(r"Enter filepath to Landsat files: ")
directory = windows_path_fix(r'Z:\Users\Gabe\OverpassETa\Iraq')
#aux_inputdir = raw_input('Enter filepath to other inputs:')
aux_inputdir = directory + os.sep + 'Inputs'
print('input directory: {}'.format(aux_inputdir))
k_input = 1

# Establish scratch, output, and backup folders
# Outputs is where the final rasters will be located
output = directory + os.sep + 'Outputs'
if not os.path.exists(output):
    os.mkdir(output)
# Backup is where the Landsat '.tar.gz' files will be placed after using them
backup = directory + os.sep + 'Backup'
if not os.path.exists(backup):
    os.mkdir(backup)
# scratch is where the raw bands will be unzipped and intermediate data will be processed
# scratch will be deleted at the end
scratch = directory + os.sep + 'scratch'
if not os.path.exists(scratch):
    os.mkdir(scratch)

# Find the current time to set the timer for the process
ProcessStartTime = datetime.now()
# Create scene folders and place corresponding unzipped .tar.gz files in them
tarfiles = glob.glob(directory + os.sep + '*.tar.gz')
number = len(tarfiles)
print('there are', str(number), 'Landsat images to process')

logfile = open(output + os.sep + 'Cfactors' + '.txt','a')
logfile.write("SceneDate" + " " + "Cfactor" + "\n")
logfile.close()


for i in tarfiles:
    SceneStartTime = datetime.now()
    basename = os.path.basename(i)
    scenedate = str(basename[-30:-22])  # returns YYYYMMDD ie 20040703
    scenefolder = scratch + os.sep + str(scenedate)  # create a folder for the image date
    if not os.path.exists(scenefolder):
        os.mkdir(scenefolder)
    shutil.move(i, scenefolder)  # moves the scene tarfile to the new folder
    zippedscene = scenefolder + os.sep + basename
    landsatNumber = str(basename[3:4])

    print
    'Landsat', str(landsatNumber), 'Image'
    print
    'Calendar Date:', scenedate
    print
    "Unzipping bands..."

    # Unzip/Extract .tar.gz file ----> Extracts all Bands, Metadata
    tar = tarfile.open(zippedscene)
    for item in tar:
        tar.extract(item, path=scenefolder)
    tar.close()
    # Move the .tar.gz file to the backup directory
    shutil.move(zippedscene, backup)

    # Get metadata file from unzipped scenefolder
    metadata = scenefolder + os.sep + basename[:-7] + "_MTL" + '.txt'

    # establish the workspace environment to the scene folder for intermediate files
    arcpy.env.workspace = scenefolder


    # function to classify the BQA - Landsat Quality Assessment Band into a cloud mask
    def cloudMask(bqaband):
        if landsatNumber == '5' or landsatNumber == '7':
            cloudmask = Con(bqaband == 672, 0, 1)  # 672 is the "clear" pixel flag in the BQA for L5/L7
        if landsatNumber == '8':
            cloudmask = Con(bqaband == 2720, 0, 1)  # 2720 is the "clear" pixel flag in the BQA for L8
        return cloudmask


    # function to convert the raw red and nir bands to top-of-atmosphere reflectance and
    # then calculate NDVI
    # also calculates the radiance from the thermal band digital numbers (DN)
    def L57_reflect_NDVI(redband, nirband):
        # Conversion of red and NIR bands from DN to top-of-atmosphere reflectance
        red_radiance = ((Ldiff3 / Qcaldiff) * (Float(redband) - Qcalmin) + Lmin3)  # Conversion to Radiance
        red_reflect = (3.14159 * red_radiance * d2) / (esun3 * zenith)  # Radiance to Reflectance
        nir_radiance = ((Ldiff4 / Qcaldiff) * (Float(nirband) - Qcalmin) + Lmin4)  # Conversion to Radiance
        nir_reflect = (3.14159 * nir_radiance * d2) / (esun4 * zenith)  # Radiance to Reflectance

        # Calculate Top-of-Atmosphere Reflectance NDVI
        ndvi = (Float(nir_reflect) - Float(red_reflect)) / (Float(nir_reflect) + Float(red_reflect))
        return ndvi


    def L8_reflectNDVI(redband, nirband):
        # Conversion of red and NIR bands from DN to top-of-atmosphere reflectance
        red_reflect1 = (Float(redband) * 0.00002) + (-0.1)  # TOA reflectance w/o correction for solar angle
        red_reflect = (red_reflect1 / zenith)  # TOA planetary reflectance
        nir_reflect1 = (Float(nirband) * 0.00002) + (-0.1)  # TOA reflectance w/o correction for solar angle
        nir_reflect = (nir_reflect1 / zenith)  # TOA planetary reflectance

        # Calculate Top-of-Atmosphere Reflectance NDVI
        ndvi = (Float(nir_reflect) - Float(red_reflect)) / (Float(nir_reflect) + Float(red_reflect))
        return ndvi


    def thermalRadiance(thermalband):
        if landsatNumber == '5' or landsatNumber == '7':
            # Process the thermal band 6 DN to Radiance
            thermal_radiance = ((Ldiff6 / Qcaldiff) * (Float(thermalband) - Qcalmin) + Lmin6)  # Conversion to Radiance
        if landsatNumber == '8':
            # Band 10 DN conversion to Radiance
            thermal_radiance = ((Float(thermalband) * ML10value) + AL10value)  # Conversion to Radiance
        return thermal_radiance


    # function to create NDVI-corrected Emissivity and Land surface temperature
    def surfacetemp(thermal_radiance, ndvi):
        # LST calculation -- created using corrected thermal radiance
        tnb = 0.866  # narrow band transmissivity of air
        rp = 0.91  # path radiance
        rsky = 1.32  # narrow band downward thermal radiation from a clear sky

        # Emissivity correction algorithm based on NDVI, not LAI
        ndviRangevalue = Con((ndvi >= 0.2) & (ndvi <= 0.5), ndvi)  # collects a range of NDVI
        Pv = ((ndviRangevalue - 0.2) / 0.3) ** 2
        dE = ((1 - 0.97) * (1 - Pv) * (0.55) * (
            0.99))  # Assuming typical Soil Emissivity of 0.97 and Veg Emissivity of 0.99 and shape Factor mean value of 0.553
        RangeEmiss = ((0.99 * Pv) + (0.97 * (1 - Pv)) + dE)

        # calculation of NDVI-derived emissivity
        Emissivity = Con(ndvi < 0, 0.985, Con((ndvi >= 0) & (ndvi < 0.2), 0.977,
                                              Con(ndvi > 0.5, 0.99, Con((ndvi >= 0.2) & (ndvi <= 0.5), RangeEmiss))))

        # calculation of land surface temperature in degrees Kelvin
        rc = ((thermal_radiance - rp) / tnb) - ((rsky) * (1 - Emissivity))
        lst = (K2 / Ln(((K1 * Emissivity) / rc) + 1))
        return lst


    def maskclouds(raster):
        maskedRas = Con(cloudmask == 0, raster)
        return maskedRas


    if landsatNumber == '5':
        # Bands 3,4,6 Radiance Constants (landsat 5)
        Lmax3 = 264
        Lmin3 = -1.17
        Ldiff3 = 265.17
        Lmax4 = 221
        Lmin4 = -1.51
        Ldiff4 = 222.51
        Lmax6 = 15.303
        Lmin6 = 1.238
        Ldiff6 = 14.065
        Qcalmax = 255
        Qcalmin = 1
        Qcaldiff = 254

        # LST Radiance to Temperature Constants (landsat 5)
        K1 = 607.76
        K2 = 1260.56

        # NDVI Reflectance Coefficients
        esun3 = 1533  # Band 3 Spectral Irradiance
        esun4 = 1039  # Band 4 Spectral Irradiance

        # Open metadata file and get sun elevation and Earth/Sun Distance values
        metafile = open(metadata, 'r')
        for line in metafile:
            if "EARTH_SUN_DISTANCE" in line:
                esdvalue = line.split()[-1]
            if "SUN_ELEVATION" in line:
                elevalue = line.split()[-1]
        metafile.close()

        sunelev = float(elevalue)
        zenith = math.cos(90 - sunelev)  # calculate solar zenith
        d2 = float(esdvalue) * float(esdvalue)  # earth sun distance--squared

        # Find the Red, near-Infrared Red, thermal, and quality assessment Landsat Bands
        redband = arcpy.Raster(scenefolder + os.sep + basename[:-7] + "_B3" + '.tif')
        nirband = arcpy.Raster(scenefolder + os.sep + basename[:-7] + "_B4" + '.tif')
        thermalband = arcpy.Raster(scenefolder + os.sep + basename[:-7] + "_B6" + '.tif')
        bqaband = arcpy.Raster(scenefolder + os.sep + basename[:-7] + "_BQA" + '.tif')

        # Run Cloud Mask classification function on the BQA band
        print
        'Reducing QA Band to Cloud Mask'
        cloudmask = cloudMask(bqaband)

        # Run the Top-of-Atmosphere Reflectance NDVI and Thermal Radiance function on the Red, NIR, and Thermal bands
        print
        'Creating NDVI'
        ndvi = L57_reflect_NDVI(redband, nirband)

        # Use the thermal radiance and NDVI to calculate Emissitivity and final LST
        print
        'Creating land surface temperature'
        thermal_radiance = thermalRadiance(thermalband)
        lst = surfacetemp(thermal_radiance, ndvi)

        del zenith, d2, esdvalue

    if landsatNumber == '7':
        # Bands 3,4,6 Radiance Constants (landsat 7)
        Qcalmax = 255
        Qcalmin = 1
        Qcaldiff = 254

        # LST Radiance to Temperature Constants (landsat 7)
        K1 = 666.09
        K2 = 1282.71

        # NDVI Reflectance Coefficients
        esun3 = 1533  # Band 3 Spectral Irradiance
        esun4 = 1039  # Band 4 Spectral Irradiance

        # Open metadata file and get sun elevation and Earth/Sun Distance values
        metafile = open(metadata, 'r')
        for line in metafile:
            if "EARTH_SUN_DISTANCE" in line:
                esdvalue = line.split()[-1]
            if "SUN_ELEVATION" in line:
                elevalue = line.split()[-1]
            if "RADIANCE_MINIMUM_BAND_3" in line:
                Lmin3value = line.split()[-1]
                Lmin3 = float(Lmin3value)
            if "RADIANCE_MAXIMUM_BAND_3" in line:
                Lmax3value = line.split()[-1]
                Lmax3 = float(Lmax3value)
            if "RADIANCE_MINIMUM_BAND_4" in line:
                Lmin4value = line.split()[-1]
                Lmin4 = float(Lmin4value)
            if "RADIANCE_MAXIMUM_BAND_4" in line:
                Lmax4value = line.split()[-1]
                Lmax4 = float(Lmax4value)
            if "RADIANCE_MINIMUM_BAND_6_VCID_1" in line:
                Lmin6value = line.split()[-1]
                Lmin6 = float(Lmin6value)
            if "RADIANCE_MAXIMUM_BAND_6_VCID_1" in line:
                Lmax6value = line.split()[-1]
                Lmax6 = float(Lmax6value)
        metafile.close()

        Ldiff3 = Lmax3 - Lmin3
        Ldiff4 = Lmax4 - Lmin4
        Ldiff6 = Lmax6 - Lmin6

        sunelev = float(elevalue)
        zenith = math.cos(90 - sunelev)  # calculate solar zenith
        d2 = float(esdvalue) * float(esdvalue)  # earth sun distance--squared

        # Find the Red, near-Infrared Red, thermal, and quality assessment Landsat Bands
        redband = arcpy.Raster(scenefolder + os.sep + basename[:-7] + "_B3" + '.tif')
        nirband = arcpy.Raster(scenefolder + os.sep + basename[:-7] + "_B4" + '.tif')
        thermalband = arcpy.Raster(scenefolder + os.sep + basename[:-7] + "_B6_VCID_1" + '.tif')
        bqaband = arcpy.Raster(scenefolder + os.sep + basename[:-7] + "_BQA" + '.tif')

        # Run Cloud Mask classification function on the BQA band
        print
        'Reducing QA Band to Cloud Mask'
        cloudmask = cloudMask(bqaband)

        # Run the Top-of-Atmosphere Reflectance NDVI and Thermal Radiance function on the Red, NIR, and Thermal bands
        print
        'Creating NDVI'
        ndvi = L57_reflect_NDVI(redband, nirband)

        # Use the thermal radiance and NDVI to calculate Emissitivity and final LST
        print
        'Creating land surface temperature'
        thermal_radiance = thermalRadiance(thermalband)
        lst = surfacetemp(thermal_radiance, ndvi)

        del zenith, d2, esdvalue

    if landsatNumber == '8':
        # LST Radiance to Temperature Coefficients (Landsat 8 Constants)
        K1 = 774.89  # band 10
        K2 = 1321.08  # band 10

        # Open metadata file and get sun elevation and Earth/Sun Distance values
        metafile = open(metadata, 'r')
        for line in metafile:
            if "EARTH_SUN_DISTANCE" in line:
                esdvalue = line.split()[-1]
            if "SUN_ELEVATION" in line:
                elevalue = line.split()[-1]
            if "RADIANCE_MULT_BAND_10" in line:
                ML10 = line.split()[-1]
                ML10value = float(ML10)
            if "RADIANCE_ADD_BAND_10" in line:
                AL10 = line.split()[-1]
                AL10value = float(AL10)
        metafile.close()

        sunelev = float(elevalue)
        zenith = math.cos(90 - sunelev)  # calculate solar zenith

        # Find the Red, near-Infrared Red, thermal, and quality assessment Landsat Bands
        redband = arcpy.Raster(scenefolder + os.sep + basename[:-7] + "_B4" + '.tif')
        nirband = arcpy.Raster(scenefolder + os.sep + basename[:-7] + "_B5" + '.tif')
        thermalband = arcpy.Raster(scenefolder + os.sep + basename[:-7] + "_B10" + '.tif')
        bqaband = arcpy.Raster(scenefolder + os.sep + basename[:-7] + "_BQA" + '.tif')

        # Run Cloud Mask classification function on the BQA band
        print
        'Reducing QA Band to Cloud Mask'
        cloudmask = cloudMask(bqaband)

        # Run the Top-of-Atmosphere Reflectance NDVI and Thermal Radiance function on the Red, NIR, and Thermal bands
        print
        'Creating NDVI'
        ndvi = L8_reflectNDVI(redband, nirband)

        # Use the thermal radiance and NDVI to calculate Emissitivity and final LST
        print
        'Creating land surface temperature'
        thermal_radiance = thermalRadiance(thermalband)
        lst = surfacetemp(thermal_radiance, ndvi)

        del zenith

        # Use the function to mask out clouds from both NDVI and LST
    maskedNDVI = maskclouds(ndvi)
    maskedLST = maskclouds(lst)


    def outputfile(raster, cat):
        # Create a new category folder
        outfolder = output + os.sep + cat
        if not os.path.exists(outfolder):
            os.mkdir(outfolder)
        outfile = outfolder + os.sep + cat.lower() + scenedate + '.tif'
        arcpy.CopyRaster_management(raster, outfile, "32_BIT_FLOAT")


    outNDVI = outputfile(maskedNDVI, 'NDVI')
    print
    'Created NDVI file.'
    outLST = outputfile(maskedLST, 'LST')
    print
    'Created LST file.'

    print
    'Preprocessing of Landsat scene complete.'
    print
    'Starting ETf/ETa SSEBop model.'

    year = str(scenedate[:-4])
    month = str(scenedate[-4:-2])
    day = int(scenedate[-2:])
    if int(day) in range(1, 11):
        dekad = '1'
    if int(day) in range(11, 21):
        dekad = '2'
    if int(day) in range(21, 32):
        dekad = '3'
    dekadal = str(month) + dekad
    d = datetime.strptime(scenedate, '%Y%m%d')
    jdate = d.strftime('%Y%j')[-3:]

    # find the appropriate input rasters for tmax, dt, and eto
    print
    "finding the Tmax, dT, and ETo inputs"
    tmax = arcpy.Raster(aux_inputdir + os.sep + 'tmax_dekadal' + os.sep + 'tmax' + dekadal + '.tif')
    dt = arcpy.Raster(aux_inputdir + os.sep + 'dT_dekadal' + os.sep + 'dt' + dekadal + '.tif')
    eto = arcpy.Raster(aux_inputdir + os.sep + 'ETo_daily' + os.sep + 'eto' + jdate + '.tif')

    # establish the arcpy environmental settings
    arcpy.env.extent = "MINOF"
    arcpy.env.cellSize = "MINOF"
    arcpy.env.workspace = scenefolder


    # Function to calculate the cfactor
    def cfactor(ndviRas, lstRas):
        tcorr = (lstRas / tmax)
        tdiff = (tmax - lstRas)
        tcorr2 = Con((lstRas > 270) & (tdiff > -5) & (tdiff < 10) & (ndviRas > 0.7) & (ndviRas < 1.0), tcorr)
        tcorr3 = maskclouds(tcorr2)
        mu = tcorr3.mean
        sigma = tcorr3.standardDeviation
        if mu > 0.0:
            cfactor = float(mu - (sigma * 2))
        else:
            print
            'cfactor algorithm failed. using the default cfactor of 0.985'
            cfactor = float(0.985)
        logfile = open(output + os.sep + 'Cfactors' + '.txt', 'a')
        logfile.write(str(scenedate) + " " + str(cfactor) + "\n")
        logfile.close()
        return cfactor


    # Function to calculate the SSEBop ET fraction
    def ssebopETf(lstRas, cfactor):
        # restrict the range of dT
        dtcon = Con(dt < 6, 6, dt)  # conditions low dT below 6 degrees Kelvin and makes it 6
        dtcon2 = Con(dtcon > 25, 25, dtcon)  # conditions high dT above 25 degrees Kelvin and makes it 25

        # SSEBop Model
        print
        'calculating SSEBop ET Fraction'
        Tcold = tmax * cfactor
        Thot = Tcold + dtcon2
        ETf = (Thot - lstRas) / dtcon2
        ETfCon = Con(ETf < 0, 0, Con((ETf >= 0) & (ETf <= 1.05), ETf, Con((ETf > 1.05) & (ETf < 1.3), 1.05)))
        maskedETf = maskclouds(ETfCon)
        return maskedETf


    # Function to calculate the daily actual ET - requires the ETf and a k factor
    def ssebopETa(etf, k):
        print
        "calculating actual ET with k-factor of", str(k)
        ETa = etf * (eto * float(k))
        ETacon = Con(ETa < 0, 0, ETa)
        maskedETa = maskclouds(ETacon)
        return maskedETa


    # Calculate Actual ET with ETo with k_input
    print
    'calculating the cfactor'
    cfactor = cfactor(maskedNDVI, maskedLST)
    print
    'cfactor:', str(cfactor)
    print
    'calculating SSEBop ET Fraction'
    k = k_input
    maskedETf = ssebopETf(maskedLST, cfactor)
    outETf = outputfile(maskedETf, 'ETf')
    print
    'Created ETf file.'
    etf = arcpy.Raster(output + os.sep + 'ETf' + os.sep + 'etf' + scenedate + '.tif')
    maskedETa = ssebopETa(etf, k)
    outETa = outputfile(maskedETa, 'ETa')
    print
    'Created ETa file.'
    print
    "SSEBop ET Fraction and Actual ET created"

    timeEnd = str(datetime.now() - SceneStartTime)
    print
    'Total Time to complete scene:', str(timeEnd)

# Delete the Scratch folder and intermediate data
print('deleting the scratch folder', shutil.rmtree(directory + os.sep + 'scratch'))

processtime = str(datetime.now() - ProcessStartTime)

print('Entire time to process', str(number), 'Landsat scenes:', str(processtime))