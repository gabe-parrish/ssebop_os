# Import system modules
import arcpy
from arcpy.sa import *
from arcpy import env
import glob, os
import tarfile
import math, fnmatch
import shutil, datetime

"""Python Script by MSchauer to do SSEBop on a given scene."""

arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = True

directory = raw_input("Enter path to Landsat .tar.gz files:")
#inputtable = directory + os.sep + "EarthSunDistanceTable.txt" # This can also be acquired from Landsat metadata file

output = directory + os.sep + 'Outputs'
if not os.path.exists(output):
    os.mkdir(output)
#Backup
backup = directory + os.sep + 'Backup'
if not os.path.exists(backup):
    os.mkdir(backup)
#scratch
scratch = directory + os.sep + 'scratch'
if not os.path.exists(scratch):
    os.mkdir(scratch)

# Create scene folders and place corresponding unzipped .tar.gz files in them
for filename in os.listdir(directory):
    if fnmatch.fnmatch(filename, '*.gz'):  #skips over scratch folder
        print filename
        scenepath = directory + os.sep + filename
         #----------- For Collection 1 -------------------#
        scenedate = str(filename)[-30:-22] #returns YYYYMMDD ie 20040703
        print scenedate
        scenefolder = scratch + os.sep + str(scenedate) 
        if not os.path.exists(scenefolder):
            os.mkdir(scenefolder)
        shutil.move(scenepath,scenefolder)
        
for f in sorted(os.listdir(scratch)):
    if f.startswith(('1', '2')): 
        env.workspace = scratch + os.sep + f
        inputdir = env.workspace
        for filename in os.listdir(inputdir):
            openfile = inputdir + os.sep + filename
    
        metafilepath = inputdir + os.sep + "*.txt"
        #----------- For Collection 1 -------------------#            
        Landsat = str(filename)[3:4]

        date_from_file = str(filename)[17:25] #[-30:-22]
#        updated_date = date_from_file[:4] + ' ' + date_from_file[4:6] + ' ' + date_from_file[6:]
#        print 'Calendar Date:',str(updated_date)
#        date_obj = datetime.datetime.strptime(updated_date, '%Y %m %d')
#        jdate = date_obj.strftime('%j')
#        year = date_from_file[:4]
#        scenedate = date_from_file[:4] + date_obj.strftime('%j')
        scenedate = str(date_from_file)
        print 'Calendar Date:', scenedate

        remfolder = directory + os.sep + scenedate
        
        print "Landsat " + str(Landsat)
