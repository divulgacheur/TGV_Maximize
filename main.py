#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

from argparse import ArgumentParser
from datetime import datetime, timedelta
from locale import setlocale, LC_TIME
from time import sleep
from sys import exit as sys_exit

from argcomplete import autocomplete
from pyhafas import HafasClient
from pyhafas.profile import DBProfile
from requests import get, session

from bcolors import BColors
from direct_destination import DirectDestination
from multiple_proposals import MultipleProposals
from options import SearchOptions
from proposal import Proposal
from station import Station, PARIS

setlocale(LC_TIME, "fr_FR.UTF-8")
client = HafasClient(DBProfile())

s = session()
s.get("https://www.oui.sncf/")


def get_available_seats(dep_station: str, arr_station: str, day: datetime,
                        opts: SearchOptions) -> [Proposal]:
    """
    Returns train proposals for a given day
    :param dep_station: station of departure
    :param arr_station: station of arrival
    :param day: date of departure
    :param opts:
    :return: List of journey 'Proposal' objects
    """
    page_count = 1
    all_proposals = []

    response = Proposal.get_next(dep_station, arr_station, day.strftime('%Y-%m-%dT%H:%M:00'), opts)

    response_json = response.json()
    sleep(1)

    if response_json is not None:
        all_proposals = Proposal.filter(response_json['travelProposals'], opts.max_duration)

        while response_json['nextPagination'] and response_json['nextPagination']['type'] != 'NEXT_DAY':
            if opts.verbosity:
                print(f'\t Next page - {page_count}')
            response = Proposal.get_next(dep_station,
                                         arr_station,
                                         Proposal.get_last_timetable(response),
                                         opts.verbosity)
            response_json = response.json()
            page_count += 1
            sleep(1)
            if response_json is not None and 'travelProposals' in response_json:
                all_proposals.extend(
                    Proposal.filter(response_json['travelProposals'], opts.max_duration))
    return Proposal.remove_duplicates(all_proposals, opts.verbosity) if all_proposals else []


def get_indirect_proposals(departure, arrival, departure_direct_destinations, arrival_direct_destinations, day, opts):
    print(f"Let's try to split the journey from {departure.name} to {arrival.name}", end=' : ')
    if not opts.via:
        intermediate_stations = departure_direct_destinations.get_common_stations(
            arrival_direct_destinations)   + [PARIS]
    else:
        via_code, formal_via_name = Station.name_to_code(Station(opts.via))
        intermediate_stations = [
            {'station': Station(opts.via, code=via_code,
                                formal_name=formal_via_name,
                                identifier=client.locations(opts.via)[0].__dict__['id'])}]

    for intermediate_station in intermediate_stations:

        if intermediate_station['station'].is_in_france():
            # check for segments between station located in France only
            if not opts.quiet:
                print(f"\nVia {intermediate_station['station'].name}")

            farther_station = Station.get_farther_station(
                departure_direct_destinations,
                arrival_direct_destinations,
                intermediate_station)

            if farther_station == intermediate_station:
                segments = {0: {'departure': departure, 'arrival': intermediate_station['station'],
                                1: {'departure': intermediate_station['station'], 'arrival': arrival}}}
            else:
                segments = {1: {'departure': intermediate_station['station'], 'arrival': arrival},
                            0: {'departure': departure, 'arrival': intermediate_station['station'], }}
            results = {}
            for index, segment in segments.items():
                result = get_available_seats(segment['departure'].name_to_code()[0],
                                             segment['arrival'].name_to_code()[0],
                                             day,
                                             opts=SearchOptions(
                                                 verbosity=opts.verbosity,
                                                 max_duration=opts.max_duration)
                                             )
                if result:
                    results[index] = result
                    if opts.verbosity:
                        print(f"Segment {index + 1} found")
                        Proposal.display(result)
                else:
                    if opts.verbosity:
                        print(f"{BColors.FAIL} Segment {index + 1} not found {BColors.ENDC}")
                    break

                # To optimize the search, we first search for the longest segment
                # (most demanded than the shortest and potentially limiting factor)
                # Exemple : For Beziers-Paris (~4h) via Nimes, we first search for
                # the journey from Nimes to Paris (~3h), then for the journey
                # from Beziers-Nimes (~1h), because longer segment is rare

                if len(results) > 1:  # Display results if more than one segment found
                    MultipleProposals.display(results[0], results[1], opts.berth_only, opts.long)


def total_search(dpt_name: str, arr_name: str, days: int, days_delta: int, opts: SearchOptions):
    """
    :param dpt_name:
    :param arr_name:
    :param days:
    :param days_delta:
    :param opts:
    :return:
    """
    date = datetime.now().replace(hour=0, minute=0) + timedelta(days=days_delta)

    departure_code, formal_departure_name = Station.name_to_code(Station(dpt_name))
    arrival_code, formal_arrival_name = Station.name_to_code(Station(arr_name))

    departure = Station(dpt_name, code=departure_code, formal_name=formal_departure_name,
                        identifier=client.locations(dpt_name)[0].__dict__['id'])
    arrival = Station(arr_name, code=arrival_code, formal_name=formal_arrival_name,
                      identifier=client.locations(arr_name)[0].__dict__['id'])

    arrival_direct_destinations = DirectDestination(arrival, get('https://api.direkt.bahn.guru/' + arrival.identifier))
    departure_direct_destinations = DirectDestination(departure,
                                                      get('https://api.direkt.bahn.guru/' + departure.identifier))

    for day_counter in range(days):
        day = date + timedelta(days=day_counter)
        print(day.strftime("%c"))

        print(f"Direct journey from {formal_departure_name} to {formal_arrival_name}")
        direct_proposals = get_available_seats(departure_code, arrival_code, day,
                                               SearchOptions(opts.verbosity, opts.max_duration))
        Proposal.display(direct_proposals, opts.berth_only, opts.long)

        if not opts.direct_only:
            get_indirect_proposals(departure, arrival,
                                   departure_direct_destinations,
                                   arrival_direct_destinations,
                                   day,
                                   opts)


def main():
    """
    Main function
    :return:
    """
    parser = ArgumentParser()
    parser.add_argument("stations", metavar="station", help="Station names", nargs=2)
    parser.add_argument("-t", "--timedelta", help="How many days from today", type=int, default=1)
    parser.add_argument("-p", "--period", help="Number of days to search", type=int, default=1)
    parser.add_argument("-d", "--direct-only", help="Print direct proposals only",
                        action="store_true")
    parser.add_argument("-b", "--berth-only", help="Print berth only for Intercites de Nuit proposals",
                        action="store_true")
    parser.add_argument("--via", type=str, help="Force connection station with specified name")
    parser.add_argument("-l", "--long",
                        help="Add details for prompted proposals, including transporter and vehicle number",
                        action="store_true")
    parser.add_argument("--max-duration", type=int, help="Maximum duration of a journey", default=600)
    parser.add_argument("-q", "--quiet", help="Only show results", action="store_true")
    parser.add_argument("-v", "--verbosity", action="store_true", help="Verbosity")
    autocomplete(parser)
    args = parser.parse_args()

    total_search(args.stations[0],
                 args.stations[1],
                 args.period,
                 args.timedelta,
                 SearchOptions(
                     direct_only=args.direct_only,
                     berth_only=args.berth_only,
                     via=args.via,
                     long=args.long,
                     max_duration=args.max_duration,
                     verbosity=args.verbosity,
                     quiet=args.quiet
                 )
                 )


if __name__ == '__main__':
    try:
        main()

    except KeyboardInterrupt:  # Catch CTRL-C
        print('Interrupted')
        sys_exit(1)
