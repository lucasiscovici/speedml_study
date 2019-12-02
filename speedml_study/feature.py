"""
Speedml Feature component with methods that work on dataset features or the feature engineering workflow. Contact author https://twitter.com/manavsehgal. Code, docs and demos https://speedml.com.
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

from .base import Base
from .util import DataFrameImputer

import numpy as np
from sklearn.preprocessing import LabelEncoder
import re

class Feature(Base):
    def drop(self, cols):
        """
        Drop one or more list of strings naming ``features`` from train and test datasets.
        """
        Base =self
        features= cols
        start = Base.train.shape[1]

        Base.train = Base.train.drop(features, axis=1)
        Base.test = Base.test.drop(features, axis=1)

        end = Base.train.shape[1]
        message = 'Dropped {} features with {} features available.'
        return message.format(start - end, end)

    def impute(self):
        """
        Replace empty values in the entire dataframe with median value for numerical features and most common values for text features.
        """
        Base =self
        start = Base.train.isnull().sum().sum()

        Base.test[Base.target] = -1
        combine = Base.train.append(Base.test)
        combine = DataFrameImputer().fit_transform(combine)
        Base.train = combine[0:Base.train.shape[0]]
        Base.test = combine[Base.train.shape[0]::]
        Base.test = Base.test.drop([Base.target], axis=1)

        end = Base.train.isnull().sum().sum()
        message = 'Imputed {} empty values to {}.'
        return message.format(start, end)

    def mapping(self, **kwargs):
        """
        Convert values for categorical feature ``a`` using ``data`` dictionary. Use when number of categories are limited otherwise use labels.
        kwargs=dict(COLNAME=dict(VALUE_TO_REPLACE=REPLACE_VALUE))
        """
        Base =self
        a=list(kwargs.keys())[0]
        data=list(kwargs.values())[0]
        Base.train[a] = Base.train[a].apply(lambda x: data[x])
        Base.test[a] = Base.test[a].apply(lambda x: data[x])

    def fillna(self, a, new):
        """
        Fills empty or null values in ``a`` feature name with ``new`` string value.
        """
        Base =self
        start = Base.train[a].isnull().sum() + Base.test[a].isnull().sum()

        Base.train[a] = Base.train[a].fillna(new)
        Base.test[a] = Base.test[a].fillna(new)

        message = 'Filled {} null values across test and train datasets.'
        return message.format(start)

    def replace(self, col, match, newValue): # a, match, newValue
        """
        In feature ``col`` values ``match`` string or list of strings and replace with a ``newValue`` string.
        """
        a=col
        new=newValue
        Base =self
        if type(match) is str:
            # [TODO] What is the performance cost of message ops?
            start = Base.train[Base.train[a] == match][a].shape[0] + Base.test[Base.test[a] == match][a].shape[0]
            message = 'Replaced {} matching values across train and test datasets.'
            message = message.format(start)
        else:
            # [TODO] Can we possibly use pandas.isin to check counts?
            message = 'Replaced matching list of strings across train and test datasets.'

        Base.train[a] = Base.train[a].replace(match, new)
        Base.test[a] = Base.test[a].replace(match, new)

        return message

    def outliers(self, col, lower = None, upper = None):
        """
        Fix outliers for ``lower`` or ``upper`` or both percentile of values within ``col`` feature.
        """
        Base =self
        a=col
        if upper:
            upper_value = np.percentile(Base.train[a].values, upper)
            change = Base.train.loc[Base.train[a] > upper_value, a].shape[0]
            Base.train.loc[Base.train[a] > upper_value, a] = upper_value
            message = 'Fixed {} or {:.2f}% upper outliers. '.format(change, change/Base.train.shape[0]*100)

        if lower:
            lower_value = np.percentile(Base.train[a].values, lower)
            change = Base.train.loc[Base.train[a] < lower_value, a].shape[0]
            Base.train.loc[Base.train[a] < lower_value, a] = lower_value
            message = message + 'Fixed {} or {:.2f}% lower outliers.'.format(change, change/Base.train.shape[0]*100)

        return message

    def _density_by_feature(self, col):
        Base =self
        a=col
        vals = Base.train[a].value_counts()
        dvals = vals.to_dict()
        Base.train[a + '_density'] = Base.train[a].apply(lambda x: dvals.get(x, vals.min()))
        Base.test[a + '_density'] = Base.test[a].apply(lambda x: dvals.get(x, vals.min()))

    def density(self, col):
        """
        Create new feature named ``col`` feature name + suffix '_density', based on density or value_counts for each unique value in ``a`` feature specified as a string or multiple features as a list of strings.
        """
        Base =self
        a=col
        if isinstance(a, str):
            self._density_by_feature(a)

        if isinstance(a, list):
            for feature in a:
                self._density_by_feature(feature)

    def add(self, col, num):
        """
        Update ``col`` numeric feature by adding ``num`` number to each values.
        """
        Base =self
        a=col
        Base.train[a] = Base.train[a] + num
        Base.test[a] = Base.test[a] + num

    def sum(self, *args ,newCol):
        """
        Create ``newCol`` numeric feature by adding argsfeature values.
        """
        Base =self
        Base.train[newCol] = Base.train[args].sum(axis=1)
        Base.test[newCol] = Base.test[args].sum(axis=1)

    def diff(self, *args ,newCol):
        """
        Create ``newCol`` numeric feature by subtracting args feature values.
        """
        Base =self
        a=args[0]
        args=args[1:]
        Base.train[newCol] = Base.train[a] - Base.train[args].sum(axis=1)
        Base.test[newCol] = Base.test[a] - Base.test[args].sum(axis=1)

    def product(self,  *args ,newCol):
        """
        Create ``newCol`` numeric feature by multiplying args feature values.
        """
        Base =self
        Base.train[newCol] = Base.train[args].prod(axis=1)
        Base.test[newCol] = Base.test[args].prod(axis=1)

    def divide(self, *args ,newCol):
        """
        Create ``newCol`` numeric feature by dividing args feature values. Replace division-by-zero with zero values.
        """
        Base =self
        new=newCol
        a=args[0]
        args=args[1:]
        Base.train[new] = Base.train[a] / Base.train[args].prod(axis=1)
        Base.test[new] = Base.test[a] / Base.test[b].prod(axis=1)
        # Histograms require finite values
        Base.train[new] = Base.train[new].replace([np.inf, -np.inf], 0)
        Base.test[new] = Base.test[new].replace([np.inf, -np.inf], 0)

    def round(self, *args, newCol, precision=2):
        """
        Create ``newCol`` numeric feature by rounding args features value to ``precision`` decimal places.
        """
        Base =self
        new=newCol
        Base.train[new] = round(Base.train[args], precision)
        Base.test[new] = round(Base.test[args], precision)

    def concat(self, *args, newCol, sep=""):
        """
        Create ``new`` text feature by concatenating ``a`` and ``b`` text feature values, using ``sep`` separator.
        """
        Base =self
        new=newCol
        a=args[0]
        args=args[1:]
        Base.train[new] = Base.train[a].str.cat(Base.train[args].astype(str),sep=sep)
        Base.test[new] = Base.test[a].str.cat(Base.test[args].astype(str),sep=sep)

    def list_len(self, newCol, col):
        """
        Create ``new`` numeric feature based on length or item count from ``a`` feature containing list object as values.
        """
        Base =self
        new=newCol
        a=col
        Base.train[new] = Base.train[a].apply(len)
        Base.test[new] = Base.test[a].apply(len)

    def word_count(self, newCol, col):
        """
        Create ``new`` numeric feature based on length or word count from ``a`` feature containing free-form text.
        """
        Base =self
        new=newCol
        a=col
        Base.train[new] = Base.train[a].apply(lambda x: len(x.split(" ")))
        Base.test[new] = Base.test[a].apply(lambda x: len(x.split(" ")))

    def _regex_text(self, regex, text):
        regex_search = re.search(regex, text)
        # If the word exists, extract and return it.
        if regex_search:
            return regex_search.group(1)
        return ""

    def extract(self, col, regex, newCol=None):
        """
        Match ``regex`` regular expression with ``a`` text feature values to update ``a`` feature with matching text if ``new`` = None. Otherwise create ``new`` feature based on matching text.
        """
        Base =self
        a=col
        new=newCol
        Base.train[new if new else a] = Base.train[a].apply(lambda x: self._regex_text(regex=regex, text=x))
        Base.test[new if new else a] = Base.test[a].apply(lambda x: self._regex_text(regex=regex, text=x))

    def labels(self, cols):
        """
        Generate numerical labels replacing text values from list of categorical ``features``.
        """
        Base =self
        features=cols
        Base.test[Base.target] = -1
        combine = Base.train.append(Base.test)

        le = LabelEncoder()
        for feature in features:
            combine[feature] = le.fit_transform(combine[feature])

        Base.train = combine[0:Base.train.shape[0]]
        Base.test = combine[Base.train.shape[0]::]
        Base.test = Base.test.drop([Base.target], axis=1)
