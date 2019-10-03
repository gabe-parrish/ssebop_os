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
import math
import numpy as np
import gdal
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
# ============= standard library imports ========================
from utils.os_utils import windows_path_fix
from ETref_tools.refet_functions import *

"""This script will calculate daily reference ET for the Leyendecker Met Station at NMSU. It is intended to be 
rewritten and have its functionality generalized. Procedure sourced from
 Zotarelli et al 'Step by Step Calculation of the Penman-Monteith Evapotranspiration (FAO-56 Method)'
  by the University of Florida."""


# Make the functions first and apply them to the data frame as they are applicable.

# Get 1 day's data as a sample to work with: July 26 2012 aka Day 208 index 207

# === inputs ===

# daily meteorological data for the year 2012

ld_csv = pd.read_csv(r'Z:\Users\Gabe\refET\jupyter_nbs\weather_station_data\leyendecker_2012_daily.csv')
print(ld_csv.loc[207])
# get a dataseries from the dataframe to do a 1 day example
ds = ld_csv.loc[207]

# === other constants needed ===
# 1) Height of windspeed instrument (we assume 2m for this instrument so we don't adjust)
# 2) Elevation above sealevel
feet_abv_sl = 3858.46
# 3) Lon Lat location (must be a geographic coordinate system?)
lonlat = (-106.74, 32.20)
# 4) julian date
measurement_date = ds['Date']
mdate = datetime.strptime(measurement_date, '%Y-%m-%d')
jdate = mdate.timetuple().tm_yday
print('julian day', jdate)


# print(ld_csv.columns.to_list())
# print(ld_csv.loc[207].to_list())


tmax = ds['Max Air Temperature (F)']
tmin = ds['Min Air Temperature (F)']
# Step 1 Mean daily temp
# return mean temp in metric units
Tmean = calc_Tmean(Tmax=tmax, Tmin=tmin, metric=False)

# step 2 convert solar rad from watts to meters (skip for this dataset)

# step 3 get average daily wind speed in m/s at 2 m by adjusting (for now assume wind speed is at 2m)
wind_speed_us = ds['Mean Wind Speed (MPH)']
# otherwise use calc_u2(metric=False)
u2 = conv_mph_to_mps(wind_speed_us)
print('wind speed Meters per s', u2)
# u2 = calc_u2(uh=wind_speed_us, h=5, metric=False)

# step 4 - Slope of saturation vapor pressure
delta = calc_delta(Tmean=Tmean)

# step 5 - Calculate atmospheric pressure
atmP = calc_atmP(z=feet_abv_sl, metric=False)

# step 6 - calculate the psychrometric constant
gamma = calc_psych_const(p_atm=atmP)

# step 7 - Calculate the delta term of PM (Auxiliary term for Radiation)
DT = calc_DT(delta=delta, psych_const=gamma, u2_vel=u2)

# step 8 - calculate psi term PT for PM equation (Auxiliary calc for wind term)
PT = calc_PT(delta=delta, psych_const=gamma, u2_vel=u2)

# step 9 - calculate temp term (TT) for PM equation (Aux calc for wind term)
TT = calc_TT(Tmean=Tmean, u2_vel=u2)

# step 10 - Mean saturation vapor pressure from air Temp
Tmax = conv_F_to_C(tmax)
Tmin = conv_F_to_C(tmin)
e_sat, e_tmax, e_tmin = calc_sat_vp(Tmax=Tmax, Tmin=Tmin)
print('e_sat, e_tmax, e_tmin', e_sat, e_tmax, e_tmin)
# step 11 - actual vapor pressure from relative humidity
rh_max = ds['Max RH (%)']
rh_min = ds['Min RH (%)']
rh_mean = ds['Mean RH (%)']
print('extreme pm', 10 * 1.2)
e_a = calc_e_actual(rh_max=rh_max, rh_min=rh_min, e_tmax=e_tmax, e_tmin=e_tmin)
print('e_a', e_a)
# e_a = calc_e_actual(rh_max=rh_max, rh_min=rh_min, e_tmax=e_tmax, e_tmin=e_tmin, rhmax_only=True)
# e_a = calc_e_actual(e_tmax=e_tmax, e_tmin=e_tmin, rh_mean=rh_mean)
# === Calculating Radiation Terms ===

# step 12 - calculate relative earth sun distance and solar declination
solar_declination = calc_sol_decl(julian_date=jdate)
dr = calc_dr(julian_date=jdate)

# step 13 - convert latitude from degrees to radians
lat_rad = conv_lat_deg2rad(degrees_lat=lonlat[1])

# step 14 - sunset hour angle
omega_sun = calc_sunsethour_angle(lat_rad=lat_rad, sol_decl=solar_declination)

# step 15 - extraterrestrial radiation
Ra = calc_Ra(dr=dr, omega_sun=omega_sun, lat_rad=lat_rad, sol_decl=solar_declination)
print('Ra', Ra)

# step 16 - clear sky radiation
Rso = calc_Rso(z=conv_f_to_m(feet_abv_sl), Ra=Ra)
print('Rso', Rso)

# step 17 Net shortwave -
Rs = ds['Total Solar Radiation (MJ/m^2)']
Rns = calc_Rns(Rs=Rs)
print('Rns', Rns)

# step 18 Net longwave

# print('e_a', e_a)
# print('Rs', Rs)
# print('tmax', Tmax, 'tmin', Tmin)
Rnl = calc_Rnl(Tmax=Tmax, Tmin=Tmin, e_actual=e_a, Rs=Rs, Rso=Rso, Ra=Ra)
print('Rnl', Rnl)

# step 19 Net Rad
Rn = calc_Rn(Rns=Rns, Rnl=Rnl, mm=True)
# print('Rn', Rn)

# calc ETo
ETrad = DT * Rn
print('rad term', ETrad)

print('PT', PT)
print('TT', TT)
print('sat vs actual diff', e_sat - e_a)
ETwind = PT * TT * (e_sat - e_a)
print('wind term', ETwind)
# ETwind *= 0.408
ETo = ETwind + ETrad

print('ETo in mm: ', ETo)

A = delta * (Rn)

# Figure out why you're getting e-sat wrong
print('e actual', e_a, 'E_SAT', e_sat)
B = gamma * (900/(Tmean+273))*u2*(e_sat - e_a)

C = gamma * (1 + (0.34*u2))

print('a', A, 'b', B, 'c', C, 'delta', delta)

print('numerator', A + B)
print('denominator', delta + C)

ETo = (A + B) / (delta + C)
print('O.G. ETo', ETo)


