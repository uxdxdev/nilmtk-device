import argparse
import os
import utils
from threading import Thread
from dotenv import load_dotenv
load_dotenv()


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
    # end = '2011-04-24'

    start = '2011-04-25'
    end = '2011-04-26'

    # get building data
    building_number = 1
    building_data = utils.init(building_number, start, end)

    # output appliances in building_data
    print(building_data)

    applianceList = ["fridge", "dish washer", "microwave", "light"]
    threadList = []

    def get_payload_and_analyse(building_data, appliance):
        # get payload for known appliance
        appliance_payload = utils.get_payload_for_appliance(
            building_data, appliance)

        DELAY_IN_MEASUREMENT_FREQUENCY = os.getenv(
            "DELAY_IN_MEASUREMENT_FREQUENCY")

        utils.analyse_payload(deviceId,
                              appliance_payload, DELAY_IN_MEASUREMENT_FREQUENCY)

    for appliance in applianceList:
        thread = Thread(
            target=get_payload_and_analyse,
            args=(building_data, appliance),
        )
        thread.start()
        threadList.append(thread)

    for threadObject in threadList:
        thread.join()
        print("thread finished...exiting")


if __name__ == "__main__":
    main()
