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
import zipfile
from progressbar import progressbar

root = r'Z:\Users\Gabe\refET\Drought\full_ts'
# output = r'Z:\Users\Gabe\refET\Drought\full_ts'

for f in progressbar(os.listdir(root)):
    path = os.path.join(root, f)
    if path.endswith('.zip'):  # and f.startswith('USDM_202012')
        print(f'extracting {path}')
        with zipfile.ZipFile(path, 'r') as rzip:
            rzip.extractall(root)

# with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
#     zip_ref.extractall(directory_to_extract_to)