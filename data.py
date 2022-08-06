import requests
import json

def stash_data(date, local=False):
    out_url = "/tmp/timeseries.csv"
    if local:
        return out_url

    url = 'https://gi8st4xbib.execute-api.us-east-2.amazonaws.com/request'
    myobj = {
        "operation": "get_transaction_timeseries",
        "args": {
            "file_info": {
                "day": date,
                "bucket_name": "scifi-trades",
                "file_name": date + "/trades/positions.json"
            }
        }
    }

    response = requests.post(url, json = myobj)
    response_text = json.loads(response.text)
    if (response_text.get("errorMessage")):
        return  "Error", response_text["errorMessage"]
    elif not response.status_code == 200:
        return "Error", response.text
    else:
        out = open(out_url,"w")
        out.writelines(response_text["body"]["results"])
        out.close()
        return "Success", out_url
