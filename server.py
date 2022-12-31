from flask import Flask, Response, request, abort, redirect
from flask_cors import CORS
from flask_apscheduler import APScheduler # https://viniciuschiele.github.io/flask-apscheduler/rst/usage.html https://www.techcoil.com/blog/how-to-use-flask-apscheduler-in-your-python-3-flask-application-to-run-multiple-tasks-in-parallel-from-a-single-http-request/
from waitress import serve
import argparse
import importlib
import datetime
from pytz import timezone
import time
import random
import taskerJoinSMS

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
        force = "False"
    if hourisbetween(9, 21) or force == "True":
        print("Updating Prediction")
        result = gas_gasWizard.getPrediction()
        if result[0]:
            gas_jsonController.savePrediction("GasWizard",result[1][0],result[1][1],result[1][2])
        result = gas_Enpro680.getPrediction()
        if result[0]:
            gas_jsonController.savePrediction("EnPro",result[1][0],result[1][1],result[1][2])
        return("Prediction Updated")
    return("Prediction Not Updated")

@app.route('/gas')
def sendPrediction():
    print("Sending Prediction")
    # message = gas_gasWizard.getPrediction()
    data, tomorrow = gas_jsonController.checkPrediction(readData=True)
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
        return ("No prediction found for " + tomorrowDate.strftime("%b %d"))
    else:
        message = "Gas Prediction - " + tomorrowDate.strftime("%b %d") + "\n" + message
        return(message[:-1])

import os
from dotenv import load_dotenv
load_dotenv()
userKey = os.getenv('USER_KEY')

@app.route('/gas/user',methods = ['POST', 'GET', 'PUT', "DELETE"])
def manageUsers():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        reqJson = request.json
    else:
        print('Content-Type not supported!')
        return ("")

    try:
        if reqJson["Key"] != userKey:
            return("")
    except:
        return ("")

    if request.method == 'GET' or request.method == 'PUT':
        # print("Find Users")
        return(";".join(gas_jsonController.readUsers())) 
        
    elif request.method == 'POST':
        # print("Add User")
        try:
            number = reqJson["Number"]
        except:
            return ("")
        if gas_jsonController.addUser(number):
            taskerJoinSMS.sendSMS(tasker_join_api, tasker_join_device, number,
                                    "Success!\n"\
                                    "You will receive predictions daily.\n"\
                                    "Text CHECK for current prediction.\n"\
                                    "Text STOP to opt out.\n"\
                                    "Contact James for any questions."
                                    )
            taskerJoinSMS.sendSMS(tasker_join_api, tasker_join_device, number, sendPrediction())
            return ("Successful")
        else:
            taskerJoinSMS.sendSMS(tasker_join_api, tasker_join_device, number, "Something went wrong. Please contact James")
            return ("Failed")

    elif request.method == 'DELETE':
        # print("Remove User")
        try:
            number = reqJson["Number"]
        except:
            return ("")
        if gas_jsonController.deleteUser(number):
            taskerJoinSMS.sendSMS(tasker_join_api, tasker_join_device, number, "You have been removed. Bye!")
            return ("Successful")
        else:
            taskerJoinSMS.sendSMS(tasker_join_api, tasker_join_device, number, "Something went wrong. Please contact James")
            return ("Failed")
    else:
        print("Ignore")
        return("")

tasker_join_api = os.getenv('TASKER_JOIN_API')
tasker_join_device = os.getenv('TASKER_JOIN_DEVICE')

@scheduler.task('interval', id='send_gas_SMS', minutes=130, misfire_grace_time=900)
@app.route('/gas/sendSMS')
def sendSMS():

    try:
        force = request.args.get('force')
    except:
        force = "False"
    if hourisbetween(13, 21) or force == "True":
        message = sendPrediction()

        try:
            with open("gasPredictionMessage.txt","r") as f:
                contents = f.read()
        except:
            contents = ""
        
        if message != contents:
            with open("gasPredictionMessage.txt","w") as f:
                f.write(message)
            
            try:
                numbers = request.args.get('number')
            except:
                numbers = ""

            if numbers == "" or numbers == None:
                numbers = gas_jsonController.readUsers()
            else:
                numbers = {numbers:True}

            for number in numbers:
                taskerJoinSMS.sendSMS(tasker_join_api, tasker_join_device, number, message)
                time.sleep(5)
        else:
            return("")
    else:
        return("")
    return("Successful")

#---Flights in Radius---------------------------
flightsRadius = importlib.import_module("flights-in-radius.flights_in_radius")

@app.route('/flights')
def flightCheck():
    try:
        if (request.method == 'GET') and (None != request.args.get('GPS_lon')) and (None != request.args.get('GPS_lat')):
            GPS_lat = float(request.args.get('GPS_lat'))
            GPS_lon = float(request.args.get('GPS_lon'))
            return flightsRadius.main(GPS_lat,GPS_lon),200
        else:
            return("Please Provide GPS corrdinates as GPS_lon and GPS_lat.")
    except:
        abort(400)

# Default
@app.route('/')
def default_redirect():
    return redirect("https://jamesckluo.ca/")

@app.errorhandler(404)
def path_not_found(e):
    # your processing here
    print("Someone tried a weird route: " + str(request.path))
    return("")


scheduler.start()
if __name__ == '__main__':
    args = parser.parse_args()

    # print(sendPrediction())
    print("Starting Flask Server...")
    print("Listening on " + listenOn + ":" + str(args.port))
    serve(app,host = listenOn, port = int(args.port))
#    app.run(host=listenOn, port=port)
