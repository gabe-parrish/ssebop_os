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

""" These functions are useful for calculating daily reference ET from a Meteorological station and have been 
checked against Leyendecker II met station at NMSU in Las Cruces."""

# def conv_wattflux_2_MJflux()

def conv_date_to_jdate(datetime_obj):
    """"""
    pass

def conv_lat_deg2rad(degrees_lat):
    """

    :param degrees_lat:
    :return:
    """

    rad_lat = (math.pi / 180) * degrees_lat
    return rad_lat

def conv_F_to_C(tempF):
    """
    Convert Farhenheit to Celcius
    :param tempF: Degrees F
    :return: tempC
    """
    tempC = (tempF - 32) * (5/9)
    return tempC

def conv_mph_to_mps(mph):
    """
    converts miles per hour to meters per second
    :param mph:
    :return:
    """
    mps = mph * 0.44704
    return mps

def conv_f_to_m(foot_lenght):
    """
    Convert feet to meters
    :param foot_lenght:
    :return:
    """
    m = foot_lenght / 3.28084
    return m

def calc_Tmean(Tmax, Tmin, metric=True):
    """
    Calculate mean daily temp. If only mean temp is available it
     can be used but will cause other errors in calculations
    :param Tmax: daily max temp in degrees celcius
    :param Tmin: daily min temp in degrees celcius
    :param metric: bool True if units are metric
    :return: Tmean in degrees C
    """
    if metric:
        Tmean = (Tmax + Tmin) / 2

    else:
        print('assuming temp in F')
        Tmax = conv_F_to_C(Tmax)
        Tmin = conv_F_to_C(Tmin)
        Tmean = (Tmax + Tmin) / 2

    return Tmean

def calc_u2(uh, h, metric=True):
    """
    Calculate the windspeed in meters per second at 2m height based on a given height and windspeed
    :param uh: windspeed measured by instrument in meters per second
    :param h: Height of instrument in meters
    :param metric: bool True if units are metric
    :return:
    """

    if h == 2.0 and metric:
        u2 = uh
    else:
        if metric:
            print('windspeed units are given in meters per second')
            u2 = uh * (4.87 / math.log((67.8*h) - 5.42))
        else:
            print('assuming windspeed units are in MPH and instrument height in feet')
            uh = conv_mph_to_mps(uh)
            h = conv_f_to_m(h)
            u2 = uh * (4.87 / math.log((67.8 * h) - 5.42))
    return u2

def calc_delta(Tmean):
    """
    Given a Tmean in Celcius calculate the SLOPE of the saturation vapor curve
    :param Tmean: mean temp calculated from Tmax and Tmin
    :return: delta slope of sat vapor curve in Kpa/degC
    """
    a = math.exp((17.27 * Tmean)/(Tmean + 237.3))
    # a = math.e ** ((17.27 * Tmean)/(Tmean + 237.3))
    b = (Tmean + 237.3)**2

    delta = (4098 * (0.6108 * a)) / b

    # # ASCE pg 36 (which one) makes value bigger
    # delta = (2503 * (0.6108 * a)) / b
    return delta

def calc_atmP(z, metric=True):
    """
    Calculating atmospheric pressure based on elevation using simplification
     of ideal gas law assuming 20C for a standard atmosphere
    :param z: elevation in meters above sealevel
    :param metric: bool True if units are metric
    :return: p_atm in kPa
    """

    if metric:
        p_atm = 101.3 * (((293 - (0.0065 * z))/293)**5.26)

    else:
        print('assuming the elevation is in feet above sea level')
        z = conv_f_to_m(z)
        p_atm = 101.3 * (((293 - (0.0065 * z)) / 293) ** 5.26)

    return p_atm

def calc_psych_const(p_atm):
    """
    A simplified way of calculating the psychrometric constant assuming no change of latent heat of vap with temp or
    changes in specific heat based on changing humidity
    :param p_atm: atmospheric pressure based on elevation in meters above sealevel in kPa.
    :return: psych_const in units of kPa/C
    """
    psych_const = 0.000665 * p_atm
    return psych_const

def calc_DT(delta, psych_const, u2_vel):
    """
    Calculate the Delta Term, the auxiliary calculation for the radiation component
    :param delta: slope of pressure temp curve kPa/C
    :param psych_const: psychrometric constant KPa/C
    :param u2_vel: velocity at 2m height in m/s
    :return: DT term (s/m ??)
    """

    DT = delta / (delta + (psych_const * (1 + (0.34 * u2_vel))))
    return DT

def calc_PT(delta, psych_const, u2_vel):
    """
    Calculate the Psi Term
    :param delta: slope of pressure temp curve kPa/C
    :param psych_const: psychrometric constant KPa/C
    :param u2_vel: velocity at 2m height in m/s
    :return: PT
    """

    PT = psych_const / (delta + (psych_const * (1 + (0.34 * u2_vel))))
    return PT

def calc_TT(Tmean, u2_vel):
    """

    :param Tmean: mean temp calculated from Tmax and Tmin
    :param u2_vel: velocity at 2m height in m/s
    :return: TT term (m/(degC * s)??)
    """

    TT = (900 / (Tmean + 273))* u2_vel
    return TT

def calc_sat_vp(Tmax, Tmin):
    """
    :param Tmax:
    :param Tmin:
    :return:
    """

    e_tmax = 0.6108 * (math.exp((17.27 * Tmax)/(Tmax + 237.3)))
    e_tmin = 0.6108 * (math.exp((17.27 * Tmin) / (Tmin + 237.3)))
    # get mean saturation vapor pressure from the sat vapor pressure at min and max
    e_sat = (e_tmax + e_tmin) / 2

    return (e_sat, e_tmax, e_tmin)

