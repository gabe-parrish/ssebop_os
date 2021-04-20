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
"""This script stores various functions that calculate statistics used in Phil Blankenau's paper
on Bias in gridded datasets.
"""
import math
import sys


def kling_gupta_efficiency(ed):
    """A statistic that measures model accuracy.
    see Gupta et al. 2009 for details"""
    return 1 - ed


def kge_ed(r, alpha, beta):
    """Kling-Gupta Efficiency Euclidean Distance"""
    pytho = (((r-1)**2) + ((alpha-1)**2) + ((beta-1)**2))
    ed = math.sqrt(pytho)
    return ed

def alpha(sigma_m, sigma_o):
    """
    ...
    :param sigma_m: model standard deviation
    :param sigma_o: observed standard deviation
    :return:
    """
    return sigma_m/sigma_o


def beta(mu_m, mu_o):
    """

    :param mu_m: modeled data mean
    :param mu_o: observed data mean
    :return:
    """

    return mu_m/mu_o


def pearson_r(y_o, y_m, n):
    """
    a measuer of linear correlation between two sets of data: The covariates of two
    variables, divided by the standard deviation...
    :param y_o: iterable
    :param y_m: iterable
    :param n: len of each iterable
    :return: float
    """
    # TODO - fix this function. Pearson's r is much too SMALL

    # DO a check to make sure that n is the same as len() of the other two params
    if not len(y_m)==n and len(y_o) == n:
        print('pearson_r() observed (y_o) and modeled (y_m) iterables must\n'
              'be the same length and match param n')
        sys.exit(0)

    # getting the 'ingredients' for the pearson statistic.
    # https://www.statisticshowto.com/probability-and-statistics/correlation-coefficient-formula/
    modeled_prod = [i_o * i_m for i_o, i_m in zip(y_o, y_m)]
    observed_square = [i_o ** 2 for i_o in y_o]
    modeled_square = [i_m ** 2 for i_m in y_m]
    # get the sums
    sum_modeled_prod = sum(modeled_prod)
    sum_obs_square = sum(observed_square)
    sum_modeled_square = sum(modeled_square)
    model_sum = sum(y_m)
    obs_sum = sum(y_o)

    # getting the means
    # numerator of the pearson coeff
    num = (n * (sum_modeled_prod)) - (obs_sum * model_sum)
    # denominator of the pearson coeff
    denom = math.sqrt(((n * sum_obs_square)-(obs_sum ** 2))*((n * sum_modeled_square) - (model_sum ** 2)))

    return num/denom


def mbe_stat(y_o, y_m, n):
    """
    Mean Bias Error
    :param y_o: iterable
    :param y_m: iterable
    :param n: n
    :return:
    """
    # DO a check to make sure that n is the same as len() of the other two params
    if not len(y_m) == n and len(y_o) == n:
        print('pearson_r() observed (y_o) and modeled (y_m) iterables must\n'
              'be the same length and match param n')
        sys.exit(0)

    diff_lst = [i_m - i_o for i_m, i_o in zip(y_m, y_o)]
    return (1/n) * sum(diff_lst)


def sde_stat(y_o, y_m, n, mbe):
    """
    Standard Deviation of Error
    :param y_o: iterable
    :param y_m: iterable
    :param n: number of y_o, equivalent to number of y_m
    :param mbe: float from mbe() func (Mean Bias Error)
    :return: float statistic
    """
    # DO a check to make sure that n is the same as len() of the other two params
    if not len(y_m) == n and len(y_o) == n:
        print('pearson_r() observed (y_o) and modeled (y_m) iterables must\n'
              'be the same length and match param n')
        sys.exit(0)

    # see equation 2.8 of blankenau thesis
    squared_diff_list = [((i_m - i_o) - mbe) ** 2 for i_m, i_o in zip(y_m, y_o)]
    return math.sqrt((1/n) * sum(squared_diff_list))


def data_mean(y):
    """
    This IS your grandad's mean.
    :param y: iterable
    :return: mean
    """
    n = len(y)
    return sum(y)/n


def std_dev(y):
    """"""
    print('inside std dev')
    n = len(y)
    print('y', y)
    print('sum', sum(y))
    mn = sum(y) / n
    print('n', n)
    print('mn', mn)
    # for each number, subtract the mean and square the result
    square_dif = [(i-mn)**2 for i in y]
    # take the mean of the squared differences
    mn_square = sum(square_dif) / n
    # take the square root and thats the std dev!
    return math.sqrt(mn_square)


def calc_kge(y_o, y_m):
    """"""
    # print('indside kge')
    n = len(y_o)
    # print('n', n)
    # print(len(y_o), len(y_m))

    if not n == len(y_m):
        print(f'observed and measuerd iterables must be the same length. '
              f'You gave y_o of len {n} and y_m of {len(y_m)}')
        sys.exit()


    so = std_dev(y_o)
    sm = std_dev(y_m)
    # print(so, sm)
    mean_o = sum(y_o)/n
    mean_m = sum(y_m)/n
    # print(mean_o)
    # print(mean_m)
    a = alpha(sigma_m=sm, sigma_o=so)
    b = beta(mu_m=mean_m, mu_o=mean_o)
    r = pearson_r(y_o=y_o, y_m=y_m, n=n)
    ed = kge_ed(r=r, alpha=a, beta=b)
    # print(a, b, r, ed)

    return (kling_gupta_efficiency(ed), a, b, r)


def calc_mbe(y_o, y_m):
    """"""
    n = len(y_o)

    if not n == len(y_m):
        print(f'observed and measuerd iterables must be the same length. '
              f'You gave y_o of len {n} and y_m of {len(y_m)}')
        sys.exit()

    return mbe_stat(y_o=y_o, y_m=y_m, n=n)

def calc_sde(y_o, y_m):
    """"""
    n = len(y_o)

    if not n == len(y_m):
        print(f'observed and measuerd iterables must be the same length. '
              f'You gave y_o of len {n} and y_m of {len(y_m)}')
        sys.exit()

    mbe = mbe_stat(y_o=y_o, y_m=y_m, n=n)

    return sde_stat(y_o=y_o, y_m=y_m, n=n, mbe=mbe)

