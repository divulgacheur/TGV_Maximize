from typing import TYPE_CHECKING

import requests
from unidecode import unidecode

if TYPE_CHECKING:
    from direct_destination import DirectDestination


class Station:
    """
    Class for a station.
    """
    name: str
    identifier: str
    latitude: float
    longitude: tuple[float]
    code: str

    def __init__(self, name, formal_name=None, coordinates=None, identifier=None, code=None):
        self.name = name
        self.formal_name = formal_name
        self.coordinates = coordinates
        self.identifier = identifier
        self.code = code

    def is_in_france(self):
        """
        Check if the station is in France
        :return: True if the station is in France, False otherwise
        """
        return self.identifier[:2] == '87'

    # noinspection SpellCheckingInspection
    def name_to_code(self) -> (str, str) or None:
        """
        Get the station code from the station name
        For multiple station in the same city, return generic codes to avoid ambiguity
        (e.g. "Gare de Lyon/ Gare Montparnasse" -> "FRPAR")
        :return: Station code (5 letters)
        """
        if self.code is not None:
            return self.code, self.name
        elif self.name.startswith('Paris'):
            return 'FRPAR', 'Paris'
        elif self.name.startswith('Lyon'):
            return 'FRLYS', 'Lyon'
        elif self.name == 'Aeroport Paris-Charles de Gaulle TGV':
            return 'FRMLW', 'Paris Aéroport Roissy Charles-de-Gaulle'
        elif self.name == 'Massy TGV':
            return 'FRDJU', 'Paris Massy'
        elif self.name.startswith('Le Creusot Montceau'):
            return 'FRMLW', 'Le Creusot - Montceau TGV '
        elif 'Montpellier' in self.name:
            return 'FRMPL', 'Montpellier'
        elif 'Nice' in self.name:
            return 'FRNCE', 'Nice'
        elif self.name == 'Vierzon Ville':
            return 'FRXVZ', 'Vierzon'
        elif self.name == 'Vendôme Villiers sur Loire':
            return 'FRAFM', 'Vendôme'
        elif self.name == 'Moulins-sur-Allier':
            return 'FRXMU', 'Moulins'
        elif self.name == 'Saumur Rive Droit':
            return 'FRACN', 'Saumur'
        elif self.name == 'Orange(Avignon)':
            return 'FRXOG', 'Orange'
        elif self.name.endswith('Ville'):  # endswith because Montauban-Ville-Bourbon
            query = self.name.replace('Ville', '')
        elif self.name.endswith('Hbf'):
            # Hbf == German for central railway station, see https://en.wikipedia.org/wiki/HBF
            query = self.name.replace('Hbf', '')
        else:
            query = self.name
        result = self.get_station_code(query)
        if not result:
            raise ValueError(f'The station {self.name} does not exist')
        return result

    @staticmethod
    def get_station_code(station_name):
        """
        Get the station code from the station name
        :param station_name: Station official name
        :return: Station code (5 letters)
        """

        station_match = requests.get(
            'https://www.oui.sncf/booking/autocomplete-d2d?',
            params={'uc': 'fr-FR', 'searchField': 'origin', 'searchTerm': unidecode(station_name)},
            headers={'User-Agent': 'Mozilla/5.0'})
        station_match.close()
        if station_match.status_code == 200:
            station_match_json = station_match.json()
            if station_match_json:
                if 'rrCode' in station_match_json[0]:
                    return station_match_json[0]['rrCode'], station_match_json[0]['label']
                return station_match_json[0]['id'].split('_')[-1], station_match_json[0]['label']
        return None

    @classmethod
    def get_farther_station(cls, departure: 'DirectDestination', arrival: 'DirectDestination',
                            intermediate_station: 'dict') -> 'Station':
        """
        Get the station that is the farthest from the departure station
        :param departure:
        :param arrival:
        :param intermediate_station:
        :return:
        """
        if intermediate_station['station'] in departure.destinations and\
                departure.destinations[intermediate_station['station'].identifier]['duration'] > \
                arrival.destinations[intermediate_station['station'].identifier]['duration']:
            return departure.station
        return intermediate_station['station']

    @classmethod
    def parse(cls, proposal):
        """
        Parse a proposal from the API
        :param proposal: JSON object from the API
        :return: Station object
        """
        return Station(str.lower(proposal['station']['label']),
                       proposal['latitude'],
                       proposal['longitude'],
                       code=proposal['station']['metaData']['PAO']['code'],
                       )


# Nimes (centre) = Nimes Pont du Gard
PARIS = {
    'station':
        Station(name='Paris', code='FRPAR', coordinates=(48.856614, 2.3522219), identifier='8796001')
}
