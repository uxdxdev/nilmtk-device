""" Utility functions for project"""
import pandas as pd
import time
import json
from threading import Thread
import nilmtk
import hart_85 as algo
import requests
from nilmtk.utils import print_dict
from nilmtk import DataSet
from nilmtk.dataset_converters import convert_redd


def current_milli_time(): return int(round(time.time() * 1000))


def send_report(deviceId, reportText):
    now = current_milli_time()

    # send report to API
    r = requests.post("https://nilmtk-service.firebaseapp.com/api/report",
                      headers={'Content-Type': 'application/json'},
                      json={'deviceId': deviceId, 'text': reportText, 'date': now})
    print(r.status_code, r.reason)


def convert_data():
    print("Converting data to H5 format...")
    convert_redd('data/REDD/low_freq',
                 'data/redd.h5')
    print("Converting data to H5 format complete.")


def update_model():
    print('Updating model...')
    training_building = init(1)
    # train the model on the data recieved
    mains = training_building.mains()
    # the remote service will already provide a model, but for this example
    # we include the training step and upload the model to remote server
    url = train_and_upload_model(mains)
    print('Updating model done.')
    return url


def train_and_upload_model(mains):
    algorithm = algo.Hart85()

    print('Training model...')
    start = time.time()
    algorithm.train(mains, columns=[('power', 'apparent')])
    algorithm.export_model('models/latest_model.pickle')
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


def disaggregate(mains, path):
    h = algo.Hart85()

    print('Importing model from', path)
    h.import_model(path)

    print('Disaggregating mains...')
    start = time.time()
    output = nilmtk.HDFDataStore('data/disaggregation_store.h5', 'w')
    predictions = h.disaggregate(mains, output)
    end = time.time()
    print('Disaggregating mains done. {} seconds'.format(end - start))

    output.close()
    return predictions


def init(building_number):
    print('Importing dataset...')
    data_set = nilmtk.DataSet('data/redd.h5')
    print('Importing dataset done.', len(data_set.buildings), 'buildings')
    data_set.set_window(start='2011-04-25', end='2011-04-26')
    building_data = data_set.buildings[building_number].elec
    return building_data


def get_payload_for_appliance(building_data, appliance):
    """ Returns JSON object of appliance name, load, and timestamp.

    Parameters
    ----------
    building_data : DataSet.OrderedDict.elec
        Building data from NILMTK DataSet. E.g building_data = data_set.buildings[1].elec

    appliance: string
        Name of the appliance in building_data.

    Example:
    {
        "appliance":"fridge",
        "load:[
            {
                "timestamp": 1379897298,
                "load": 6.0
            },
            {
                "timestamp": 1379897301,
                "load": 7.0
            }
        ]
    }
    """
    print('getting payload for', appliance)
    df_appliance = next(building_data[appliance, 1].load())

    timestamp, load = [], []
    for datetime, j in df_appliance.iterrows():
        timestamp.append(timestamp_to_milliseconds(datetime))

    for value in df_appliance['power', 'active']:
        load.append(value)

    payload = {'appliance': appliance, 'load': []}
    payload['load'] = [{'timestamp': t, 'load': l}
                       for t, l in zip(timestamp, load)]

    return payload


def timestamp_to_milliseconds(timestamp):
    """ Convert Timestamp data structure ot miiliseconds

    Parameters
    ----------
    timestamp : Timestamp
        Timestamp data.
    """
    return int(round(time.mktime(timestamp.timetuple())))


def write_to_json_file(appliance, payload):
    with open('payloads/' + appliance + '.json', 'w') as outfile:
        json.dump(payload, outfile)
