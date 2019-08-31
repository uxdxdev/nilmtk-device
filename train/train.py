#!/usr/bin/env python

import sys
sys.path.append('../')
import requests
import time
import hart_85 as algo


def train(mains):
    h = algo.Hart85()

    print('Training model...')
    start = time.time()
    h.train(mains, columns=[('power', 'apparent')])
    h.export_model('models/latest_model.pickle')
    end = time.time()
    print('Training model done. {} seconds'.format(end - start))

    print('Uploading model...')
    start = time.time()
    # export the model to a remote server
    files = {
        'file': ('models/latest_model.pickle', open('models/latest_model.pickle', 'rb')),
    }

    # file.io allows the file to be downloaded only once
    # this step should be refactored to use an appropriate
    # file storage API
    response = requests.post('https://file.io/', files=files)
    json = response.json()
    link = json['link']
    print("Model uploaded to remote server:", link)
    end = time.time()
    print('Uploading model done. {} seconds'.format(end - start))
    return link
