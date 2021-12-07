#!/usr/bin/python3
import argparse
from os.path import join, dirname
from dotenv import load_dotenv

from os import environ as env
from sys import argv
from time import sleep
from json import dumps as json_dumps
from locale import setlocale, LC_TIME
from requests import get, session

from datetime import datetime, timedelta
from operator import itemgetter

from pyhafas import HafasClient
from pyhafas.profile import DBProfile

from BColors import BColors
from DirectDestination import DirectDestination
from MultipleProposals import MultipleProposals
from Station import Station
from Proposal import Proposal

DISPLAY_NON_TGVMAX = False
DISPLAY_UNAVAILABLE = False
direct_journey_max_duration = 0
setlocale(LC_TIME, "fr_FR.UTF-8")
client = HafasClient(DBProfile())

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
OUISNCF_COOKIE = env.get("OUISNCF_COOKIE")
TGVMAX_CARD_NUMBER = env.get("TGVMAX_CARD_NUMBER")
BIRTH_DATE = env.get("BIRTH_DATE")

s = session()
s.get("https://www.oui.sncf/")


def get_next_proposals(departure_station, arrival_station, departure_date, verbosity, quiet):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.oui.sncf/proposition/outward/train?wishId=95edb29e-9529-4e54-9645-01d0040da16d',
        'content-type': 'application/json',
        'x-client-app-id': 'VSD',
        'x-client-channel': 'web',
        'x-market-locale': 'fr_FR',
        'x-vsd-locale': 'fr_FR',
        'X-INSTANA-L': '1,correlationType=web;correlationId=afc550728eb5e772',
        'Origin': 'https://www.oui.sncf',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'TE': 'trailers',
        'Cookie': OUISNCF_COOKIE
    }
    data = {'context': {'features': [], 'paginationContext': {'travelSchedule': {'departureDate': departure_date}}},
            'wish': {'id': '8938068f-7816-4ee3-8176-1c35e6a81245',
                     'mainJourney': {'origin': {'codes': {'RESARAIL': {'code': departure_station}}},
                                     'destination': {'codes': {'RESARAIL': {'code': arrival_station}}}, 'via': None},
                     'directTravel': True,
                     'schedule': {'outward': departure_date, 'outwardType': 'DEPARTURE_FROM', 'inward': None,
                                  'inwardType': 'DEPARTURE_FROM'}, 'travelClass': 'SECOND', 'passengers': [
                    {'id': '0', 'typology': 'YOUNG', 'customerId': '', 'firstname': '', 'lastname': '',
                     'dateOfBirth': BIRTH_DATE, 'age': 21,
                     'discountCards': [{'code': 'HAPPY_CARD', 'number': TGVMAX_CARD_NUMBER, 'dateOfBirth': BIRTH_DATE}],
                     'promoCode': '', 'bicycle': None}], 'checkBestPrices': False, 'salesMarket': 'fr-FR',
                     'channel': 'web', 'pets': [], 'context': {'sumoForTrain': {'eligible': True}}}}

    response = s.post('https://www.oui.sncf/api/vsd/travels/outward/train/next', headers=headers, data=json_dumps(data))
    if response.status_code != 200:
        print(BColors.FAIL + 'Error: HTTP', str(response.status_code) + BColors.ENDC)
        exit('Error in proposal request')
    return response


def get_available_seats_next_x_days(departure_station: str, arrival_station: str, day: datetime, verbosity, quiet) -> [
    Proposal]:
    """
    Returns stations that are searched with the provided term

    The further forward the station is in the list, the higher the similarity to the search term.


    :param departure_station: station of departure
    :param arrival_station: station of arrival
    :param day: date of departure
    :param quiet:
    :param verbosity:

    :return: List of journey 'Proposal' objects
    """
    page_count = 0
    all_proposals = []

    response = get_next_proposals(departure_station, arrival_station, day.strftime('%Y-%m-%dT%H:%M:00'), verbosity,
                                  quiet)

    response_json = response.json()
    sleep(1)

    if response_json is not None:
        all_proposals = Proposal.filter_proposals(response_json['travelProposals'], direct_journey_max_duration)

        while response_json['nextPagination'] and response_json['nextPagination']['type'] != 'NEXT_DAY':
            print('Next page', page_count) if verbosity else None
            response = get_next_proposals(departure_station, arrival_station, Proposal.get_last_timetable(response),
                                          verbosity, quiet)
            response_json = response.json()
            page_count += 1
            sleep(1)
            if response_json is not None and 'travelProposals' in response_json:
                all_proposals.extend(
                    Proposal.filter_proposals(response_json['travelProposals'], direct_journey_max_duration))
    return Proposal.remove_duplicates(all_proposals, verbosity) if all_proposals is not None else []


