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
