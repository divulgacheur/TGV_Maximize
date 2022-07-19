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
from requests import session

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

    response = Proposal.get_next(dep_station, arr_station, day.strftime('%Y-%m-%dT%H:%M:00')+'.000Z', opts)
    if response:
        response_json = response.json()['longDistance']
        sleep(2)

        if response_json is not None:
            all_proposals = Proposal.filter(response_json['proposals']['proposals'], opts.max_duration)

            while response_json['proposals']['pagination']['next']['changeDay'] is False:
                if opts.verbosity:
                    print(f'\t Next page - {page_count}')
                response = Proposal.get_next(dep_station,
                                             arr_station,
                                             Proposal.get_last_timetable(response)+'.000Z',
                                             opts.verbosity)
                response_json = response.json()['longDistance']
                page_count += 1
                sleep(2)
                if response_json is not None and 'proposals' in response_json:
                    all_proposals.extend(
                        Proposal.filter(response_json['proposals']['proposals'], opts.max_duration))
        return Proposal.remove_duplicates(all_proposals, opts.verbosity) if all_proposals else []


def display_indirect_proposals(dpt_direct_dest, arr_direct_dest, day, opts):
    """
    Display indirect train proposals for a given day
    :param dpt: station of departure
    :param arr: station of arrival
    :param dpt_direct_dest: direct destinations of departure
    :param arr_direct_dest: direct destinations of arrival
    :param day: date of departure
    :param opts: search options
    """

    if not opts.via:
        intermediate_stations = dpt_direct_dest.get_common_stations(
            arr_direct_dest) + [PARIS]
    else:
        via = Station(opts.via)
        via.get_code()
        via.get_identifier()
        intermediate_stations = [{'station': via}]

    for intermediate_station in intermediate_stations:
        if intermediate_station['station'].is_in_france():
            # check for segments between station located in France only
            if not opts.quiet:
                print(f"\nVia {intermediate_station['station'].name}")

            farther_station = Station.get_farther(
                dpt_direct_dest,
                arr_direct_dest,
                intermediate_station)

            segments = [{'dpt': dpt_direct_dest.station, 'arr': intermediate_station['station']},
                        {'dpt': intermediate_station['station'], 'arr': arr_direct_dest.station}]

            if farther_station == intermediate_station:
                segments.reverse()

            results = {}
            for index, segment in enumerate(segments):
                result = get_available_seats(segment['dpt'].name_to_code()[0],
                                             segment['arr'].name_to_code()[0],
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
                # from Beziers-Nimes (~1h), because longer segment is rarer

                if len(results) > 1:  # Display results if more than one segment found
                    MultipleProposals.display(results[0], results[1], opts.berth_only, opts.long)


def total_search(dpt_name: str, arr_name: str, days: int, days_delta: int, opts: SearchOptions):
    """
    :param dpt_name: name of departure station
    :param arr_name: name of arrival station
    :param days: number of days to search
    :param days_delta: number of days to search from today
    :param opts: search options
    """
    date = datetime.now().replace(hour=0, minute=0) + timedelta(days=days_delta)

    departure = Station(dpt_name)
    departure.get_code()
    departure.get_identifier()
    dpt_direct_dest = DirectDestination.get(departure)

    arrival = Station(arr_name)
    arrival.get_code()
    arrival.get_identifier()
    arr_direct_dest = DirectDestination.get(arrival)

    for day_counter in range(days):
        day = date + timedelta(days=day_counter)
        print(day.strftime("%c"))

        print(f"Direct journey from {departure.formal_name} to {arrival.formal_name}")
        direct_proposals = get_available_seats(departure.code, arrival.code, day,
                                               SearchOptions(opts.verbosity, opts.max_duration))
        Proposal.display(direct_proposals, opts.berth_only, opts.long)

        if not opts.direct_only:
            print(f"Let's split the journey from {departure.name} to {arrival.name}", end=' : ')
            display_indirect_proposals(dpt_direct_dest, arr_direct_dest, day, opts)


def main():
    """
    Main function
    """
    parser = ArgumentParser()
    parser.add_argument("stations", metavar="station", help="Station names", nargs=2)
    parser.add_argument("-t", "--timedelta", help="How many days from today", type=int, default=1)
    parser.add_argument("-p", "--period", help="Number of days to search", type=int, default=1)
    parser.add_argument("-d", "--direct-only", help="Print direct proposals only",
                        action="store_true")
    parser.add_argument("-b", "--berth-only", help="Print berth only "
                                                   "for Intercites de Nuit proposals",
                        action="store_true")
    parser.add_argument("--via", type=str, help="Force connection station with specified name")
    parser.add_argument("-l", "--long", help="Add details for prompted proposals,"
                                             " including transporter and vehicle number",
                        action="store_true")
    parser.add_argument("--max-duration", type=int, help="Maximum duration of a journey",
                        default=600)
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