def get_common_stations(departure_direct_destinations: DirectDestination,
                        arrival_direct_destinations: DirectDestination) -> [Station]:
    print("Let's try to split the journey from", departure_direct_destinations.station.name, 'to',
          arrival_direct_destinations.station.name, end=' : ')

    destinations_keys = set(departure_direct_destinations.destinations.keys()).intersection(
        arrival_direct_destinations.destinations.keys())
    destinations = list(itemgetter(*destinations_keys)(
        departure_direct_destinations.destinations | arrival_direct_destinations.destinations))

    print(len(destinations), 'intermediate stations available')

    return destinations


def total_search(departure_name: str, arrival_name: str, days: int, days_delta: int, verbosity: bool, quiet: bool):
    date = datetime.now().replace(hour=0, minute=0) + timedelta(days=days_delta)

    departure_code, formal_departure_name = Station.name_to_code(Station(departure_name))
    arrival_code, formal_arrival_name = Station.name_to_code(Station(arrival_name))

    departure = Station(departure_name, code=departure_code, formal_name=formal_departure_name,
                        identifier=client.locations(departure_name)[0].__dict__['id'])
    arrival = Station(arrival_name, code=arrival_code, formal_name=formal_arrival_name,
                      identifier=client.locations(arrival_name)[0].__dict__['id'])

    arrival_direct_destinations = DirectDestination(arrival, get('https://api.direkt.bahn.guru/' + arrival.id))
    departure_direct_destinations = DirectDestination(departure,
                                                      get('https://api.direkt.bahn.guru/' + departure.id))

    for day_counter in range(days):
        day = date + timedelta(days=day_counter)
        print(day.strftime("%c"))

        print('Direct journey from', formal_departure_name, 'to', formal_arrival_name)
        direct = get_available_seats_next_x_days(departure_code, arrival_code, day, verbosity, quiet)
        if direct:
            for proposal in direct:
                proposal.print()

        intermediate_stations = get_common_stations(departure_direct_destinations,
                                                    arrival_direct_destinations)  # + [PARIS]

        for intermediate_station in intermediate_stations:
            if intermediate_station['station'].is_in_france():  # check for segments between station located in France only
                # farther_station = Station.get_farther_station(departure_direct_destinations, arrival_direct_destinations, intermediate_station)

                # To optimize the search, we first search for the longest segment (most demanded than the shortest and
                # potentially limiting factor) Exemple : For Beziers-Paris (~4h) via Nimes, we first search for the
                # journey from Nimes to Paris (~3h), then for the journey from Beziers-Nimes (~1h), because longer
                # segment is rare
                print('Via', intermediate_station['station'].name) if not quiet else None
                first_segment = get_available_seats_next_x_days(departure_code,
                                                                intermediate_station['station'].name_to_code()[0],
                                                                day, verbosity=verbosity, quiet=quiet)
                if first_segment:  # we try to find second segment only if first segment is not empty
                    if verbosity:
                        print('First segments found :')
                        for proposal in first_segment:
                            proposal.print()
                    second_segment = get_available_seats_next_x_days(intermediate_station['station'].name_to_code()[0],
                                                                     arrival_code,
                                                                     day, verbosity=verbosity, quiet=quiet)

                    if second_segment:
                        if verbosity:
                            print('Second segments found :')
                            for proposal in second_segment:
                                proposal.print()
                        for first_proposal in first_segment:
                            for second_proposal in second_segment:
                                if second_proposal.departure_date > first_proposal.arrival_date:
                                    journey = MultipleProposals(first_proposal, second_proposal)
                                    journey.display()


def _help():
    args = argv
    print('Usage: python3', args[0], 'departure_station arrival_station days_delta')


def main():
    args = argv
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("stations", metavar="station", help="Station names", nargs=2)
        parser.add_argument("-t", "--timedelta", help="Number of days to search", type=int, default=1)
        parser.add_argument("-q", "--quiet", help="Only show results", action="store_true")
        parser.add_argument("-v", "--verbosity", action="store_true", help="Verbosity")
        args = parser.parse_args()


    except ValueError:
        _help()
        exit(1)

    total_search(args.stations[0], args.stations[1], 1, args.timedelta, verbosity=args.verbosity, quiet=args.quiet)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        exit(1)