#!/usr/bin/python3
import argparse
from datetime import datetime, timedelta
from locale import setlocale, LC_TIME
from time import sleep

from pyhafas import HafasClient
from pyhafas.profile import DBProfile
from requests import get, session

from DirectDestination import DirectDestination
from MultipleProposals import MultipleProposals
from Proposal import Proposal
from Station import Station

direct_journey_max_duration = 0
setlocale(LC_TIME, "fr_FR.UTF-8")
client = HafasClient(DBProfile())

s = session()
s.get("https://www.oui.sncf/")


def get_available_seats(departure_station: str, arrival_station: str, day: datetime, verbosity, quiet) -> [Proposal]:
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

    response = Proposal.get_next(departure_station, arrival_station, day.strftime('%Y-%m-%dT%H:%M:00'), verbosity,
                                 quiet)

    response_json = response.json()
    sleep(1)

    if response_json is not None:
        all_proposals = Proposal.filter_proposals(response_json['travelProposals'], direct_journey_max_duration)

        while response_json['nextPagination'] and response_json['nextPagination']['type'] != 'NEXT_DAY':
            print('Next page', page_count) if verbosity else None
            response = Proposal.get_next(departure_station, arrival_station, Proposal.get_last_timetable(response),
                                         verbosity, quiet)
            response_json = response.json()
            page_count += 1
            sleep(1)
            if response_json is not None and 'travelProposals' in response_json:
                all_proposals.extend(
                    Proposal.filter_proposals(response_json['travelProposals'], direct_journey_max_duration))
    return Proposal.remove_duplicates(all_proposals, verbosity) if all_proposals is not None else []


def total_search(departure_name: str, arrival_name: str, days: int, days_delta: int, direct_only: bool,
                 berth_only: bool, verbosity: bool, quiet: bool):
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
        direct = get_available_seats(departure_code, arrival_code, day, verbosity, quiet)
        display_proposals(direct)

        if not direct_only:
            intermediate_stations = departure_direct_destinations.get_common_stations(
                arrival_direct_destinations)  # + [PARIS]

            for intermediate_station in intermediate_stations:
                # check for segments between station located in France only
                if intermediate_station['station'].is_in_france():
                    # farther_station = Station.get_farther_station(departure_direct_destinations, arrival_direct_destinations, intermediate_station)

                    # To optimize the search, we first search for the longest segment (most demanded than the shortest and
                    # potentially limiting factor) Exemple : For Beziers-Paris (~4h) via Nimes, we first search for the
                    # journey from Nimes to Paris (~3h), then for the journey from Beziers-Nimes (~1h), because longer
                    # segment is rare
                    print('Via', intermediate_station['station'].name) if not quiet else None
                    first_segment = get_available_seats(departure_code,
                                                        intermediate_station['station'].name_to_code()[0],
                                                        day, verbosity=verbosity, quiet=quiet)
                    if first_segment:  # we try to find second segment only if first segment is not empty
                        if verbosity:
                            print('First segments found :')
                            display_proposals(first_segment)
                        second_segment = get_available_seats(intermediate_station['station'].name_to_code()[0],
                                                             arrival_code,
                                                             day, verbosity=verbosity, quiet=quiet)

                        if second_segment:
                            if verbosity:
                                print('Second segments found :')
                                display_proposals(second_segment)

                            for first_proposal in first_segment:
                                for second_proposal in second_segment:
                                    if second_proposal.departure_date > first_proposal.arrival_date:
                                        MultipleProposals(first_proposal, second_proposal).display(berth_only=berth_only)


def display_proposals(proposals: list[Proposal] or None, berth_only: bool = False):
    if proposals:
        for proposal in proposals:
            if berth_only and proposal.transporter == 'INTERCITES DE NUIT':
                if 'berths' in proposal.remaining_seats:
                    proposal.print()
            else:
                proposal.print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stations", metavar="station", help="Station names", nargs=2)
    parser.add_argument("-t", "--timedelta", help="How many days from today", type=int, default=1)
    parser.add_argument("-p", "--period", help="Number of days to search", type=int, default=1)
    parser.add_argument("-d", "--direct-only", help="Print direct proposals only", action="store_true")
    parser.add_argument("-b", "--berth-only", help="Print berth only for Intercites de Nuit proposals",
                        action="store_true")
    parser.add_argument("-q", "--quiet", help="Only show results", action="store_true")
    parser.add_argument("-v", "--verbosity", action="store_true", help="Verbosity")
    args = parser.parse_args()

    total_search(args.stations[0],
                 args.stations[1],
                 args.period,
                 args.timedelta,
                 direct_only=args.direct_only,
                 berth_only=args.berth_only,
                 verbosity=args.verbosity, quiet=args.quiet
                 )


if __name__ == '__main__':
    try:
        main()

    except KeyboardInterrupt:  # Catch CTRL-C
        print('Interrupted')
        exit(1)
