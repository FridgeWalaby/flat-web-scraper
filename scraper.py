import requests
import json
import os
import csv

from bs4 import BeautifulSoup
from datetime import datetime
from decouple import config


USERID = config("USERID")
PASSWORD = config("PASSWORD")
SLACK_LINK = config("SLACK_LINK")


def get_date_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def csv_file_includes_offer(streetname, price):
    with open("offers.csv", newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        duplicate = False
        for row in reader:
            if streetname in row and str(price) in row:
                duplicate = True
        return duplicate


def write_offer_to_csv(offer):
    with open("offers.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=",", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(offer)


def send_slack_message(text):
    wekbook_url = SLACK_LINK

    data = {
        "text": text,
        "username": "BRUDI",
        "icon_emoji": ":robot_face:",
    }

    response = requests.post(
        wekbook_url, data=json.dumps(data), headers={"Content-Type": "application/json"}
    )


with requests.Session() as session:
    url = "https://www.stadt-zuerich.ch/login/intertl/auth?RequestedPage=%2fapp%2fmkfewww%2fweb%2fauth%2f"
    res0 = session.get(url)

    soup = BeautifulSoup(res0.content, "html.parser")
    login_data = {"userid": USERID, "password": PASSWORD}
    login_data["currentRequestedPage"] = soup.find(
        "input", attrs={"name": "currentRequestedPage"}
    )["value"]

    login_url = "https://www.stadt-zuerich.ch/login/intertl/auth"
    res1 = session.post(url, data=login_data)

    offers_url = "https://www.vermietungen.stadt-zuerich.ch/publication/apartment/"
    res2 = session.get(offers_url)

    soup1 = BeautifulSoup(res2.content, "html.parser")

    table = soup1.find("tbody")
    table_body = BeautifulSoup(str(table), "lxml").find("tbody")

    for tr in table_body.find_all("tr"):
        data = tr.find_all("td")

        timestamp = get_date_string()
        address = data[1].text.strip()
        rooms = data[2].text.strip()
        floor = data[3].text.strip()
        sq_meters = data[4].text.strip()
        price = data[5].text.strip()
        intent = data[6].text.strip()
        district = data[7].text.strip()
        move_date = data[8].text.strip()

        if float(rooms) < 3:
            continue

        offer = [
            timestamp,
            address,
            rooms,
            floor,
            sq_meters,
            price,
            intent,
            district,
            move_date,
        ]

        if not csv_file_includes_offer(address, price):
            message = (
                "-----------------"
                + "\n"
                + offer[0]
                + "\n"
                + "*"
                + offer[1]
                + "*"
                + "\n"
                + offer[2]
                + "Zi.\n"
                + offer[5]
                + " CHF\n"
                + offer[6]
                + "\n"
                + offer[7]
                + "\n"
                + offer[8]
                + " Einzug\n"
            )

            send_slack_message(message)
            write_offer_to_csv(offer)
