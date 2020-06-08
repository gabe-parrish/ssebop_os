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
from bs4 import BeautifulSoup, Comment
from datetime import datetime
import requests
# ============= standard library imports ========================

"""This script is used to scrape AZMET meteorological data from the University of Arizona Website. 
It is not very flexible"""


azmet_historical = r'https://cals.arizona.edu/AZMET/az-data.htm'
azmet_home = r'https://cals.arizona.edu/AZMET'

daily_raw_weather = {}
# hourly_raw_weather = {}
# daily_azmet_eto = {}

# === OUTPUT Locations ====
daily_raw_weather_out = r'Z:\Users\Gabe\refET\AZMet_Stations\scraped_raw\daily_raw_data'
# hourly_raw_weather_out = r'Z:\Users\Gabe\refET\AZMet_Stations\scraped_raw\hourly_raw_data'
# daily_azmet_eto_out = r'Z:\Users\Gabe\refET\AZMet_Stations\scraped_raw\Daily_ETo'

with open(r'C:\Users\gparrish\Downloads\az-data.htm', 'r') as cleanfile:
    soup = BeautifulSoup(cleanfile, features="lxml")
# print(soup.table)

    # Find all the links in the files
    for t in soup.find_all('a'):

        # Now identify each site and it's name and build a path for requests to follow
        if t.get('target') == '_blank':
            # this is what we're going to write to.
            daily_textlines = []
            hourly_textlines = []
            ETo_textlines = []
            # print(t)
            name = t.b.string
            print('name:::', name)
            link_stub = t.get('href')

            full_url = f'{azmet_home}/{link_stub}'
            # print(full_url)

            # grab the met tower site http code
            azmet_sitepage = requests.get(full_url, verify=False)
            azmet_content = azmet_sitepage.content
            site_soup = BeautifulSoup(azmet_content, features='html5lib')

            # GET ALL THE DAILY RAW DATA for EACH YEAR....
            # it's comma separated and has the full date plus other stuff...
            # print(site_soup.title)
            print('NAME:', name)

            # print(site_soup.text)
            # WE NEED TO GET THE ELEVATION AND COORDINATES (LAT LON) FROM THE WEBPAGE FOR EACH SITE
            for bb in site_soup.find_all('b'):

                str_var = bb.string
                # NOTE THAT SOME SITES HAVE TWO LOCATIONS OVER TIME, BUT ARE USUALLY VERY CLOSE IN ELEV AND COORDS.
                # THE OLD COORDS ARE WRITTEN IN DEGREES AND MINS SO SOMETIMES THERE MAY BE A MIX OF ELEVATION AND
                # LOCATION FROM TWO SITES THE WAY THE SCRAPING SCRIPT IS WRITTEN BUT ANY DIFFERENCES ARE DEMINIMIS.
                try:
                    if str_var == ' Elevation :':
                        # print(bb.text)
                        # print(bb.next_sibling)
                        etext = bb.next_sibling
                        etext = etext.split('meters')
                        etext = etext[0]
                        etext = etext.strip(' ')
                        elevation = int(etext)
                        print('the elevation: {}'.format(elevation))

                    elif str_var == ' Coordinates :':
                        # print(bb.text)
                        ctext = bb.next_sibling
                        ctext = ctext.split(',')
                        # latitude
                        lattext = ctext[0]
                        lattext = lattext.strip(' ')
                        lat = float(lattext)
                        # longitude
                        lontext = ctext[1]
                        lontext = lontext.strip(' ')
                        lon = float(lontext)
                        print('lat, lon: {}, {}'.format(lat, lon))
                except:
                    continue

            for aa in site_soup.find_all('a'):

                if aa.b != None:
                    # print('aa.b', aa.b.string)
                    filename = aa.get('href').split('/')[-1]


                    # now for each site get the data for every year available at a daily timestep,
                    # (optionally an hourly timestep.) Also get the ETo from AZMET
                    if 'rd' in filename:
                        # get the daily data
                        # print('textfilename', filename)
                        tf_link = aa.get('href')
                        tf_url = f'{azmet_home}/{tf_link}'
                        tf_req = requests.get(tf_url, verify=False)
                        tf_soup = BeautifulSoup(tf_req.content, features='lxml')
                        # print(repr(tf_soup.text))
                        filetext = tf_soup.text
                        lines = filetext.split('\r\n')
                        # WE ADD the lat and lon back onto the scraped data.
                        newlines = []
                        for line in lines:
                            if len(line) > 4:
                                # print('{},{},{},{}'.format(line, lat, lon, elevation))
                                newlines.append('{},{},{},{}'.format(line, lat, lon, elevation))
                        # putting the text back together
                        newtext = '\r\n'.join(newlines)
                        daily_textlines.append(newtext)

                    # elif 'et' in filename:
                    #     # get the ET data
                    #     tf_link = aa.get('href')
                    #     tf_url = f'{azmet_home}/{tf_link}'
                    #     tf_req = requests.get(tf_url, verify=False)
                    #     tf_soup = BeautifulSoup(tf_req.content, features='lxml')
                    #     # print(tf_soup.text)
                    #     ETo_textlines.append(tf_soup.text)

                    # # in order to get hourly data
                    # elif 'rh' in filename:
                    #     # get the hourly data
                    #     tf_link = aa.get('href')
                    #     tf_url = f'{azmet_home}/{tf_link}'
                    #     tf_req = requests.get(tf_url, verify=False)
                    #     tf_soup = BeautifulSoup(tf_req.content, features='lxml')
                    #     print(tf_soup.text)
                    #     hourly_textlines.append(tf_soup.text)

            # put all the scraped data into a dictionary
            daily_raw_weather[f'{name}'] = daily_textlines
            # hourly_raw_weather[f'{name}'] = hourly_textlines
            # daily_azmet_eto[f'{name}'] = ETo_textlines


