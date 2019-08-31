#!/usr/bin/env python

import nilmtk
from nilmtk import HDFDataStore
import hart_85 as algo
import time


def disaggregate(mains, path):
    h = algo.Hart85()

    print('Importing model from', path)
    h.import_model(path)

    print('Disaggregating mains...')
    start = time.time()
    output = HDFDataStore('data/hart_redd_output.h5', 'w')
    predictions = h.disaggregate(mains, output)
    end = time.time()
    print('Disaggregating mains done. {} seconds'.format(end - start))

    output.close()
    return predictions
