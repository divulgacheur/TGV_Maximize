from operator import itemgetter

import requests

from station import Station


class DirectDestination:
    """
    Class for finding the direct destinations of a given station.
    """

    station: Station
    destination = {'station': Station, 'duration': int}
    destinations: dict[str, destination]

    def __init__(self, station: Station, request: requests.Response):
        self.station = station
        self.destinations = {
            station['id']: {
                'station':
                    Station(
                        name=station['name'],
                        coordinates=(
                            station['location']['latitude'], station['location']['longitude']),
                        identifier=station['id'],
                    ),
                'duration':
                    station['duration']}
            for station in request.json()}

    def get_common_stations(self: 'DirectDestination',
                            arrival_direct_destinations: 'DirectDestination') -> [Station]:
        """
        Returns a list of stations that are common to both the departure and arrival stations.
        :param self: The departure station's direct destinations.
        :param arrival_direct_destinations: The arrival station's direct destinations.
        :return: A list of stations
        """

        destinations_keys = set(self.destinations.keys()).intersection(
            arrival_direct_destinations.destinations.keys())
        destinations = list(itemgetter(*destinations_keys)(
            self.destinations | arrival_direct_destinations.destinations))

        print(len(destinations), 'intermediate stations available')

        return destinations
