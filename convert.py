#!/usr/bin/env python

from nilmtk.utils import print_dict
from nilmtk import DataSet
from nilmtk.dataset_converters import convert_redd
convert_redd('data/REDD/low_freq',
             'data/redd.h5')
