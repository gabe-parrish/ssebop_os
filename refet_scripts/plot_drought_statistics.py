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
import yaml
import matplotlib.pyplot as plt
# ============= standard library imports ========================

path = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\script-generated_plots\et_ref_stats.yml_USDMlvl3'

with open(path, 'r') as ryaml:
    stat_dict = yaml.load(ryaml)

print('stats \n', stat_dict)

# relational_dict = {'Antelope'}
color_dict = {'USDMDrought': 'red', 'AntelopeValleyNV_USDMnonDrought': 'blue'}
stat_list = ['alpha', 'beta', 'kge', 'mbe', 'pearson_r', 'sde']
drought_condtion_dict = {'USDMDrought_mbe': [], 'USDMDrought_kge':[],
                         'USDMDrought_alpha': [], 'USDMDrought_beta': [], 'USDMDrought_pearson_r': [],
                         'USDMDrought_sde': [],
                         'USDMnonDrought_mbe': [], 'USDMnonDrought_kge': [],
                         'USDMnonDrought_alpha': [], 'USDMnonDrought_beta': [], 'USDMnonDrought_pearson_r': [],
                         'USDMnonDrought_sde': []}
# todo - figure out how to make the stat labels shorter
for stat in stat_list:
    for k, v in stat_dict.items():
        klist = k.split('_')
        site = klist[0]
        drought_condition = klist[1]
        try:
            drought_condtion_dict[f'{drought_condition}_{stat}'].append(v[stat])
            print(f'appended value of {stat} = {v[stat]} for {k}')
        except:
            f'got a error for site {site} and drought condition {drought_condition}'
            pass
print('resulting dict \n', drought_condtion_dict)
# TODO - Now Plot :-)
fig, ax = plt.subplots()
for k, v in drought_condtion_dict.items():
    lst = [k for i in range(len(v))]
    ax.scatter(lst, v)
ax.grid(True)
ax.set_title(
    f'Drought and Non-Drought Statistics for All Locations')
ax.set_xlabel('(Drought/Non-Drought) Statistic')
ax.set_ylabel('Statistic Value')
# plt.savefig(os.path.join(plot_output, f'USDM_non_drought_comparison_{sn}_USDMlvl{USDM_drought_threshhold}.png'))
plt.show()



# x = ['apples', 'pears', 'oranges']
# y = [[2,4,8], [9,3,1], [5,1,6]]
#
# fig, ax = plt.subplots()
# for i, lst in zip(x, y):
#     ax.scatter([i for a in range(len(lst))], lst)
# ax.grid(True)
# ax.set_title(
#     f'Sad Froots and their statistics')
# ax.set_xlabel('Froot typ')
# ax.set_ylabel('Actual Numbers')
# # plt.savefig(os.path.join(plot_output, f'USDM_non_drought_comparison_{sn}_USDMlvl{USDM_drought_threshhold}.png'))
# plt.show()