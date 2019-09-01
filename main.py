import sys
import nilmtk
import utils
import urllib.request

# to update the model pass -u as an argument when running main.py
flag_update = False
if len(sys.argv) > 1 and sys.argv[1] == '-u':
    print('Model will be updated')
    flag_update = True

# get building data
building_data = utils.init(1)

# get mains readings from training building
mains = building_data.mains()

# download model from remote server
url = 'https://drive.google.com/uc?authuser=0&id=1xkpI7QQ4jZ1wQJauI0Kn65Q2OeUzL32l&export=download'

# don't use the default model URL, update the model and get new URL
if flag_update:
    # update model and get URL
    url = utils.update_model()

# download latest model to models/
print('Model URL', url)
model_path = 'models/latest_model.pickle'
urllib.request.urlretrieve(url, model_path)

# use model during disaggregation
predictions = utils.disaggregate(mains, model_path)

# get average number of seconds per load for the first entry in predictions.
# from testing predictions[0] is the fridge prediction
secondsPerLoadList = []
seconds = 0
preValue = 0
for currentValue in predictions[0]:
    if(currentValue > 10):
        # in load
        seconds = seconds + 1

    if(preValue > 10 and preValue > currentValue):
        secondsPerLoadList.append(seconds)

    if(currentValue < 10):
        # out of load
        seconds = 0

    preValue = currentValue

avgSecondsPerLoad = sum(secondsPerLoadList) / len(secondsPerLoadList)
print("Appliance load average seconds {:.2f}".format(avgSecondsPerLoad))

# find abnormalities in load by comparing the running time with the average running time
avgSecondsPerLoadLow = avgSecondsPerLoad * .80
avgSecondsPerLoadHigh = avgSecondsPerLoad * 1.20

reports = []

for secondsPerLoad in secondsPerLoadList:
    precentage = ((secondsPerLoad - avgSecondsPerLoad) /
                  avgSecondsPerLoad) * 100
    if precentage > 50 or precentage < -50:
        print("Load is +/-50% of average at {} seconds".format(secondsPerLoad))
        reportText = "abnormal load detected: average {:.2f} precentage {:.2f}% duration {:.2f}".format(
            avgSecondsPerLoad, precentage, secondsPerLoad)
        print(reportText)
        reports.append({"reportText": reportText})

# send report to user if abnormalities found
reportMessage = reports[0]["reportText"]  # report at index 0
utils.send_report(1234, reportMessage)
