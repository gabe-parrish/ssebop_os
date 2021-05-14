
"""Just like combine_ndvi_timeseries, but this time I had to skin the cat differently because the data format was
different when I exported from a single shapefile."""
import os
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

root = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\terra_aqua_ndvi_raw'
output_location = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\terra_aqua_ndvi_merged'
terra = []
aqua = []
names = []

for csv in os.listdir(root):
    # print('csv: ', csv)
    path = os.path.join(root, csv)
    if 'Terra' in path:
        terra.append(path)
        nme = csv.split('_')[2]
        names.append(nme)
    elif 'Aqua' in path:
        aqua.append(path)

# root = r'Z:\Users\Gabe\refET\deliverable_june18\analysis_MarchMay_2021\Field_NDVI_Timeseries'
# terra = []
# aqua = []
# names = []
# for csv in os.listdir(root):
#     # print('csv: ', csv)
#     path = os.path.join(root, csv)
#     if 'Terra' in path:
#         tupy = ()
#         terra.append(path)
#         nme = csv.split('_')[2]
#         names.append(nme)
#     elif 'Aqua' in path:
#         aqua.append(path)

terra = sorted(terra)
aqua = sorted(aqua)
names = sorted(names)
print(terra)
print(aqua)
print(names)

terra_dict = {}
terra_keys = []
aqua_dict = {}
aqua_keys = []
for t, a, n in zip(terra, aqua, names):
    print(t, a)

    with open(t, 'r') as rterr:
        for i, l in enumerate(rterr):
            l = l.strip('\n')
            if i == 0:
                # Get rid of the first and last entry for the dates
                tdts = l.split(',')[1:-1]
                # print('dts: ', l)
                tdt_lst = []
                for dd in tdts:
                    try:
                        tdt_lst.append(datetime.strptime(dd, '%Y-%m-%d'))
                    except ValueError:
                        tdt_lst.append(datetime.strptime(dd, '%m/%d/%Y'))
                # tdt_lst = [datetime.strptime(dd, '%Y-%m-%d') for dd in tdts]

                # terra_dict[f'{n}_terra_dts'] = dts
                # terra_keys.append(f'{n}_terra_dts')
            else:
                # get rid of the last entry based on this multipolygon string
                raw_ndvi = l.split("type")[0]
                # .... Then execute the split
                raw_ndvi = raw_ndvi.split(',')[1:-1]
                # strip out unecessary data
                raw_ndvi = [f.strip('{NDVI=') for f in raw_ndvi]
                traw_ndvi = [j.strip('}') for j in raw_ndvi]
                # # need to remove a very strange GEE entry from the list
                # if '"{""geodesic"":false' in traw_ndvi:
                #     traw_ndvi[:-1] = 'NAN'
                tndvi = []
                for p in traw_ndvi:
                    try:
                        tndvi.append(float(p))
                    except ValueError:
                        tndvi.append(float('NAN'))

                print(len(tndvi), 'tndvi')

                # terra_dict[f'{n}_terra_vals'] = ndvi
                # terra_keys.append(f'{n}_terra_vals')
    with open(a, 'r') as raqua:
        for i, l in enumerate(raqua):
            l = l.strip('\n')
            if i == 0:
                # Get rid of the first and last entry for the dates
                adts = l.split(',')[1:-1]
                # adt_lst = [datetime.strptime(dd, '%Y-%m-%d') for dd in adts]
                adt_lst = []
                for dd in adts:
                    try:
                        adt_lst.append(datetime.strptime(dd, '%Y-%m-%d'))
                    except ValueError:
                        adt_lst.append(datetime.strptime(dd, '%m/%d/%Y'))

                # aqua_dict[f'{n}_aqua_dts'] = dts
                # aqua_keys.append(f'{n}_aqua_dts')
            else:
                # get rid of the last entry based on this multipolygon string
                raw_ndvi = l.split("type")[0]
                # .... Then execute the split
                raw_ndvi = raw_ndvi.split(',')[1:-1]
                # strip out unecessary data
                raw_ndvi = [f.strip('{NDVI=') for f in raw_ndvi]
                araw_ndvi = [j.strip('}') for j in raw_ndvi]
                # andvi = [float(p) for p in araw_ndvi]
                andvi = []
                for p in araw_ndvi:
                    try:
                        andvi.append(float(p))
                    except ValueError:
                        andvi.append(float('NAN'))
                print(len(andvi), 'andvi')


                # aqua_dict[f'{n}_aqua_vals'] = ndvi
                # aqua_keys.append(f'{n}_aqua_vals')

    # take terra dates and merge with terra values in a dataframe, same for aqua
    tdf = pd.DataFrame({'dts': tdt_lst, 'tvals': tndvi}, columns=['dts', 'tvals'])
    # set datetime index before you store in the dictionary
    tdf.set_index('dts', inplace=True)
    terra_dict[f'{n}_terra'] = tdf
    terra_keys.append(f'{n}_terra')
    adf = pd.DataFrame({'dts': adt_lst, 'avals': andvi}, columns=['dts', 'avals'])
    # set datetime index before you store in the dictionary
    adf.set_index('dts', inplace=True)
    aqua_dict[f'{n}_aqua'] = adf
    aqua_keys.append(f'{n}_aqua')

print('terra keys \n', terra_keys)
print('aqua keys \n', aqua_keys)

for tkey, akey in zip(terra_keys, aqua_keys):

    sn = tkey.split('_')[0]
    # Convert to dataframes
    terra_df = terra_dict[tkey]
    aqua_df = aqua_dict[akey]

    # merge the dfs
    modis_df = pd.merge(terra_df, aqua_df, how='outer', left_index=True, right_index=True)
    print('modishead \n', modis_df.head(11))
    modis_df['tvals'].fillna(modis_df['avals'], inplace=True)
    # get a continuous NDVI timeseries by gap-filling terra with aqua.
    modis_df['modis_ndvi'] = modis_df['tvals']
    # get rid of cols you no longer need.
    modis_df = modis_df.drop(['tvals', 'avals'], axis=1)

    # plt.plot(modis_df.index, modis_df.modis_ndvi)
    # plt.title(sn)
    # plt.show()

    modis_df.to_csv(os.path.join(output_location, f'{sn}_modis_ndvi.csv'))
#
#     # output to file
