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
import matplotlib.pyplot as plt
# ============= standard library imports ========================
from utils.os_utils import windows_path_fix

"""This script will calculate daily reference ET for the Leyendecker Met Station at NMSU. It is intended to be 
rewritten and have its functionality generalized. Procedure sourced from
 Zotarelli et al 'Step by Step Calculation of the Penman-Monteith Evapotranspiration (FAO-56 Method)'
  by the University of Florida."""


# === inputs ===

# daily meteorological data for the year 2012

ld_csv = pd.read_csv(r'Z:\Users\Gabe\refET\jupyter_nbs\weather_station_data\leyendecker_2012_daily.csv')
print(ld_csv.head)

print(ld_csv.columns.to_list())

print(ld_csv.loc[207].to_list())

print(ld_csv.loc[207])


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
            u2 = uh * (4.87 / math.ln((67.8*h) - 5.42))
        else:
            print('assuming windspeed units are in MPH and instrument height in feet')
            uh = conv_mph_to_mps(uh)
            h = conv_f_to_m(h)
            u2 = uh * (4.87 / math.ln((67.8 * h) - 5.42))
    return u2

def calc_delta(Tmean):
    """
    Given a Tmean in Celcius calculate the SLOPE of the saturation vapor curve
    :param Tmean: mean temp calculated from Tmax and Tmin
    :return: delta slope of sat vapor curve in Kpa/degC
    """
    a = math.exp((17.27 * Tmean)/(Tmean + 237.3))
    b = (Tmean + 237.3)**2

    delta = (4098 * (0.6108 * a)) / b
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



# Make the functions first and apply them to the dataframe as they are applicable.

# Get 1 day's data as a sample to work with: July 26 2012 aka Day 208 index 207








