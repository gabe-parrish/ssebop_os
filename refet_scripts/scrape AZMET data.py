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
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import urllib.request

from bs4 import BeautifulSoup
import requests
# ============= standard library imports ========================

# requests.get()

class AzmetScrape():

    def __init__(self, url):

        self.url = url
        site = requests.get(url)
        self.content = self.site.content

        self.soup = BeautifulSoup(self.content, 'html5lib')




azmet_historical = r'https://cals.arizona.edu/AZMET/az-data.htm'


with open(r'C:\Users\gparrish\Downloads\az-data.htm', 'r') as cleanfile:
    soup = BeautifulSoup(cleanfile, features="lxml")
# print(soup.table)

    # Find all the links in the files
    for t in soup.find_all('a'):

        # Now identify each site and it's name and build a path for requests to follow
        if t.get('target') == '_blank':
            # this is what we're going to write to.
            textlines = []
            print(t)
            name = t.b
            print(name)
            link_stub = t.get('href')

            full_url = f'{azmet_historical}/{link_stub}'

            # grab the met tower site http code
            azmet_sitepage = requests.get(full_url, verify=False)
            azmet_content = azmet_sitepage.content
            site_soup = BeautifulSoup(azmet_content, features='lxml')

            # GET ALL THE DAILY RAW DATA for EACH YEAR.... it's comma separated and has the full date plus other shit...


    # for line in soup.contents:
    #     print(line)



# for c in soup.find('center'):
#     print(c)
#
# for aa in soup.find_all('ul', recursive=True):
#
#     print(aa)
#     print(aa.contents)
#
#     # for tag in tr.descendants:
#         # tablebits = tag.contents
#         # print(tag)
#         # for child in tag.children:
#         #     print(child)
#         #
#         #     for aa in child.find_all('a'):
#         #         print(aa)
#             # for i in child.descendants:
#             #     print(i)






