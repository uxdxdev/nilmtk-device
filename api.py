import requests
import time


def current_milli_time(): return int(round(time.time() * 1000))


def send_report(reportText):
    now = current_milli_time()

    # send report to API
    r = requests.post("https://nilmtk-service.firebaseapp.com/api/report",
                      headers={'Content-Type': 'application/json'},
                      json={'deviceId': 1234, 'text': reportText, 'date': now})
    print(r.status_code, r.reason)
