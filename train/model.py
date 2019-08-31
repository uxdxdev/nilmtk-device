#!/usr/bin/env python

import nilmtk
from nilmtk import DataSet
import train


def update_model():
    print('Updating model...')
    # simulate receiving mains data from remote monitoring device
    # by loading dataset and restrict to 1 week
    print('Loading dataset...')
    data = DataSet('data/redd.h5')
    print('Loaded', len(data.buildings), 'buildings')

    building = 1
    data.set_window(start='2011-04-20', end='2011-04-27')

    training_building = data.buildings[building].elec
    # train the model on the data recieved
    mains = training_building.mains()
    # the remote service will already provide a model, but for this example
    # we include the training step and upload the model to remote server
    url = train.train(mains)
    print('Updating model done.')
    return url
