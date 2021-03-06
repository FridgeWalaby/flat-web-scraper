import requests
import json
import os
import csv

from bs4 import BeautifulSoup
from datetime import datetime
from decouple import config
from lxml import etree
import re

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

        if float(rooms) < 3 or float(rooms) >= 4:
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
                + " Zi.\n"
                + offer[5]
                + " CHF\n"
                + offer[6]
                + "\n"
                + offer[7]
                + "\n"
                + offer[8]
                + "<https://www.vermietungen.stadt-zuerich.ch/publication/apartment/|E-Vermietung>"
            )

            send_slack_message(message)
            write_offer_to_csv(offer)


with requests.Session() as session:
    url = "https://www.homegate.ch/mieten/wohnung/trefferliste?ac=3&loc=Albisrieden%20%5BQuartier%5D%2CAltstetten%20%5BQuartier%5D%2CWipkingen%20%5BQuartier%5D%2CWiedikon%20%5BQuartier%5D%2CZ%C3%BCrich%20Kreis%201%20%5BStadtteil%5D%2CZ%C3%BCrich%20Kreis%203%20%5BStadtteil%5D%2CZ%C3%BCrich%20Kreis%204%20%5BStadtteil%5D%2CZ%C3%BCrich%20Kreis%205%20%5BStadtteil%5D%2CZ%C3%BCrich%20Kreis%206%20%5BStadtteil%5D%2CH%C3%B6ngg%20%5BQuartier%5D&ah=1705"
    res0 = session.get(url)

    soup = BeautifulSoup(res0.content, "html.parser")

    items = soup.find_all(attrs={"data-test": "result-list-item"})

    for item in items:
        item_data = item.find_all(attrs={"class": re.compile("^ListItem_data.*")})
        top_item_data = item.find_all(
            attrs={"class": re.compile("^ListItemTopPremium_data.*")}
        )

        if len(item_data) == 0 and len(top_item_data) == 0:
            print("not")
            continue

        if len(item_data) == 1:
            address = item_data[0].find_all("p")[1].get_text()

        if len(top_item_data) == 1:
            address = top_item_data[0].find_all("p")[1].get_text()

        room_data = item.find_all(
            attrs={"class": re.compile("^ListItemRoomNumber_value.*")}
        )
        rooms = room_data[0].get_text(" ")

        text = item.get_text("|")
        data = text.split("|")
        price = data[3]

        link = "https://www.homegate.ch" + item.get("href")

        if not csv_file_includes_offer(address, price):

            timestamp = get_date_string()

            offer = [
                timestamp,
                address,
                rooms,
                "",
                "",
                price,
                "",
                "",
                link,
            ]

            message = (
                "----Homegate-----"
                + "\n"
                + offer[0]
                + "\n"
                + "*"
                + offer[1]
                + "*"
                + "\n"
                + offer[2]
                + "\n"
                + offer[5]
                + " CHF\n"
                + "<"
                + offer[8]
                + "|Homegate Link>"
            )

            send_slack_message(message)
            write_offer_to_csv(offer)