#        print "Year is " + str(year)
#        print "Day is " + str(jdate)
        print "Unzipping bands..."

        # Unzip/Extract .TAR file ----> Bands,Metadata table
        tar = tarfile.open(openfile)
        for item in tar:
            tar.extract(item, path=inputdir)
        # Move the .tar.gz file to directory, delete unzipped contents of subfolders
        tar.close()
        shutil.move(openfile,backup)
        
        def cloudMask(qaband):
            print 'Reducing QA Band to Cloud Mask'
            if Landsat == '5' or Landsat == '7':
                cloudmask = Con(qaband == 672,0,1)
            if Landsat == '8':
                cloudmask = Con(qaband == 2720,0,1)
            return cloudmask
                
        def surfacetemp(lst,ndvi):
            print 'Creating land surface temperature'
            # LST calculation (2/2) -- created using corrected thermal radiance
            # This is a combination of correction methods from Sobrino & Allen, creating similar results to METRIC LST
                
            tnb = 0.866  # narrow band transmissivity of air
            rp = 0.91    # path radiance
            rsky = 1.32  # narrow band downward thermal radiation from a clear sky

            # Emissivity correction algorithm based on NDVI, not LAI
            ndviRangevalue = Con((ndvi >= 0.2) & (ndvi <= 0.5), ndvi)
            Pv = ((ndviRangevalue - 0.2) / 0.3) ** 2
            dE = ((1 - 0.97) * (1 - Pv) * (0.55) * (0.99))# Assuming typical Soil Emissivity of 0.97 and Veg Emissivity of 0.99 and shape Factor mean value of 0.553
            RangeEmiss = ((0.99 * Pv) + (0.97 * (1 - Pv)) + dE)
            Emissivity = Con(ndvi < 0, 0.985, Con((ndvi >= 0) & (ndvi < 0.2), 0.977, Con(ndvi > 0.5, 0.99, Con((ndvi >= 0.2) & (ndvi <= 0.5), RangeEmiss))))
            rc = ((lst - rp) / tnb) - ((rsky) * (1 - Emissivity))
            finallst = (K2 / Ln(((K1 * Emissivity) / rc) + 1))
            return finallst
         
        if Landsat == '5':
            #print 'filename is ' + str(filename) + ' is Landsat 5'
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
            esun3 = 1533  #Band 3 Spectral Irradiance
            esun4 = 1039  #Band 4 Spectral Irradiance

            # Open metadata file and get sun elevation value
            for textfile in glob.glob(metafilepath):
                if fnmatch.fnmatch(textfile, '*MTL.txt'):
                    metafile = open(textfile, 'r')
            for line in metafile:
                if "EARTH_SUN_DISTANCE" in line:
                    esdvalue = line.split()[-1]
                if "SUN_ELEVATION" in line:
                    elevalue = line.split()[-1]
            metafile.close()            
                    
            sunelev = float(elevalue)        
            zenith = math.cos(90 - sunelev)

            d2 = float(esdvalue) * float(esdvalue)  # earth sun distance--squared

        #------------------------Create NDVI and LST grids---------------------------#

            env.workspace = inputdir
            BandList = arcpy.ListRasters() # (lists each extracted scene band)
            for Band in BandList:
            # LST calculation (1/2)
                if "B6" in Band:
                    lst = ((Ldiff6 / Qcaldiff) * (Raster(Band) - Qcalmin) + Lmin6) #Conversion to Radiance
            # NDVI calculation
                if "B3" in Band:
                    #print Band
                    ndvi30 = Raster(Band)
                    ndvi30rad = ((Ldiff3 / Qcaldiff) * (Raster(Band) - Qcalmin) + Lmin3) #Conversion to Radiance
                    ndvi30ref = (3.14159 * ndvi30rad * d2)/(esun3 * zenith) #Radiance to Reflectance
                if "B4" in Band:
                    ndvi40 = Raster(Band)
                    ndvi40rad = ((Ldiff4 / Qcaldiff) * (Raster(Band) - Qcalmin) + Lmin4) #Conversion to Radiance
                    ndvi40ref = (3.14159 * ndvi40rad * d2)/(esun4 * zenith) #Radiance to Reflectance                
                    ndvi = (Float(ndvi40ref - ndvi30ref)) / (Float(ndvi40ref + ndvi30ref))
            # QA Band
                if "BQA" in Band:
                    qaband = Raster(Band)
                    cloudmask = cloudMask(qaband)
            finallst = surfacetemp(lst,ndvi)

        elif Landsat == '7':
            # Bands 3,4,6 Radiance Constants (landsat 7)
            Qcalmax = 255
            Qcalmin = 1
            Qcaldiff = 254

            # LST Radiance to Temperature Constants (landsat 7)
            K1 = 666.09
            K2 = 1282.71
            
            # NDVI Reflectance Coefficients
            esun3 = 1533  #Band 3 Spectral Irradiance
            esun4 = 1039  #Band 4 Spectral Irradiance

            # Open metadata file and get sun elevation value & band radiance coefficients
            for textfile in glob.glob(metafilepath):
                if fnmatch.fnmatch(textfile, '*MTL.txt'):
                    metafile = open(textfile, 'r')
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
                    Lmin6_1 = float(Lmin6value)
                if "RADIANCE_MAXIMUM_BAND_6_VCID_1" in line:
                    Lmax6value = line.split()[-1]
                    Lmax6_1 = float(Lmax6value)
            metafile.close()
            
            Ldiff3 = Lmax3 - Lmin3
            Ldiff4 = Lmax4 - Lmin4
            Ldiff6_1 = Lmax6_1 - Lmin6_1                   
            sunelev = float(elevalue)        
            zenith = math.cos(90 - sunelev)

