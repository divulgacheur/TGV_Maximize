#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
"""
Script entry point
"""
from argparse import ArgumentParser, SUPPRESS
from datetime import datetime, timedelta
from locale import setlocale, LC_TIME
from time import sleep
from sys import exit as sys_exit
from random import uniform

from argcomplete import autocomplete
from pyhafas import HafasClient
from pyhafas.profile import DBProfile
from alive_progress import alive_bar

from direct_destination import DirectDestination
from multiple_proposals import MultipleProposals
from options import SearchOptions, PromptOptions
from proposal import Proposal, console
from station import Station, PARIS
from trips_statistics import Statistics

setlocale(LC_TIME, "fr_FR.UTF-8")
client = HafasClient(DBProfile())


def wait_random_time() -> None:
    """
    Sleep script during a random interval of time
    :return: None
    """
    sleep(uniform(2.5, 4.0))


def get_available_seats(dep_station: str, arr_station: str, day: datetime,
                        search_opts: SearchOptions, prompt_opts: PromptOptions) -> [Proposal]:
    """
    Returns train proposals for a given day
    :param dep_station: station of departure
    :param arr_station: station of arrival
    :param day: date of departure wished
    :param search_opts: search options specified by the user
    :param prompt_opts: display options specified by the user

    :return: List of journey 'Proposal' objects
    """
    all_proposals = []
    with alive_bar(title='Searching', stats=False, disable=prompt_opts.quiet, monitor="Page {count}") as progress_bar:
        response = Proposal.get_next(dep_station, arr_station, day.strftime('%Y-%m-%dT%H:%M:00'), prompt_opts.verbosity)
        progress_bar()  # pylint: disable=not-callable
        if response:
            response_json = response.json()['longDistance']
            wait_random_time()

            if response_json is not None and response_json['proposals'] and response_json['proposals']['proposals']:
                all_proposals = Proposal.filter(response_json['proposals']['proposals'], search_opts.max_duration)
                if prompt_opts.debug:
                    print(response_json['proposals'])
                while response_json['proposals']['pagination']['next']['changeDay'] is False:
                    response = Proposal.get_next(dep_station,
                                                 arr_station,
                                                 Proposal.get_last_timetable(response),
                                                 prompt_opts.verbosity)
                    response_json = response.json()['longDistance']
                    progress_bar()  # pylint: disable=not-callable
                    wait_random_time()
                    all_proposals.extend(
                        Proposal.filter(response_json['proposals']['proposals'], search_opts.max_duration))
        progress_bar.title = 'Search has finished'
    return Proposal.remove_duplicates(all_proposals, prompt_opts.verbosity) if all_proposals else []


def display_indirect_proposals(dpt_direct_dest, arr_direct_dest, day,
                               search_opts: SearchOptions, prompt_opts: PromptOptions) -> None:
    """
    Display indirect train proposals for a given day
    :param dpt_direct_dest: direct destinations of departure
    :param arr_direct_dest: direct destinations of arrival
    :param day: date of departure
    :param search_opts: search options
    :param prompt_opts: search options
    :return: None
    """

    if not search_opts.via:
        intermediate_stations = DirectDestination.get_common_stations(dpt_direct_dest, arr_direct_dest) + [PARIS]
    else:  # if --via option is specified, search only proposals via this station
        via = Station(search_opts.via)
        via.get_code()
        via.get_identifier()
        intermediate_stations = [{'station': via}]

    for intermediate_station in intermediate_stations:
        # check for segments between station located in France only
        if intermediate_station['station'].is_in_france():
            if not prompt_opts.quiet:
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
                                             search_opts,
                                             prompt_opts
                                             )
                if result:
                    results[index] = result
                    if prompt_opts.verbosity:
                        print(f"Segment {index + 1} found :")
                        Proposal.display(result, long=True)
                else:
                    if prompt_opts.verbosity:
                        console.print(f"Segment {index + 1} not found", style='red')
                    break # it's useless to search next segment if one is not available

                # To optimize the search, we first search for the longest segment
                # (most demanded than the shortest and potentially limiting factor)
                # Exemple : For Beziers-Paris (~4h) via Nimes, we first search for
                # the journey from Nimes to Paris (~3h), then for the journey
                # from Beziers-Nimes (~1h), because longer segment is rarer

                if len(results) > 1:  # Display results if more than one segment found
                    MultipleProposals.display(results[0], results[1], search_opts, prompt_opts)


