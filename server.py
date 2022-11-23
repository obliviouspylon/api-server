from flask import Flask, Response, request, abort
from flask_cors import CORS
from flask_apscheduler import APScheduler # https://viniciuschiele.github.io/flask-apscheduler/rst/usage.html https://www.techcoil.com/blog/how-to-use-flask-apscheduler-in-your-python-3-flask-application-to-run-multiple-tasks-in-parallel-from-a-single-http-request/
from waitress import serve
import argparse
import importlib
import datetime
from pytz import timezone

parser = argparse.ArgumentParser()
parser.add_argument('-p', default=9000, dest='port',
                    help = 'Change Flask Port. Default 9000',)

app = Flask(__name__)
CORS(app)
scheduler = APScheduler()
scheduler.api_enabled = True
scheduler.init_app(app)

# config
listenOn = "0.0.0.0"

#---Gas Price Prediction---------------------------
gas_gasWizard = importlib.import_module("gas-price-notification.gasWizard")
gas_jsonController = importlib.import_module("gas-price-notification.jsonController")
gas_Enpro680 = importlib.import_module("gas-price-notification.Enpro680")


def hourisbetween(start, end):
    now = datetime.datetime.now(timezone("EST")).hour
    if (now >= start) and (now <= end):
        return True
    else:
        return False

@scheduler.task('interval', id='do_test', minutes=60, misfire_grace_time=900)
# @scheduler.task('interval', id='do_test', seconds=5, misfire_grace_time=900)
@app.route('/gas/update')
def getGasPrediction():
    # print(datetime.datetime.now(timezone("EST")))
    try:
        force = request.args.get('force')
    except:
        force = "True"
    if hourisbetween(9, 21) or force == "True":
        print("Updating Prediction")
        result = gas_gasWizard.getPrediction()
        if result[0]:
            gas_jsonController.saveJson("GasWizard",result[1][0],result[1][1],result[1][2])
        result = gas_Enpro680.getPrediction()
        if result[0]:
            gas_jsonController.saveJson("EnPro",result[1][0],result[1][1],result[1][2])
        return("Prediction Updated")
    return("Prediction Not Updated")

@app.route('/gas')
def sendPrediction():
    print("Sending Prediction")
    # message = gas_gasWizard.getPrediction()
    data, tomorrow = gas_jsonController.checkJson(readData=True)
    tomorrowDate = datetime.datetime.strptime(tomorrow, "%Y%m%d")
    message = ""

    for site in data[tomorrow]:
        direction = data[tomorrow][site]["direction"]
        amount = str(data[tomorrow][site]["amount"])
        price = str(data[tomorrow][site]["price"])
        if direction == "STAYS":
            message = message + site + ": " + direction + " at " + price + "¢/L\n"
        else:
            message = message + site + ": " + direction + " by " + amount + " to " + price + "¢/L\n"

    if message == "":
        return Response("No prediction found for " + tomorrowDate.strftime("%b %d"), status=201)
    else:
        message = "Gas Prediction - " + tomorrowDate.strftime("%b %d") + "\n" + message
        return(message[:-1])

#---Flights in Radius---------------------------
flightsRadius = importlib.import_module("flights-in-radius.flights_in_radius")

@app.route('/flights')
def flightCheck():
  if (request.method == 'GET') and (None != request.args.get('GPS_lon')) and (None != request.args.get('GPS_lat')):
    GPS_lat = float(request.args.get('GPS_lat'))
    GPS_lon = float(request.args.get('GPS_lon'))
    return flightsRadius.main(GPS_lat,GPS_lon),200
  else:
    abort(400)


scheduler.start()
if __name__ == '__main__':
    args = parser.parse_args()

    # print(sendPrediction())
    print("Starting Flask Server...")
    print("Listening on " + listenOn + ":" + str(args.port))
    serve(app,host = listenOn, port = int(args.port))
#    app.run(host=listenOn, port=port)
