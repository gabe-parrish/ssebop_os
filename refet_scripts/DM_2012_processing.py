import itertools
import os

from shapely.geometry import Polygon
from shapely.ops import cascaded_union
import geopandas as gpd
from matplotlib import pyplot as plt

#
root = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\2012figs\2012_drought_shapes'

# todo - create monthly drought 1+ shapefiles
monthlies = {}
monthlist = []
for i, file in enumerate(sorted(os.listdir(root))):
    print(type(file))
    if file.endswith('.shp'):
        fpath = os.path.join(root, file)
        month_str = file[-8:-6]
        monthlist.append((month_str, fpath))

# using groupby
# https://www.geeksforgeeks.org/itertools-groupby-in-python/
mnth_iterator = itertools.groupby(monthlist, lambda x: x[0])

for key, group in mnth_iterator:
    monthlies[key] = list(group)

print(monthlies)
print(monthlies['05'])

for k, v in monthlies.items():
    monthly_polys = []
    for tup in v:
        fpath = tup[-1]
        gdf = gpd.read_file(fpath)
        # print('===DM===')
        # print(gdf['DM'])
        drought_gdf = gdf[gdf.DM > 0]
        # print(drought_gdf)
        # print('drought dm')
        # print(drought_gdf.DM)
        # we use dissolve to get rid of some shapefiles attribute tables that had separate polygons w a DM attribute
        # for each discreet drought location.
        try:
            drought_gdf_diss = drought_gdf.dissolve(by='DM')
        except:
            # topology problem. Solution in link below doesn't help... but worth writing down.
            # https://gis.stackexchange.com/questions/287064/dissolve-causes-no-shapely-geometry-can-be-created-from-null-value-in-geopanda/287065
            print(f'passing on {file}')
            pass

        # from:
        # https://stackoverflow.com/questions/40385782/make-a-union-of-polygons-in-geopandas-or-shapely-into-a-single-geometry
        drought_poly_list = drought_gdf_diss.geometry.to_list()
        monthly_polys.extend(drought_poly_list)
        # drought_boundary = gpd.GeoSeries(cascaded_union(drought_poly_list))
        # monthly_polys.append(cascaded_union(drought_poly_list))
    print(f'polys for month {v} \n {monthly_polys}')
    # join the monthly polygons
    monthly_drought_bounds = gpd.GeoSeries(cascaded_union(monthly_polys))
    monthly_drought_bounds.plot(color='red')
    plt.title(f'Month {k} Drought')
    plt.show()

    # todo - ouput this shit!


#  hold for later
# for i, file in enumerate(os.listdir(root)):
#     if file.endswith('.shp'):
#         print(file)
#         fpath = os.path.join(root, file)
#         gdf = gpd.read_file(fpath)
#         # print('===DM===')
#         # print(gdf['DM'])
#         drought_gdf = gdf[gdf.DM > 0]
#         # print(drought_gdf)
#         # print('drought dm')
#         # print(drought_gdf.DM)
#         # we use dissolve to get rid of some shapefiles attribute tables that had separate polygons w a DM attribute
#         # for each discreet drought location.
#         try:
#             drought_gdf_diss = drought_gdf.dissolve(by='DM')
#         except:
#             # topology problem. Solution in link below doesn't help... but worth writing down.
#             # https://gis.stackexchange.com/questions/287064/dissolve-causes-no-shapely-geometry-can-be-created-from-null-value-in-geopanda/287065
#             print(f'passing on {file}')
#             pass
#
#         # from:
#         # https://stackoverflow.com/questions/40385782/make-a-union-of-polygons-in-geopandas-or-shapely-into-a-single-geometry
#         drought_poly_list = drought_gdf_diss.geometry.to_list()
#         drought_boundary = gpd.GeoSeries(cascaded_union(drought_poly_list))
#         drought_boundary.plot(color='red')
#         plt.title(f'{file}')
#         plt.show()
#
