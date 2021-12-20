from operator import itemgetter

import requests

from Station import Station


class DirectDestination:
    station: Station
    destinations: dict[str, Station]

    def __init__(self, station: Station, request: requests.Response):
        self.station = station
        self.destinations = {
            station['id']: {
                'station':
                    Station(
                        name=station['name'],
                        latitude=station['location']['latitude'],
                        longitude=station['location']['longitude'],
                        identifier=station['id'],
                    ),
                'duration':
                    station['duration']}
            for station in request.json()}

    def get_common_stations(self: 'DirectDestination',
                            arrival_direct_destinations: 'DirectDestination') -> [Station]:
        print("Let's try to split the journey from", self.station.name, 'to',
              arrival_direct_destinations.station.name, end=' : ')

        destinations_keys = set(self.destinations.keys()).intersection(
            arrival_direct_destinations.destinations.keys())
        destinations = list(itemgetter(*destinations_keys)(
            self.destinations | arrival_direct_destinations.destinations))

        print(len(destinations), 'intermediate stations available')

        return destinations
