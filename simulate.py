import argparse
import os
import utils
import EcoPush
import time
from threading import Thread
from dotenv import load_dotenv
load_dotenv()


def analyse(deviceId, appliance_payload):
    DELAY_IN_MEASUREMENT_FREQUENCY_HISTORICAL_SAMPLING = os.getenv("DELAY_IN_MEASUREMENT_FREQUENCY_HISTORICAL_SAMPLING")

    DELAY_IN_MEASUREMENT_FREQUENCY_REALTIME_SAMPLING = os.getenv("DELAY_IN_MEASUREMENT_FREQUENCY_REALTIME_SAMPLING")

    appliance = appliance_payload["appliance"]
    load = appliance_payload["load"]
    ghostLoad = 50

    # create new EcoPushMonitoringSystem
    ecoPushConfig = {
        'deviceId': deviceId,
        'appliance': appliance,
        'ghostLoad': ghostLoad
    }
    ecoPushMonitoringSystem = EcoPush.MonitoringSystem(ecoPushConfig)

    # analyse data for this date
    testDate = '2011-04-25'

    # split the dataset on the test date
    trainingData = [entry for entry in load if entry["date"] != testDate]
    testData = [entry for entry in load if entry["date"] == testDate]

    # add new day to end of test data for summary generation
    testData.append({'date': '2011-04-26', 'timestamp': 1303776000, 'load': 0})

    # import historical data
    for entry in trainingData:
        currentLoad = entry["load"]
        timestamp = entry["timestamp"]

        # delay processing to minimize number requests to cloud API to conserve quota
        time.sleep(float(DELAY_IN_MEASUREMENT_FREQUENCY_HISTORICAL_SAMPLING))

        ecoPushMonitoringSystem.import_historical_data(currentLoad=currentLoad, timestamp=timestamp)
    
    # analyse data for test date, each entry is read and passed to the
    # monitoring system with a delay to simulate real-time power signal sampling
    for entry in testData:
        currentLoad = entry["load"]
        timestamp = entry["timestamp"]

        # delay processing to simulate real-time sampling speed
        time.sleep(float(DELAY_IN_MEASUREMENT_FREQUENCY_REALTIME_SAMPLING))

        # analyse data
        ecoPushMonitoringSystem.analyse_data(currentLoad=currentLoad, timestamp=timestamp)  


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("id", help="Device ID")
    args = parser.parse_args()

    # default device id
    deviceId = 1234
    if args.id:
        deviceId = args.id

    # set the timeframe for analysis
    # full timeframe for REDD data start='2011-04-18 09:22:09-04:00', end='2011-05-24 15:57:02-04:00'
    # start = '2011-04-20'
    # end = '2011-05-24'

    startDate = '2011-04-21'
    endDate = '2011-04-26'

    # get building data
    building_number = 1
    building_data = utils.init(building_number, startDate, endDate)

    # output appliances in building_data
    # print(building_data)

    # applianceList = [("fridge", 1), ("dish washer", 1), ("microwave", 1)]
    applianceList = [("fridge", 1), ("light", 2)]
    # applianceList = [("fridge", 1)]

    # get appliance payload from building data
    payloadsForAnalysis = []
    for (appliance, id) in applianceList:
        payload = utils.get_payload_for_appliance(building_data, appliance, id)
        payloadsForAnalysis.append(payload)

    # analyse the payloads
    threadList = []
    for payload in payloadsForAnalysis:
        thread = Thread(
            target=analyse,
            args=(deviceId, payload),
        )
        thread.start()
        threadList.append(thread)

    for threadObject in threadList:
        thread.join()
        print("thread finished...exiting")


if __name__ == "__main__":
    main()