#            # Get Earth-Sun distance based on julian date
#            esdtable = open(inputtable)
#            for line in esdtable.readlines():
#                if line.startswith(jdate):
#                    esdvalue = line.split()[-1]
#            esdtable.close()
            d2 = float(esdvalue) * float(esdvalue)  # earth sun distance--squared

        #------------------------Create NDVI and LST grids---------------------------#

            env.workspace = inputdir
            BandList = arcpy.ListRasters() # (lists each extracted scene band)
            #print BandList
            for Band in BandList:
                if "B6_VCID_1" in Band:
                    lst = ((Ldiff6_1 / Qcaldiff) * (Raster(Band) - Qcalmin) + Lmin6_1) #Conversion to Radiance
                # NDVI calculation
                if "B3" in Band:
                    ndvi30 = Raster(Band)
                    ndvi30rad = ((Ldiff3 / Qcaldiff) * (Raster(Band) - Qcalmin) + Lmin3) #Conversion to Radiance
                    ndvi30ref = (3.14159 * ndvi30rad * d2)/(esun3 * zenith) #Radiance to Reflectance
                if "B4" in Band:
                    ndvi40 = Raster(Band)
                    ndvi40rad = ((Ldiff4 / Qcaldiff) * (Raster(Band) - Qcalmin) + Lmin4) #Conversion to Radiance
                    ndvi40ref = (3.14159 * ndvi40rad * d2)/(esun4 * zenith) #Radiance to Reflectance
                    ndvi = (Float(ndvi40ref - ndvi30ref)) / (Float(ndvi40ref + ndvi30ref))
            # QA Band
                if "BQA" in Band:
                    qaband = Raster(Band)
                    cloudmask = cloudMask(qaband)                  
            finallst = surfacetemp(lst,ndvi)

        elif Landsat == '8':
            # LST Radiance to Temperature Coefficients (Landsat 8 Constants)
            K1 = 774.89    # band 10
            K2 = 1321.08   # band 10

            # Bands 4 and 5 reflectance rescale values 
            MP4value = 0.00002   # aka RADIANCE_MULT_BAND_4
            AP4value = -0.1      # aka RADIANCE_ADD_BAND_4
            MP5value = 0.00002   # aka RADIANCE_MULT_BAND_5
            AP5value = -0.1      # aka RADIANCE_ADD_BAND_5

            # Open metadata file and get coefficients and scaling factor values
            for textfile in glob.glob(metafilepath):
                if fnmatch.fnmatch(textfile, '*MTL.txt'):
                    metafile = open(textfile, 'r')
            for line in metafile:
                if "EARTH_SUN_DISTANCE" in line:
                    esdvalue = line.split()[-1]
                if "SUN_ELEVATION" in line:
                    elevalue = line.split()[-1]
                if "EARTH_SUN_DISTANCE" in line:
                    esdvalue = line.split()[-1]
                if "RADIANCE_MULT_BAND_4" in line:
                    ML4 = line.split()[-1]
                    ML4value = float(ML4)
                if "RADIANCE_ADD_BAND_4" in line:
                    AL4 = line.split()[-1]
                    AL4value = float(AL4)
                if "RADIANCE_MULT_BAND_5" in line:
                    ML5 = line.split()[-1]
                    ML5value = float(ML5)
                if "RADIANCE_ADD_BAND_5" in line:
                    AL5 = line.split()[-1]
                    AL5value = float(AL5)  
                if "RADIANCE_MULT_BAND_10" in line:
                    ML10 = line.split()[-1]
                    ML10value = float(ML10)
                if "RADIANCE_ADD_BAND_10" in line:
                    AL10 = line.split()[-1]
                    AL10value = float(AL10)
                if "RADIANCE_MULT_BAND_11" in line:
                    ML11 = line.split()[-1]
                    ML11value = float(ML11)
                if "RADIANCE_ADD_BAND_11" in line:
                    AL11 = line.split()[-1]
                    AL11value = float(AL11)  
            metafile.close()

            sunelev = float(elevalue)        
            zenith = math.cos(90 - sunelev)

        #------------------------Create NDVI and LST grids---------------------------#

            env.workspace = inputdir
            BandList = arcpy.ListRasters() # (lists each extracted scene band)
            for Band in BandList:
            # LST calculation (1/2)
            #Band 10 DN conversion to TOA Radiance
                if "B10" in Band:
                    lst = ((Raster(Band) * ML10value) + AL10value) #Conversion to Radiance
            # NDVI calculation
                if "B4" in Band:
                    #print Band
                    ndvi40 = ((Raster(Band) * MP4value) + AP4value) # TOA reflectance w/o correction for solar angle
                    ndvi40ref = (ndvi40 / zenith) # TOA planetary reflectance
                if "B5" in Band:
                    #print Band
                    ndvi50 = ((Raster(Band) * MP5value) + AP5value) # TOA reflectance w/o correction for solar angle
                    ndvi50ref = (ndvi50 / zenith) # TOA planetary reflectance                  
                    ndvi = (Float(ndvi50ref - ndvi40ref)) / (Float(ndvi50ref + ndvi40ref))
            # QA Band
                if "BQA" in Band:
                    qaband = Raster(Band)
                    cloudmask = cloudMask(qaband)
            finallst = surfacetemp(lst,ndvi)

        # Set up output folders and save NDVI output
        outNDVI = output + os.sep + "NDVI"  
        if not os.path.exists(outNDVI):
            os.mkdir(outNDVI)
        outLST = output + os.sep + "LST"
        if not os.path.exists(outLST):
            os.mkdir(outLST)
        
        masked_ndvi = Con(cloudmask == 0, ndvi)
        outNDVI_file = outNDVI + os.sep + "ndvi" + scenedate + ".tif"
        arcpy.CopyRaster_management(masked_ndvi,outNDVI_file,"32_BIT_FLOAT")
        print 'Created NDVI file.'
        maskedLST = Con(cloudmask == 0, finallst)
        outLST_file = outLST + os.sep + "lst" + scenedate + ".tif"
        arcpy.CopyRaster_management(maskedLST,outLST_file,"32_BIT_FLOAT")
        print 'Created LST file.'
        

        
