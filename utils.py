""" Utility functions for project"""
import pandas as pd
import time
import json
import nilmtk
import hart_85 as algo
import requests
from nilmtk.utils import print_dict
from nilmtk import DataSet
from nilmtk.dataset_converters import convert_redd
from datetime import datetime
import os


REPORT_TYPE_INFO = 'info'
REPORT_TYPE_WARNING = 'warning'

HOSTNAME_DEV = 'http://localhost:3000'
HOSTNAME_PROD = 'https://nilmtk-service.firebaseapp.com'

HOSTNAME = HOSTNAME_DEV if os.getenv("RUNTIME_ENV") == 'development' else HOSTNAME_PROD

SEND_REPORTS = os.getenv("SEND_REPORTS")


def output(text):
    print('utils.py: {}'.format(text))


def match_results(submeters, predictions):
    algorithm = algo.Hart85()
    return algorithm.best_matched_appliance(submeters, predictions)


def current_milli_time():
    return int(round(time.time() * 1000))


def send_report(deviceId, reportText, reportType='info', appliance=''):

    now = current_milli_time()

    # TODO change this when running in production
    deviceSecret = "deviceAGM23nds8xnkdSga"

    if SEND_REPORTS == 'enabled':
        # send report to API
        r = requests.post(HOSTNAME + "/api/report",
                          headers={'Content-Type': 'application/json',
                                   'Authorization': 'Bearer ' + deviceSecret},
                          json={'deviceId': deviceId, 'applianceId': appliance, 'reportType': reportType, 'text': reportText, 'date': now})
        output(r.status_code, r.reason)


def send_report_summary(summary):

    deviceSecret = "deviceAGM23nds8xnkdSga"

    if SEND_REPORTS == 'enabled':
        r = requests.post(HOSTNAME + "/api/summary",
                          headers={'Content-Type': 'application/json',
                                   'Authorization': 'Bearer ' + deviceSecret},
                          json={'summary': summary})
        output(r.status_code, r.reason)


def convert_data():
    output("Converting data to H5 format...")
    convert_redd('data/REDD/low_freq',
                 'data/redd.h5')
    output("Converting data to H5 format complete.")


def update_model(training_building):
    # train the model on the data recieved
    mains = training_building.mains()
    # the remote service will already provide a model, but for this example
    # we include the training step and upload the model to remote server
    url = train_and_upload_model(mains)
    output('Updating model done.')
    return url


def train_and_upload_model(mains):
    algorithm = algo.Hart85()

    output('Training model...')
    start = time.time()
    algorithm.train(mains, columns=[('power', 'apparent')])
    algorithm.export_model('models/latest_model.pickle')
    end = time.time()
    output('Training model done. {} seconds'.format(end - start))

    output('Uploading model...')
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
    output("Model uploaded to remote server:", link)
    end = time.time()
    output('Uploading model done. {} seconds'.format(end - start))
    return link


def disaggregate(mains, path):
    h = algo.Hart85()

    output('Importing model from {}'.format(path))
    h.import_model(path)

    output('Disaggregating mains...')
    start = time.time()
    output = nilmtk.HDFDataStore('data/disaggregation_store.h5', 'w')
    predictions = h.disaggregate(mains, output)
    end = time.time()
    output('Disaggregating mains done. {} seconds'.format(end - start))

    output.close()
    return predictions


def init(building_number, start='2011-04-25', end='2011-04-26'):
    output('Importing dataset...')
    data_set = nilmtk.DataSet('data/redd.h5')

    output('Importing dataset done. {} buildings'.format(len(data_set.buildings)))
    building_data = data_set.buildings[building_number].elec

    output('Full timeframe for data {}'.format(building_data.get_timeframe()))

    data_set.set_window(start=start, end=end)

    output('Timeframe set for data {}'.format(building_data.get_timeframe()))

    return building_data


def get_payload_for_appliance(building_data, appliance, id):    
    output('getting payload for {}'.format(appliance))
    df_appliance = next(building_data[appliance, id].load())
    
    timestamp, load, date = [], [], []
    for timestamp_datetime, j in df_appliance.iterrows():
        timestampResult = timestamp_to_milliseconds(timestamp_datetime)
        dateResult = datetime.utcfromtimestamp(timestampResult).strftime('%Y-%m-%d')
        timestamp.append(timestampResult)
        date.append(dateResult)

    for value in df_appliance['power', 'active']:
        load.append(value)

    payload = {'appliance': appliance, 'load': []}
    payload['load'] = [{'timestamp': t, 'load': l, 'date': d}
                       for t, l, d in zip(timestamp, load, date)]

    return payload


def get_payload_for_unknown_appliance(predictions, appliance_index):
    output('getting payload for {}'.format(appliance_index))

    timestamp, load = [], []
    for timestamp_datetime, value in predictions[appliance_index].iteritems():
        load.append(value)
        timestamp.append(timestamp_to_milliseconds(timestamp_datetime))

    payload = {'appliance': appliance_index, 'load': []}
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
