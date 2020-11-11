#!/usr/bin/env python3
from __future__ import print_function
import calendar
import datetime
import dateutil.parser
import logging
import os.path
import pandas as pd
import pickle
import sys
from argparse import ArgumentParser
from dateutil import tz
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dateutil.relativedelta import *
from dateutil.parser import *

################################################################################
# Logging stuff (need to do this to not interfere with Google's logging)
################################################################################
logger = logging.getLogger('gcal')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

################################################################################
# Globals
################################################################################

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

################################################################################
# Main script
################################################################################
def get_parser():
    """ Takes care of script argument parsing. """
    today = datetime.datetime.now()
    today_str = "{}-{}-{}".format(today.year, today.month, today.day)
    parser = ArgumentParser(description='Script used to update comments in Jira')

    parser.add_argument('-s', '--start', required=False, action="store", \
            default=today_str, \
            help='Start date on format YYYY-MM-DD')

    parser.add_argument('-e', '--end', required=False, action="store", \
            default=today_str, \
            help='End date on format YYYY-MM-DD')

    parser.add_argument('-ne', '--no-earlier', required=False, action="store", \
            default=8, \
            help='Hide slots earlier than <hour> (08, 10, 21 etc)')

    parser.add_argument('-nl', '--no-later', required=False, action="store", \
            default=17, \
            help='Hide slots after <hour> (08, 10, 21 etc)')

    parser.add_argument('-p', '--people', required=False, action="store", \
            default="joakim.bech", \
            help='Comma separated list of people to invite')

    parser.add_argument('-u', '--utc', required=False, action="store", \
            default="+1", \
            help='Your own UTCs (default is +1)')

    parser.add_argument('-eu', '--extra-utc', required=False, action="store", \
            default="0", \
            help='Comma separated list of extra UTCs to show')

    return parser


def get_credentials():
    hour = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


def create_service():
    creds = get_credentials()
    return build('calendar', 'v3', credentials=creds)


def send_query(service, query):
    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    logger.debug("Sending query to Google API")
    result = service.freebusy().query(body=query).execute()
    return result


def parse_result(result, timezone):
    global freelist

    persons = result.get('calendars', [])
    for p in persons:
        logger.debug(p)
        for b in persons[p]["busy"]:
            start = dateutil.parser.parse(b["start"])
            logger.debug(start)
            day_start = start.day
            month_start = start.month
            h_start = start.hour
            m_start = start.minute

            end = dateutil.parser.parse(b["end"])
            day_end = end.day
            month_end = end.month
            h_end = end.hour
            m_end = end.minute

            delta = end - start
            nbrof_halfhours = round(delta.total_seconds() / 1800);

            # 2020-11-25 21:00
            offset = 0
            logger.debug("Busy: {}/{}: {:02d}.{:02d}-{:02d}.{:02d} ({})".format(day_start, month_start, h_start, m_start, h_end, m_end, timezone))
            for i in range(0, nbrof_halfhours):
                current = start + relativedelta(minutes = offset)
                # Strip away the ":00+00:00"
                tmp = str(current)[:-9]
                logger.debug("Removing: {}".format(tmp))
                try:
                    freelist.remove(tmp)
                except ValueError:
                    pass
                finally:
                    offset += 30


def main():
    global freelist

    args = get_parser().parse_args()

    logger.debug(args)

    # This is UTC ...
    sign = "+"
    timezone = "1"

    if args.utc[0] == "-":
        sign = "-"
        timezone = args.utc[1:]
    elif args.utc[0] == "+":
        sign = "+"
        timezone = args.utc[1:]
    elif len(args.utc) == 1 and args.utc.isdigit():
        timezone = args.utc

    service = create_service()

    start_date = "{}T08:00:00{}{:02d}00".format(args.start, sign, int(timezone))
    end_date   = "{}T21:00:00{}{:02d}00".format(args.end, sign, int(timezone))


    logger.debug(start_date)
    logger.debug(end_date)

    ppl = args.people.split(",")
    ppl = list(map(lambda x: "{}@linaro.org".format(x), ppl))
    logger.debug(ppl)
    invitees = []
    for p in ppl:
        invitees.append({ "id": p })

    logger.debug(invitees)

    query = { "timeMin": start_date,
              "timeMax": end_date,
              "timeZone": "UTC+{}".format(timezone),
              "items": invitees
              }

    result = send_query(service, query)

    freelist = (pd.DataFrame(columns=['NULL'],
                index=pd.date_range(start_date, end_date, freq='30T'))
                .between_time('08:00','21:00')
                .index.strftime('%Y-%m-%d %H:%M')
                .tolist())

    for l in freelist:
        logger.debug(l)

    parse_result(result, timezone)

    for l in freelist:
        # Hard coded at this position
        hour = int(l[11:13])
        if hour >= int(args.no_earlier) and hour < int(args.no_later):
            print("{} UTC+{} ({})".format(l, timezone, calendar.day_name[parse(l).weekday()]))


if __name__ == '__main__':
    main()
