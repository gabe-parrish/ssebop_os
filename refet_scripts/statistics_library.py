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
    # DO a check to make sure that n is the same as len() of the other two params
    if not len(y_m)==n and len(y_o) == n:
        print('pearson_r() observed (y_o) and modeled (y_m) iterables must\n'
              'be the same length and match param n')
        sys.exit(0)

    # [y_o * y_m, ....]
    modeled_prod = [i_o * i_m for i_o, i_m in zip(y_o, y_m)]
    a = sum(modeled_prod)
    # todo - is it really a product of the two sums? (blankenau Thesis)
    model_sum = sum(y_m)
    obs_sum = sum(y_o)

    # getting the means
    b = (obs_sum * model_sum)/n
    # numerator of the pearson coeff
    num = a - b

    # observed std dev
    c = (obs_sum ** 2) - ((obs_sum ** 2)/n)
    # modeled standard dev
    d = (model_sum ** 2) - ((model_sum ** 2)/n)
    # denominator of the pearson coeff
    denom = math.sqrt(c * d)

    return num/denom


def mbe(y_o, y_m, n):
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


def sde(y_o, y_m, n, mbe):
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
    n = len(y)
    mn = sum(y) / n
    # for each number, subtract the mean and square the result
    square_dif = [(i-mn)**2 for i in y]
    # take the mean of the squared differences
    mn_square = sum(square_dif) / n
    # take the square root and thats the std dev!
    return math.sqrt(mn_square)