# output the files
for n, lst in daily_raw_weather.items():


    # First fix a few stupid formating errors that the AZMET ppl left in there
    ilist = []
    for i in lst:

        print('i \n', i)

        year_lst = i.split('\n')
        print('this is year list \n', year_lst)

        for j in year_lst:

            # get rid of the newline it complicates everything
            j = j.strip('\n')
            # get rid of the /r return
            j = j.rstrip()
            # we want the line as a list
            k = j.split(',')

            # print('len k', len(k))
            # print('this is k: \n', k)
            if len(k) >= 25:
                year = k[0]
                X = k[23]  # 24th
                Y = k[24]  # 25th python indices

                # the 90s lack the 19 prefix in the textfiles, so we fix that
                if len(year) < 4:
                    k[0] = '19{}'.format(year)
                # Heat units and Ref et were in opposite positions prior to 2003
                if int(year) < 2003:
                    k[23] = Y
                    k[24] = X


                # join the list back together with commas in a string

                if (k[0] == '1995') or (k[0] == '1994'):
                    print(k)
                    print(','.join(k))
                line = ','.join(k)
                # add the new line back to each line
                # print('line II \n', line)
                line = '{}\n'.format(line)
                ilist.append(line)

    print('Outputting raw daily data for site {}'.format(n))
    outfile = os.path.join(daily_raw_weather_out, '{}.csv'.format(n))
    with open(outfile, 'w') as wfile:

        # this is the first file with headers
        wfile.write('Year,DOY,Station,max_air,min_air,avg_air,max_rel_hum,min_rel_hum,avgrelhum,avg_VPD,solar_rad,ppt,'
                    'max_soil_shallow,min_soil_shallow,mean_soil_shallow,max_soil_deep,min_soil_deep,'
                    'mean_soil_deep,sc_wind_mg,day_wind_vector_mag,day_wind_dir,day_wind_std_dev,max_wind,'
                    'heat_units,ETo_AZ,ETo_PM,mean_vapor_pressure,mean_dewpoint,lat,lon,elev\n')

        for i in ilist:
            # write all the lines of data we want from the file
            wfile.write(i)