def display_proposals(dpt_name: str, arr_name: str, days: int, days_delta: int,
                      search_opts: SearchOptions, prompt_opts: PromptOptions):
    """
    Display train proposals depending on search options provided by the user
    :param dpt_name: name of departure station
    :param arr_name: name of arrival station
    :param days: number of days to search
    :param days_delta: number of days to search from today
    :param search_opts: search options defined by user
    :param prompt_opts: display options defined by user
    """

    # set initial search date based on --timedelta argument
    date = datetime.now().replace(hour=0, minute=0, second=1) + timedelta(days=days_delta)

    departure = Station(dpt_name)  # Store station name
    departure.get_code()  # Get station code from name (ex: Paris-> FRPAR)
    arrival = Station(arr_name)
    arrival.get_code()
    if prompt_opts.verbosity:
        print("Stations codes acquired")
        # acquire direct destinations of both stations only if --direct option is not specified

    if search_opts.direct_only:
        dpt_direct_dest = arr_direct_dest = None
    else:
        departure.get_identifier()
        arrival.get_identifier()
        dpt_direct_dest = DirectDestination.get(departure)
        arr_direct_dest = DirectDestination.get(arrival)
        if prompt_opts.verbosity:
            print("Stations identifiers acquired")

    for day_counter in range(days):  # Iterate over the period (--period) specified by the user
        day = date + timedelta(days=day_counter)
        print(day.strftime("%c"))

        print(f"Direct journey from {departure.display_name} to {arrival.display_name}")

        direct_proposals = get_available_seats(departure.code, arrival.code, day, search_opts, prompt_opts)
        if direct_proposals:
            Proposal.display(direct_proposals, search_opts.berth_only, prompt_opts.long)
        elif prompt_opts.verbosity:
            print("No direct journey found")

        if not search_opts.direct_only:
            print(f"Let's split the journey from {departure.formal_name} to {arrival.formal_name} :")
            display_indirect_proposals(dpt_direct_dest, arr_direct_dest, day, search_opts, prompt_opts)


def main():
    """
    Main function
    """
    parser = ArgumentParser(add_help=False)
    parser.add_argument("--statistics", action="store_true", help="Show only account statistics")
    args, _ = parser.parse_known_args()

    if args.statistics:
        statistics = Statistics()
        statistics.show()

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
    parser.add_argument("-q", "--quiet", action="store_true", help="Only show results")
    parser.add_argument("-v", "--verbosity", action="store_true", help="Verbosity")
    parser.add_argument("--debug", action="store_true", help="Debug")
    parser.add_argument('-h', '--help', action='help', default=SUPPRESS,
                        help='Show this help message and exit.')


    autocomplete(parser)
    args = parser.parse_args()

    display_proposals(args.stations[0],
                      args.stations[1],
                      args.period,
                      args.timedelta,
                      SearchOptions(
                          via=args.via,
                          max_duration=args.max_duration,
                          berth_only=args.berth_only,
                          direct_only=args.direct_only,
                      ),
                      PromptOptions(
                          verbosity=args.verbosity,
                          quiet=args.quiet,
                          debug=args.debug,
                          long=args.long,
                      )
                      )


if __name__ == '__main__':
    try:
        main()

    except KeyboardInterrupt:  # Catch CTRL-C
        print('Interrupted')
        sys_exit(1)