def calc_e_actual(rh_max=None, rh_min=None, e_tmax=None, e_tmin=None, rhmax_only=False, rh_mean=None):
    """

    :param rh_max: maximum daily relative humidity as %
    :param rh_min: minimum daily relative humidity as %
    :param e_tmax:
    :param e_tmin:
    :param rhmax_only: bool True only if RHmin where error could be relatively large or if data is in doubt
    :param rh_mean: None unless the rh max and min are not available
    :return: e_actual in kPa
    """
    if rhmax_only:
        print('calculating with Rxmax only')
        e_actual = e_tmin * (rh_max / 100)
    elif rh_mean is not None:
        print('using Rh mean actual vapor pressur calc')
        e_actual = ((e_tmin + e_tmax) / 2) * (rh_mean/100)
    # this is the default unless data is suspect or missing
    else:
        print('calculating e actual as the default')
        e_actual = ((e_tmin*(rh_max/100)) + (e_tmax*(rh_min/100))) / 2
    # moreover, if humidity data overall is very unreliable you can assume that e_actual = e_tmin
    return e_actual

def calc_dr(julian_date):
    """
    Calculate the inverse relative distance Earth-Sun.
    :param julian_date:
    :return:
    """
    dr = 1 + (0.033 * math.cos(((2 * math.pi) / 365) * julian_date))
    return dr

def calc_sol_decl(julian_date):
    """

    :param julian_date:
    :return:
    """
    sol_decl = 0.409 * (math.sin((((2 * math.pi) / 365)*julian_date) - 1.39))
    return sol_decl

def calc_sunsethour_angle(lat_rad, sol_decl):
    """

    :param lat_rad: radians
    :param sol_decl: radians (or dimensionless???)
    :return: omega
    """
    omega_sun = math.acos(-math.tan(lat_rad) * math.tan(sol_decl))
    return omega_sun


def calc_Ra(dr, omega_sun, lat_rad, sol_decl):
    """
    Calculate Extraterrestrial Radiation (Ra) in MJ/(m^2 * day)
    :param dr:
    :param omega_sun:
    :param lat_rad:
    :param sol_decl:
    :return: Ra extraterrestrial radiation
    """

    # define the solar constant in MJ/(m^2 * min)
    Gsc = 0.0820

    Ra = ((24 * 60) / (math.pi)) * Gsc * dr * ((omega_sun * math.sin(lat_rad) * math.sin(sol_decl)) +
                                              (math.cos(lat_rad) * math.cos(sol_decl) * math.sin(omega_sun)))
    return Ra

def calc_Rso(z, Ra):
    """
    Calculate Clear Sky radiation in in MJ/(m^2 * day)
    :param z: elevation above sealevel in m
    :param Ra: extraterrestrial radiation in MJ/(m^2 * day)
    :return: Rso in in MJ/(m^2 * day)
    """

    Rso = (0.75 + (2e-5 * z)) * Ra
    return Rso

# step 17 Net solar or net shortwave

def calc_Rns(Rs, a=0.23):
    """
    calculate net shortwave.
    :param Rs: net solar radiation in MJ/(m^2 * day)
    :param a: albedo set to 0.23 dimensionless for grass ETo reference
    :return:
    """

    Rns = (1 - a) * Rs
    return Rns

def calc_Rnl(Tmax, Tmin, e_actual, Rs, Rso, Ra=None):
    """
    Rate of outgoing long wave radiation is proportional to the temperature of the surace raised to the fourth.
    :param Tmax: maximum temp deg C
    :param Tmin: min temp deg C
    :param e_actual: actual vapor pressure in kPa
    :param Rs: incoming solar radiation
    :param Rso: clear sky solar radiation
    :return: Rnl in MJ/(m^2 * day)
    """

    # # in MJ/(K^4 * m^2 * day)
    boltzman_c = 4.903e-9
    # print(boltzman_c)
    mid_term = (0.34 - (0.14 * math.sqrt(e_actual)))
    print('middle term', mid_term)
    fcd = ((1.35 * (Rs / Rso)) - 0.35)
    print('ratio term (fcd)', fcd)
    T4 = (((Tmax + 273.16)**4) + (Tmin + 273.16)**4)/2
    print('t4 term', T4)
    # print('t4 times boltzman', (((Tmax + 273.16)**4 + (Tmin + 273.16)**4)/2)*boltzman_c)

    Rnl = fcd * mid_term * T4 * boltzman_c
    print('proper Rnl', Rnl)

    # # simplification from DeBruin ASCE pg 80 (if no humidity data available)
    # Rnl = 140 * (Rs/Ra)

    return Rnl

def calc_Rn(Rns, Rnl, mm=True):
    """
    Calculate net radiation
    :param Rns:
    :param Rnl:
    :param mm: True if we want mm equivalent of net rad for PM equation
    :return:
    """


    Rn = Rns - Rnl

    if mm:
        Rn *= 0.408

    return Rn

## Now we're at the FS1 Step

def calculate_daily_penman(Rn, DT, PT, TT, e_sat, e_actual):
    """
    Calculate daily PM ref et in mm/day
    :param Rn:
    :param DT:
    :param PT:
    :param TT:
    :param e_sat:
    :param e_actual:
    :return:
    """
    ETrad = DT * Rn
    ETwind = PT * TT * (e_sat - e_actual)
    ETo = ETwind + ETrad

    return ETo

