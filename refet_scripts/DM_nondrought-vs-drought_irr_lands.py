import rasterio
import numpy as np
import rasterio as rio
import os
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling


annual_ET_diff = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\2012figs\annual_analysis\pet2012_minus_medpet_0115_annual.tif'

## this one is clipped to the IL border, but it might be chill to use the CONUS one above ^^^
# annual_ET_diff = r'	Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\IrrigatedLands\pet2012_minus_medpet_0115_annual_clipped_IL.tif'
landsat_irr_map = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\IrrigatedLands\lanid2012_clipped_IL.tif'

# output locations
masked_et_diffs_output = r'Z:\Users\Gabe\refET\DroughtPaper\paper_analysis\regionalGRIDMET_droughtSensitivity\2012figs\annual_analysis'


# open landsat_irr_map
with rio.open(landsat_irr_map, 'r+') as src:

    # print('nodata \n', src.nodatavals)
    # set the nodata value.
    src.nodata = 255
    # get crs
    irr_crs = src.crs
    # get metadata
    irr_meta = src.meta
    print('the metadata', irr_meta)
    # set dtype to float 64 so all will be gucci with writing it out...
    irr_meta['dtype'] = 'float64'

# resample --- to the extent and resolution of landat_irr_map
with rio.open(annual_ET_diff) as src:
    with WarpedVRT(src, crs=irr_crs, transform=irr_meta['transform'],
                   height=irr_meta['height'], width=irr_meta['width'],
                   resampling=Resampling.nearest) as vrt:

        et_diff = vrt.read(1)
        print(type(et_diff))
        # set nan value in numpy arr
        et_diff[et_diff == -3.40282e+38] = np.nan

        # read the annual_ET_diff
        with rio.open(landsat_irr_map) as irr_src:

            irr_array = irr_src.read(1)

            print(type(irr_array))
            print('shape match shape \n', et_diff.shape, irr_array.shape)
            # # set nan values in numpy arr (actually unecessary? -commented)
            # irr_array[irr_array == 255.0] = np.NAN
            et_diff_masked = irr_array * et_diff

            # trying to label trash values
            et_diff_masked[et_diff_masked < 0.0] = -9999.0
            et_diff_masked[et_diff_masked > 1000.0] = -9999.0
            et_diff_masked[et_diff_masked == 0.0] = -9999.0

            with rio.open(os.path.join(masked_et_diffs_output, 'etdiff_2012_median_0115_lsIrrMaskedII.tif'),
                          'w', **irr_meta) as outfile:

                outfile.write(et_diff_masked, 1)
                










        # mask the data by irr_src: 0 is non irrigated, 1 is irrigated, 255 is NoData

        # output a map of masked annual_ET_Diff
