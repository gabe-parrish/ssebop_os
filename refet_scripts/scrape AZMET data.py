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


class AzmetScrape():

    def __init__(self, url):

        self.url = url
        site = requests.get(url)
        self.content = self.site.content

        self.soup = BeautifulSoup(self.content, 'lxml')




azmet_historical = 'https://cals.arizona.edu/AZMET/az-data.htm'

azmet_sitepage = requests.get(azmet_historical)
azmet_content = azmet_sitepage.content

# parse the html content
soup = BeautifulSoup(azmet_content)
print(soup.text)






