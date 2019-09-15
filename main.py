import os
import argparse
import sys
import utils
import urllib.request
from threading import Thread
from dotenv import load_dotenv
load_dotenv()


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("id", help="Device ID")
    parser.add_argument(
        "--update", help="Update the disaggregation model", action="store_true")
    args = parser.parse_args()

    flag_update = False
    if args.update:
        flag_update = True

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

    # train algorithm on building number;
    traning_building_number = 1
    ground_truth_data = utils.init(traning_building_number, start, end)

    # apply disaggregation to building number;
    application_building_number = 1
    building_data = utils.init(application_building_number, start, end)

    # get mains readings from training building
    mains = building_data.mains()

    # download model from remote server
    url = 'https://drive.google.com/uc?authuser=0&id=1xkpI7QQ4jZ1wQJauI0Kn65Q2OeUzL32l&export=download'

    # don't use the default model URL, update the model and get new URL
    if flag_update:
        # update model and get URL
        url = utils.update_model(ground_truth_data)

    # download latest model to models/
    print('Model URL', url)
    model_path = 'models/latest_model.pickle'
    urllib.request.urlretrieve(url, model_path)

    # use model during disaggregation
    predictions = utils.disaggregate(mains, model_path)

    print(ground_truth_data.submeters())
    print(utils.match_results(ground_truth_data.submeters(), predictions))

    applianceList = [0, 1, 2]
    threadList = []

    def get_payload_and_analyse(building_data, appliance):
        # get payload for unknown appliance
        appliance_payload = utils.get_payload_for_unknown_appliance(
            building_data, appliance)

        DELAY_IN_MEASUREMENT_FREQUENCY = os.getenv(
            "DELAY_IN_MEASUREMENT_FREQUENCY")

        utils.analyse_payload(deviceId,
                              appliance_payload, DELAY_IN_MEASUREMENT_FREQUENCY)

    for appliance in applianceList:
        thread = Thread(
            target=get_payload_and_analyse,
            args=(predictions, appliance),
        )
        thread.start()
        threadList.append(thread)

    for threadObject in threadList:
        thread.join()
        print("thread finished...exiting")


if __name__ == "__main__":
    main()
