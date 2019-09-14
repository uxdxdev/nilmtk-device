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


def check_on_off_states(payload, delaySeconds=0.0):

    DEVICE_ID = os.getenv("DEVICE_ID")

    appliance = payload["appliance"]
    print("checking on/off states for", appliance)
    load = payload["load"]

    averageOnLoad = 0
    sumOnLoad = 0
    numberOfOnEntries = 0
    previousLoad = 0
    isApplianceOn = False
    loadSpikeDetected = False

    # ghost load is the power draw of an appliance when its plugged in
    # and on standby mode, we don't want to trigger an on state unless the
    # load draw is above the ghost load.
    ghostLoad = 40

    applianceRunningTimeStart = 0
    applianceRunningTimeEnd = 0

    switchedOnCount = 0
    sumOnRunningTime = 0

    # each entry contains the current load of an appliance at a timestamp
    # we simulate taking a measurement at "delaySeconds" frequency and
    # calculating stats based on the appliance energy usage behaviour.
    #
    # the input to this algorithm is appliance level power usage
    # post disaggregation.
    for entry in load:

        currentLoad = entry["load"]

        # measurement read frequency
        time.sleep(float(delaySeconds))

        if not isApplianceOn and currentLoad > ghostLoad:
            switchedOnCount += 1
            applianceRunningTimeStart = entry["timestamp"]
            utc_dt = datetime.utcfromtimestamp(applianceRunningTimeStart)

            print(
                str(utc_dt)
                + " "
                + str(appliance)
                + " is on. Current load "
                + str(currentLoad)
                + " previous load "
                + str(previousLoad)
            )
            isApplianceOn = True

            send_report(DEVICE_ID, 'Appliance ' +
                        str(appliance).title() + ' is on.')

        # if currentLoad < averageLoad and isApplianceOn:
        if isApplianceOn and currentLoad < ghostLoad:
            isApplianceOn = False

            loadSpikeDetected = False
            applianceRunningTimeEnd = entry["timestamp"]
            utc_dt = datetime.utcfromtimestamp(applianceRunningTimeEnd)

            runningTime = applianceRunningTimeEnd - applianceRunningTimeStart
            print(
                str(utc_dt)
                + " "
                + str(appliance)
                + " is off. Current load "
                + str(currentLoad)
                + " previous load "
                + str(previousLoad)
                + " running time:"
                + str(runningTime)
                + " seconds"
            )

            # running time measurement
            sumOnRunningTime += runningTime
            averageOnRunningTime = sumOnRunningTime / switchedOnCount

            # if running time is 50% above the average
            if runningTime > (averageOnRunningTime * 1.5):
                message = (
                    ">>>> RUNNING TIME SPIKE >>>> "
                    + str(utc_dt)
                    + " "
                    + str(appliance)
                    + " is on for 50% longer than average "
                    + str(averageOnRunningTime)
                )
                print(message)
                send_report(DEVICE_ID, 'Please check your appliance {}, it has been running for longer than usual.'.format(
                    str(appliance).title()), REPORT_TYPE_WARNING)

            send_report(DEVICE_ID, 'Appliance ' +
                        str(appliance).title() + ' is off.')

        # calculate the average on load and check if current load
        # is above the average
        if isApplianceOn:
            numberOfOnEntries += 1

            # load measurement
            sumOnLoad += currentLoad
            averageOnLoad = sumOnLoad / numberOfOnEntries

            # check for load spikes above the average load
            if not loadSpikeDetected and currentLoad > (averageOnLoad * 2.0):
                loadSpikeDetected = True
                applianceTimestamp = entry["timestamp"]
                utc_dt = datetime.utcfromtimestamp(applianceTimestamp)
                message = (
                    ">>>> LOAD SPIKE >>>> "
                    + str(utc_dt)
                    + " "
                    + str(appliance)
                    + " load of "
                    + str(currentLoad)
                    + " is above average of "
                    + str(averageOnLoad)
                )
                print(message)
                send_report(DEVICE_ID, 'Please check your appliance {}, it is using more power than usual.'.format(
                    str(appliance).title()), REPORT_TYPE_WARNING)

        previousLoad = currentLoad


def match_results(submeters, predictions):
    algorithm = algo.Hart85()
    return algorithm.best_matched_appliance(submeters, predictions)


def current_milli_time():
    return int(round(time.time() * 1000))


REPORT_TYPE_INFO = 'info'
REPORT_TYPE_WARNING = 'warning'


def send_report(deviceId, reportText, reportType='info'):
    RUNTIME_ENV = os.getenv("RUNTIME_ENV")

    now = current_milli_time()

    # TODO changes this when running in production
    deviceSecret = "deviceAGM23nds8xnkdSga"

    if RUNTIME_ENV != 'testing':
        # send report to API
        r = requests.post("http://localhost:3000/api/report",
                          # r = requests.post("https://nilmtk-service.firebaseapp.com/api/report",
                          headers={'Content-Type': 'application/json',
                                   'Authorization': 'Bearer ' + deviceSecret},
                          json={'deviceId': deviceId, 'reportType': reportType, 'text': reportText, 'date': now})
        print(r.status_code, r.reason)


def convert_data():
    print("Converting data to H5 format...")
    convert_redd('data/REDD/low_freq',
                 'data/redd.h5')
    print("Converting data to H5 format complete.")


def update_model(training_building):
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


def init(building_number, start='2011-04-25', end='2011-04-26'):
    print('Importing dataset...')
    data_set = nilmtk.DataSet('data/redd.h5')

    print('Importing dataset done.', len(data_set.buildings), 'buildings')
    building_data = data_set.buildings[building_number].elec

    print('Full timeframe for data', building_data.get_timeframe())

    data_set.set_window(start=start, end=end)

    print('Timeframe set for data', building_data.get_timeframe())

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
    for timestamp_datetime, j in df_appliance.iterrows():
        timestamp.append(timestamp_to_milliseconds(timestamp_datetime))

    for value in df_appliance['power', 'active']:
        load.append(value)

    payload = {'appliance': appliance, 'load': []}
    payload['load'] = [{'timestamp': t, 'load': l}
                       for t, l in zip(timestamp, load)]

    return payload


def get_payload_for_unknown_appliance(predictions, appliance_index):
    print('getting payload for', appliance_index)

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
