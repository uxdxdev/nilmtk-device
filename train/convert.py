#!/usr/bin/env python

from nilmtk.utils import print_dict
from nilmtk import DataSet
from nilmtk.dataset_converters import convert_redd

print("Converting data to H5 format...")
convert_redd('../data/REDD/low_freq',
             '../data/redd.h5')
print("Converting data to H5 format complete.")
