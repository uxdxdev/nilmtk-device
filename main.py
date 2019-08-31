import sys
sys.path.append('./train')
import model
import nilmtk
from nilmtk import DataSet
import disaggregate
from api import send_report
import urllib.request

# to update the model pass -u as an argument when running main.py
flag_update = False
if len(sys.argv) > 1 and sys.argv[1] == '-u':
    print('Model will be updated')
    flag_update = True

# simulate receiving mains data from remote monitoring device
# by loading dataset and restrict to 1 week
print('Importing dataset...')
data = DataSet('data/redd.h5')
print('Importing dataset done.', len(data.buildings), 'buildings')

building = 1
data.set_window(start='2011-04-20', end='2011-04-27')
training_building = data.buildings[building].elec

# get mains readings from training building
mains = training_building.mains()

# download model from remote server
url = 'https://drive.google.com/uc?authuser=0&id=1xkpI7QQ4jZ1wQJauI0Kn65Q2OeUzL32l&export=download'

if flag_update:
    url = model.update_model()

print('Model URL', url)
model_path = 'models/latest_model.pickle'
urllib.request.urlretrieve(url, model_path)

# use model during disaggregation
predictions = disaggregate.disaggregate(mains, model_path)

# Unknown submeter - avg seconds per load
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

# average number of seconds per load
avgSecondsPerLoad = sum(secondsPerLoadList) / len(secondsPerLoadList)

print("Appliance load average seconds {:.2f}".format(avgSecondsPerLoad))

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

send_report(reports[0]["reportText"])
