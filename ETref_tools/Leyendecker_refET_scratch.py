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

# def conv_wattflux_2_MJflux()

# def conv_date_to_jdate(datetime_obj):
#     """"""
#     pass
#
# def conv_lat_deg2rad(degrees_lat):
#     """
#
#     :param degrees_lat:
#     :return:
#     """
#
#     rad_lat = (math.pi / 180) * degrees_lat
#     return rad_lat
#
# def conv_F_to_C(tempF):
#     """
#     Convert Farhenheit to Celcius
#     :param tempF: Degrees F
#     :return: tempC
#     """
#     tempC = (tempF - 32) * (5/9)
#     return tempC
#
# def conv_mph_to_mps(mph):
#     """
#     converts miles per hour to meters per second
#     :param mph:
#     :return:
#     """
#     mps = mph * 0.44704
#     return mps
#
# def conv_f_to_m(foot_lenght):
#     """
#     Convert feet to meters
#     :param foot_lenght:
#     :return:
#     """
#     m = foot_lenght / 3.28084
#     return m
#
# def calc_Tmean(Tmax, Tmin, metric=True):
#     """
#     Calculate mean daily temp. If only mean temp is available it
#      can be used but will cause other errors in calculations
#     :param Tmax: daily max temp in degrees celcius
#     :param Tmin: daily min temp in degrees celcius
#     :param metric: bool True if units are metric
#     :return: Tmean in degrees C
#     """
#     if metric:
#         Tmean = (Tmax + Tmin) / 2
#
#     else:
#         print('assuming temp in F')
#         Tmax = conv_F_to_C(Tmax)
#         Tmin = conv_F_to_C(Tmin)
#         Tmean = (Tmax + Tmin) / 2
#
#     return Tmean
#
# def calc_u2(uh, h, metric=True):
#     """
#     Calculate the windspeed in meters per second at 2m height based on a given height and windspeed
#     :param uh: windspeed measured by instrument in meters per second
#     :param h: Height of instrument in meters
#     :param metric: bool True if units are metric
#     :return:
#     """
#
#     if h == 2.0 and metric:
#         u2 = uh
#     else:
#         if metric:
#             print('windspeed units are given in meters per second')
#             u2 = uh * (4.87 / math.log((67.8*h) - 5.42))
#         else:
#             print('assuming windspeed units are in MPH and instrument height in feet')
#             uh = conv_mph_to_mps(uh)
#             h = conv_f_to_m(h)
#             u2 = uh * (4.87 / math.log((67.8 * h) - 5.42))
#     return u2
#
# def calc_delta(Tmean):
#     """
#     Given a Tmean in Celcius calculate the SLOPE of the saturation vapor curve
#     :param Tmean: mean temp calculated from Tmax and Tmin
#     :return: delta slope of sat vapor curve in Kpa/degC
#     """
#     a = math.exp((17.27 * Tmean)/(Tmean + 237.3))
#     # a = math.e ** ((17.27 * Tmean)/(Tmean + 237.3))
#     b = (Tmean + 237.3)**2
#
#     delta = (4098 * (0.6108 * a)) / b
#
#     # # ASCE pg 36 (which one) makes value bigger
#     # delta = (2503 * (0.6108 * a)) / b
#     return delta
#
# def calc_atmP(z, metric=True):
#     """
#     Calculating atmospheric pressure based on elevation using simplification
#      of ideal gas law assuming 20C for a standard atmosphere
#     :param z: elevation in meters above sealevel
#     :param metric: bool True if units are metric
#     :return: p_atm in kPa
#     """
#
#     if metric:
#         p_atm = 101.3 * (((293 - (0.0065 * z))/293)**5.26)
#
#     else:
#         print('assuming the elevation is in feet above sea level')
#         z = conv_f_to_m(z)
#         p_atm = 101.3 * (((293 - (0.0065 * z)) / 293) ** 5.26)
#
#     return p_atm
#
# def calc_psych_const(p_atm):
#     """
#     A simplified way of calculating the psychrometric constant assuming no change of latent heat of vap with temp or
#     changes in specific heat based on changing humidity
#     :param p_atm: atmospheric pressure based on elevation in meters above sealevel in kPa.
#     :return: psych_const in units of kPa/C
#     """
#     psych_const = 0.000665 * p_atm
#     return psych_const
#
# def calc_DT(delta, psych_const, u2_vel):
#     """
#     Calculate the Delta Term, the auxiliary calculation for the radiation component
#     :param delta: slope of pressure temp curve kPa/C
#     :param psych_const: psychrometric constant KPa/C
#     :param u2_vel: velocity at 2m height in m/s
#     :return: DT term (s/m ??)
#     """
#
#     DT = delta / (delta + (psych_const * (1 + (0.34 * u2_vel))))
#     return DT
#
# def calc_PT(delta, psych_const, u2_vel):
#     """
#     Calculate the Psi Term
#     :param delta: slope of pressure temp curve kPa/C
#     :param psych_const: psychrometric constant KPa/C
#     :param u2_vel: velocity at 2m height in m/s
#     :return: PT
#     """
#
#     PT = psych_const / (delta + (psych_const * (1 + (0.34 * u2_vel))))
#     return PT
#
# def calc_TT(Tmean, u2_vel):
#     """
#
#     :param Tmean: mean temp calculated from Tmax and Tmin
#     :param u2_vel: velocity at 2m height in m/s
#     :return: TT term (m/(degC * s)??)
#     """
#
#     TT = (900 / (Tmean + 273))* u2_vel
#     return TT
#
# def calc_sat_vp(Tmax, Tmin):
#     """
#     :param Tmax:
#     :param Tmin:
#     :return:
#     """
#
#     e_tmax = 0.6108 * (math.exp((17.27 * Tmax)/(Tmax + 237.3)))
#     e_tmin = 0.6108 * (math.exp((17.27 * Tmin) / (Tmin + 237.3)))
#     # get mean saturation vapor pressure from the sat vapor pressure at min and max
#     e_sat = (e_tmax + e_tmin) / 2
#
#     return (e_sat, e_tmax, e_tmin)
#
# def calc_e_actual(rh_max=None, rh_min=None, e_tmax=None, e_tmin=None, rhmax_only=False, rh_mean=None):
#     """
#
#     :param rh_max: maximum daily relative humidity as %
#     :param rh_min: minimum daily relative humidity as %
#     :param e_tmax:
#     :param e_tmin:
#     :param rhmax_only: bool True only if RHmin where error could be relatively large or if data is in doubt
#     :param rh_mean: None unless the rh max and min are not available
#     :return: e_actual in kPa
#     """
#     if rhmax_only:
#         print('calculating with Rxmax only')
#         e_actual = e_tmin * (rh_max / 100)
#     elif rh_mean is not None:
#         print('using Rh mean actual vapor pressur calc')
#         e_actual = ((e_tmin + e_tmax) / 2) * (rh_mean/100)
#     # this is the default unless data is suspect or missing
#     else:
#         print('calculating e actual as the default')
#         e_actual = ((e_tmin*(rh_max/100)) + (e_tmax*(rh_min/100))) / 2
#     # moreover, if humidity data overall is very unreliable you can assume that e_actual = e_tmin
#     return e_actual
#
# def calc_dr(julian_date):
#     """
#     Calculate the inverse relative distance Earth-Sun.
#     :param julian_date:
#     :return:
#     """
#     dr = 1 + (0.033 * math.cos(((2 * math.pi) / 365) * julian_date))
#     return dr
#
# def calc_sol_decl(julian_date):
#     """
#
#     :param julian_date:
#     :return:
#     """
#     sol_decl = 0.409 * (math.sin((((2 * math.pi) / 365)*julian_date) - 1.39))
#     return sol_decl
#
# def calc_sunsethour_angle(lat_rad, sol_decl):
#     """
#
#     :param lat_rad: radians
#     :param sol_decl: radians (or dimensionless???)
#     :return: omega
#     """
#     omega_sun = math.acos(-math.tan(lat_rad) * math.tan(sol_decl))
#     return omega_sun
#
#
# def calc_Ra(dr, omega_sun, lat_rad, sol_decl):
#     """
#     Calculate Extraterrestrial Radiation (Ra) in MJ/(m^2 * day)
#     :param dr:
#     :param omega_sun:
#     :param lat_rad:
#     :param sol_decl:
#     :return: Ra extraterrestrial radiation
#     """
#
#     # define the solar constant in MJ/(m^2 * min)
#     Gsc = 0.0820
#
#     Ra = ((24 * 60) / (math.pi)) * Gsc * dr * ((omega_sun * math.sin(lat_rad) * math.sin(sol_decl)) +
#                                               (math.cos(lat_rad) * math.cos(sol_decl) * math.sin(omega_sun)))
#     return Ra
#
# def calc_Rso(z, Ra):
#     """
#     Calculate Clear Sky radiation in in MJ/(m^2 * day)
#     :param z: elevation above sealevel in m
#     :param Ra: extraterrestrial radiation in MJ/(m^2 * day)
#     :return: Rso in in MJ/(m^2 * day)
#     """
#
#     Rso = (0.75 + (2e-5 * z)) * Ra
#     return Rso
#
# # step 17 Net solar or net shortwave
#
# def calc_Rns(Rs, a=0.23):
#     """
#     calculate net shortwave.
#     :param Rs: net solar radiation in MJ/(m^2 * day)
#     :param a: albedo set to 0.23 dimensionless for grass ETo reference
#     :return:
#     """
#
#     Rns = (1 - a) * Rs
#     return Rns
#
# def calc_Rnl(Tmax, Tmin, e_actual, Rs, Rso, Ra=None):
#     """
#     Rate of outgoing long wave radiation is proportional to the temperature of the surace raised to the fourth.
#     :param Tmax: maximum temp deg C
#     :param Tmin: min temp deg C
#     :param e_actual: actual vapor pressure in kPa
#     :param Rs: incoming solar radiation
#     :param Rso: clear sky solar radiation
#     :return: Rnl in MJ/(m^2 * day)
#     """
#
#     # # in MJ/(K^4 * m^2 * day)
#     boltzman_c = 4.903e-9
#     # print(boltzman_c)
#     mid_term = (0.34 - (0.14 * math.sqrt(e_actual)))
#     print('middle term', mid_term)
#     fcd = ((1.35 * (Rs / Rso)) - 0.35)
#     print('ratio term (fcd)', fcd)
#     T4 = (((Tmax + 273.16)**4) + (Tmin + 273.16)**4)/2
#     print('t4 term', T4)
#     # print('t4 times boltzman', (((Tmax + 273.16)**4 + (Tmin + 273.16)**4)/2)*boltzman_c)
#
#     Rnl = fcd * mid_term * T4 * boltzman_c
#     print('proper Rnl', Rnl)
#
#     # # simplification from DeBruin ASCE pg 80 (if no humidity data available)
#     # Rnl = 140 * (Rs/Ra)
#
#     return Rnl
#
# def calc_Rn(Rns, Rnl, mm=True):
#     """
#     Calculate net radiation
#     :param Rns:
#     :param Rnl:
#     :param mm: True if we want mm equivalent of net rad for PM equation
#     :return:
#     """
#
#
#     Rn = Rns - Rnl
#
#     if mm:
#         Rn *= 0.408
#
#     return Rn
#
# ## Now we're at the FS1 Step
#
# def calculate_daily_penman(Rn, DT, PT, TT, e_sat, e_actual):
#     """
#     Calculate daily PM ref et in mm/day
#     :param Rn:
#     :param DT:
#     :param PT:
#     :param TT:
#     :param e_sat:
#     :param e_actual:
#     :return:
#     """
#     ETrad = DT * Rn
#     ETwind = PT * TT * (e_sat - e_actual)
#     ETo = ETwind + ETrad
#
#     return ETo
#




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


