#!/usr/bin/env python
from bs4 import BeautifulSoup
import mechanize
import requests
import json
from datetime import datetime
import os
import yaml

def scrape_studies(username, password):
    # Browser
    br = mechanize.Browser()

    # Settings
    br.set_handle_robots(False)
    br.addheaders = [('User-agent','Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    # Open page and select login form
    br.open("https://sbe.sona-systems.com/")
    br.select_form(name="aspnetForm")

    # Fill out and submit form
    br["ctl00$ContentPlaceHolder1$userid"] = username
    br["ctl00$ContentPlaceHolder1$pw"] = password
    br.submit()

    # Open studies page
    studies_html = br.open("https://sbe.sona-systems.com/all_exp_participant.aspx")

    # Soupify
    soup = BeautifulSoup(studies_html)

    # Get the studies rows
    studies_rows = soup.select("table tbody tr")

    # Parse studies
    new_studies = []
    for row in studies_rows:
        columns = row.find_all('td')
        title = columns[1]
        new_studies.append(title.get_text(strip=True))

    return new_studies


def send_slack_msg(msg, url):
    payload = {"text": msg, "username": "Sona Bot"}
    r = requests.post(url, data=json.dumps(payload))
    return r


def main():
    try:

        with open('config.yaml', 'r') as f:
            config = yaml.load(f)

        # Read in existing studies
        existing_studies = [line.strip() for line in open(str(os.getcwd()) + '/studies.txt')]

        # Scrape available studies
        available_studies = scrape_studies(config["username"], config["password"])

        # Over-write existing studies with available studies
        with open(str(os.getcwd()) + '/studies.txt', 'w') as f:
            f.write("\n".join(available_studies).encode('ascii', 'ignore'))

        # See what's new
        new_studies = []
        for s in available_studies:
            if s not in existing_studies:
                new_studies.append(s)

        # Send a slack msg
        if new_studies:
            send_slack_msg("\n".join(new_studies), config["slack_url"])

        # Log it
        with open(str(os.getcwd()) + '/log.txt', 'a') as f:
            f.write(str(datetime.now()) + ",success\n")

    except Exception, e:
        # Log it
        with open(str(os.getcwd()) + '/err.txt', 'a') as f:
            f.write(str(datetime.now()) + "," + str(e) + "\n")


if __name__ == "__main__":
    main()
