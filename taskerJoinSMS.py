import requests
from urllib.parse import quote


def sendSMS(taskerJoinAPI, device,sms_number, sms_message):

    taskerJoinAPI = quote(taskerJoinAPI)
    device = quote(device)
    sms_number = quote(sms_number)
    sms_message = quote(sms_message)
    url = f"https://joinjoaomgcd.appspot.com/_ah/api/messaging/v1/sendPush?apikey={taskerJoinAPI}&deviceNames={device}&smsnumber={sms_number}&smstext={sms_message}"

    response = requests.post(
        url,
        # headers=headers
    )

    if "errorMessage" in response:
        return False
    else:
        return True
