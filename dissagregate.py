#!/usr/bin/env python

import nilmtk
from nilmtk import HDFDataStore
import hart_85 as algo
import time
import urllib.request


def dissagregate(mains, link=""):
    h = algo.Hart85()

    print('Importing model...')
    start = time.time()

    if link:
        # use model hosted on remote server
        url = link
        urllib.request.urlretrieve(url, 'models/latest_model.pickle')

    h.import_model('models/latest_model.pickle')
    end = time.time()
    print('Importing model done. {} seconds'.format(end - start))

    print('Disaggregating mains...')
    start = time.time()
    output = HDFDataStore('data/hart_redd_output.h5', 'w')
    predictions = h.disaggregate(mains, output)
    end = time.time()
    print('Disaggregating mains done. {} seconds'.format(end - start))

    output.close()
    return predictions
