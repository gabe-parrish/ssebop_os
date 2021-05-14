import pandas as pd
import os
import matplotlib.pyplot as plt

"""A script I was using to troubleshoot issues with OK Mesonet ETo calculations. I had been correcting relative
 Humidity by the mph-meter per second conversion, which was nonsense, boosting the ETo at the station. Moreover, 
 I was using the wrong windspeed ('WSPD'), not the average 2m windspeed ('2AVG'), which is the appropriate one for 
 ASCE Penman."""

root = r'Z:\Users\Gabe\refET\OK_Mesonet\OKMESONET_GRIDMET_daily_compare'

site = 'RING'

fig_output = r'Z:\Users\Gabe\refET\OK_Mesonet\ok_figs\ok_figs_daily'

sn = f'{site}.csv'
sp = os.path.join(root, sn)

met_df = pd.read_csv(sp)

site_eto = met_df['ETo_Station']
gm_eto = met_df['EToGM']

plt.scatter(site_eto, gm_eto, edgecolors='blue', facecolor='none')
plt.plot(site_eto, site_eto, 'black')
plt.title(f'{site} Daily ETo - OK')
plt.xlabel('Station ETo (mm)')
plt.ylabel('Gridmet ETo (mm)')
plt.grid()
plt.savefig(os.path.join(fig_output, f'{site}_comparison_ok_new.png'))
plt.close()