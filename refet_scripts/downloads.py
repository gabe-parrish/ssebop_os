from ftplib import FTP
import glob
import logging
import os
import sys
import subprocess
import traceback

"""Script by Stefanie Kagone to serve as a template for downloading data..."""

# Return script path
script_dir = sys.path[0]
# separate drive and path
(drive, tail) = os.path.splitdrive(script_dir)
tail_s = tail.split(os.sep)

servers = {
    'USGS-DDS': {
        "server": 'dds.cr.usgs.gov',
        "username": '',
        "password": '',
        "url": "https://ers.cr.usgs.gov/login/"
    },
    'NASA-EARTHDATA-LST': {
        "server": 'e4ftl01.cr.usgs.gov',
        "username": '',
        "password": '',
        "url": 'http://e4ftl01.cr.usgs.gov/'
    },
    'NASA-NOHRSC-SWE': {
        "server": 'portal.nccs.nasa.gov',
        "username": '',
        "password": '',
        "url": 'http://portal.nccs.nasa.gov/'
    }
}

# Download tools
# Wget
wget_tool_exe = (drive + os.sep + tail_s[1] + os.sep + tail_s[2] +
                 os.sep + "utilities" + os.sep + "wget-1.19.1" + os.sep +
                 "wget.exe")


def download_using_active_ftp(remote_file_url, local_file, timeout,
                              dataset_region, dataset_type, log_file):

    try:

        local_file_size = 0
        remote_file_size = 0

        if os.path.exists(local_file) and os.stat(local_file).st_size == 0:
            os.remove(local_file)
        if not dataset_type.lower() in ["gfs", "gfspars"]:
            print "INFO: Checking data availability of " + str(remote_file_url)
            log_file.write(
                "\nINFO: Checking data availability of " + str(remote_file_url))
        remotefile = urllib2.urlopen(remote_file_url, timeout=timeout)
        remotefile_data = remotefile.read()
        remotefile.close()
        remote_file_size = len(remotefile_data)
        localfile = open(local_file, 'wb')
        localfile.write(remotefile_data)
        localfile.close()
        local_file_size = os.stat(local_file).st_size
        return local_file_size, remote_file_size

    except urllib2.URLError, e:

        msg = "\nERROR: Could NOT get " + dataset_region + \
            " raw file [" + str(data_file_name) + "]"
        print msg
        log_file.write(msg)

        print"\nERROR: " + str(e.reason)
        log_file.write("\nERROR: " + str(e.reason))

        tb = sys.exc_info()[2]
        exctype, excvalue = sys.exc_info()[:2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = ("PYTHON ERRORS:\nTraceback Info:\n" +
                 tbinfo + "\nError Info:\n    " +
                 str(exctype) + ": " + str(excvalue) + "\n")

        print pymsg
        log_file.write("\n" + pymsg)

        return 0, 0


def download_using_passive_ftp(remote_site, remote_directory,
                               remote_file, local_file, timeout,
                               dataset_region, dataset_type, log_file):
    '''
        NOAA: Daily GFS Prec,  Daily GFS Pars, Daily GDAS, Dekadal ITF
        UCSB: Pentadal CHIRPS
    '''
    try:
        local_file_size = 0
        remote_file_size = 0
        remote_url_s = ("{}/{}/{}".format(remote_site,
                                          remote_directory,
                                          remote_file))
        if dataset_type.lower() == "chirps":
            remote_url = ("ftp://{}".format(remote_url_s))
        else:
            remote_url = ("https://{}".format(remote_url_s))
        if (not dataset_type.lower() in ["gfs", "gfspars", "gdas"] and
                "global_daily" not in remote_directory.split("/")):
            msg = "INFO: Checking data availability of %s" % (remote_url)
            print_msg.printMsg_orig(msg, log_file)
        try:
            ftp = FTP(remote_site)
            ftp.timeout = timeout
            ftp.login()
            ftp.cwd(remote_directory)
            # force passive FTP if server requires
            ftp.set_pasv(True)
            localfile = open(local_file, 'wb')
            res = ftp.retrbinary('RETR ' + remote_file, localfile.write)
            remote_file_size = ftp.size(remote_file)
            ftp.quit()
            localfile.close()
            if not res.startswith('226 Transfer complete'):
                os.remove(local_file)
            else:
                if (not dataset_type.lower() in ["gfs", "gfspars", "gdas"] and
                        "global_daily" not in remote_directory.split("/")):
                    msg = "INFO: %s" % (res)
                    print_msg.printMsg_orig(msg, log_file)
                if os.path.exists(local_file):
                    local_file_size = os.stat(local_file).st_size
        except:
            if os.path.exists(local_file):
                localfile.close()
                if os.stat(local_file).st_size == 0:
                    os.remove(local_file)
                    local_file_size = 0
                    remote_file_size = 0
        return local_file_size, remote_file_size
    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        msg = ("PYTHON ERRORS:\nTraceback Info:\n" + tbinfo +
               "\nError Info:\n    " + str(sys.exc_type) + ": " +
               str(sys.exc_value) + "\n")
        print_msg.printMsg_orig(msg, log_file)
        if 'ftp' in vars():
            print ftp.quit()
        return 0, 0


def download_from_usgs_dds(remote_site, remote_directory, local_directory,
                           raw_pattern, dataset_region, dataset_type,
                           log_file):
    '''
        DDS: Dekadal eMODIS NDVI
    '''
    try:
        server_name = 'USGS-DDS'
        username = servers[server_name]['username']
        password = servers[server_name]['password']
        local_file_size = 0
        local_file = None
        wget_cut_dir = len(remote_directory.split("/")) - 1
        # define URL path to the directory where the raw data is located
        remote_url = "https://" + str(remote_site)
        msg = ("INFO: Checking data availability on %s%s" % (remote_url,
                                                             remote_directory))
        print_msg.printMsg_orig(msg, log_file)
        # Use wget tool utility to download data
        wget_command = (
            "%s -r --no-host-directories --cut-dirs=%s --no-check-certificate "
            "--user %s --password %s --quiet --accept=%s %s%s" % (
                wget_tool_exe,
                str(wget_cut_dir),
                username, password,
                raw_pattern,
                remote_url,
                remote_directory))
        print("DEBUG: {}".format(wget_command))
        os.system(wget_command)
        local_files = glob.glob(local_directory + os.sep + raw_pattern)
        # Should be found 1 zip file
        if len(local_files) == 1:
            local_file = local_files[0]
            local_file_size = os.stat(local_file).st_size
        return local_file, local_file_size
    except:
        tb = sys.exc_info()[2]
        exctype, excvalue = sys.exc_info()[:2]
        tbinfo = traceback.format_tb(tb)[0]
        msg = ("PYTHON ERRORS:\nTraceback Info:\n" + tbinfo +
               "\nError Info:\n    " + str(sys.exc_type) + ": " +
               str(sys.exc_value) + "\n")
        print_msg.printMsg_orig(msg, log_file)
        if local_file is not None:
            if os.path.exists(local_file):
                if os.stat(local_file).st_size == 0:
                    os.remove(local_file)
        return local_file, local_file_size


def download_from_nasa_nohrsc(remote_site, remote_directory, remote_file,
                              log_file):
    '''
        NASA: Daily SnowDepth,  Daily SWE
    '''
    try:
        logging.basicConfig(
            filename=log_file, level=logging.DEBUG,
            format='%(asctime)-8s %(levelname)-8s %(message)s')

        local_file_size = 0
        local_file = None

        # define URL path to the directory where the raw data is located
        remote_url = "https://" + \
            str(remote_site) + remote_directory + remote_file
        # remote_url = 'https://portal.nccs.nasa.gov/lisdata_pub/FEWSNET/Asia_2016_2017/NASA_LIS_NOAH32_'+ str(run_year) + str(run_month) + str(run_day) + '0000.tgz'

        logging.info("Checking data availability on %s" % (remote_url))
        # Use wget tool utility to download data
        wget_command = "%s --no-check-certificate %s" % (
            wget_tool_exe, remote_url)
        # print wget_command
        snowfile = os.system(wget_command)
        # Should be found 1 zip file
        if snowfile == 0:
            local_file = remote_file
            local_file_size = os.stat(local_file).st_size
        return local_file, local_file_size, snowfile
    except:
        tb = sys.exc_info()[2]
        exctype, excvalue = sys.exc_info()[:2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = ("\nPYTHON ERRORS:\nTraceback Info:\n" + tbinfo +
                 "\nError Info:\n\t" +
                 str(exctype) + ": " + str(excvalue) + "\n")
        logging.error(pymsg)
        if local_file is None:
            if os.path.exists(local_file):
                if os.stat(local_file).st_size == 0:
                    os.remove(local_file)
        return local_file, local_file_size


def download_using_wget(remote_site, remote_directory, local_directory,
                        localfile, dataset_region, dataset_type,
                        logger):
    '''
	Monthly Soil Moisture
    '''
    try:
        local_file_size = 0
        local_file = os.path.join(local_directory, localfile)
        if os.path.exists(local_file):
            os.remove(local_file)
        # define URL path to the directory where the raw data is located
        remote_file = "{}{}{}".format(remote_site, remote_directory, localfile)
        msg = ("Checking data availability of {}".format(remote_file))
        logger.info(msg)
        # Use wget tool utility to download data
        wget_command = ("{} --no-host-directories -nd --quiet "
                        "--no-check-certificate {}".format(wget_tool_exe,
                                                           remote_file))
        # print wget_command
        subprocess.call(wget_command, shell=False)

        if os.path.exists(local_file):
            local_file_size = os.stat(localfile).st_size
        return local_file_size
    except:
        tb = sys.exc_info()[2]
        exctype, excvalue = sys.exc_info()[:2]
        tbinfo = traceback.format_tb(tb)[0]
        msg = ("\nPYTHON ERRORS:\nTraceback Info:\n" + tbinfo +
               "\nError Info:\n    " + str(sys.exc_type) + ": " +
               str(sys.exc_value) + "\n")
        logger.error(msg)
        if localfile is not None:
            if os.path.exists(localfile):
                if os.stat(localfile).st_size == 0:
                    os.remove(localfile)
        return 0


