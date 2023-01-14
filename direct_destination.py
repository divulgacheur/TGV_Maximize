"""
Code related to direct destinations accessible from train station
"""
from operator import itemgetter
from requests import get, Response as ReqResponse

from station import Station


class DirectDestination:
    """
    Class for finding the direct destinations of a given station.
    """

    station: Station
    destination = {'station': Station, 'duration': int}
    destinations: dict[str, destination]

    def __init__(self, station: Station, destinations: dict[str, destination]):
        self.station = station
        self.destinations = destinations

    @staticmethod
    def parse(station: Station, request: ReqResponse):
        """
        Parses the direct destinations of a given station and JSON response of the API.
        """
        destinations = {
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
        return DirectDestination(station, destinations)
    @staticmethod
    def get_common_stations(departure_direct_destinations: 'DirectDestination',
                            arrival_direct_destinations: 'DirectDestination') -> [Station]:
        """
        Returns a list of stations that are common to both the departure and arrival stations
        :param departure_direct_destinations: The departure station's direct destinations
        :param arrival_direct_destinations: The arrival station's direct destinations
        :return: A list of stations
        """

        destinations_keys = set(departure_direct_destinations.destinations.keys()).intersection(
            arrival_direct_destinations.destinations.keys())
        destinations = list(itemgetter(*destinations_keys)(
            departure_direct_destinations.destinations | arrival_direct_destinations.destinations))

        print(len(destinations), 'intermediate stations available')

        return destinations

    @staticmethod
    def get(departure: Station):
        """
        Returns the direct destinations of a given station.
        """
        response = get('https://api.direkt.bahn.guru/' + departure.identifier, timeout=15)
        if response.status_code != 200:
            print()
            raise ValueError(f'{departure.name} identifier not found is UIC database.'
                            ' Maybe you should use local station name, like Ventimiglia (IT)'
                            ' instead of Vintimille (FR) ?')
        return DirectDestination.parse(
            departure, response
            )
