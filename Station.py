import requests
import unidecode as unidecode

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from DirectDestination import DirectDestination


class Station:
    name: str
    id: str
    latitude: float
    longitude: float
    code: str

    def __init__(self, name, formal_name=None, latitude=None, longitude=None, identifier=None, code=None):
        self.name = name
        self.formal_name = formal_name
        self.id = identifier
        self.code = code
        self.latitude = latitude
        self.longitude = longitude

    def is_in_france(self):
        return self.id[:2] == '87'

    # noinspection SpellCheckingInspection
    def name_to_code(self) -> (str, str) or None:
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
        elif self.name.endswith('Hbf'):  # https://en.wikipedia.org/wiki/HBF
            query = self.name.replace('Hbf', '')
        else:
            query = self.name
        station_match = requests.get(
            'https://www.oui.sncf/booking/autocomplete-d2d?uc=fr-FR&searchField=origin&searchTerm=' +
            unidecode.unidecode(query), headers={'User-Agent': 'Mozilla/5.0'})
        station_match.close()
        if station_match.status_code == 200:
            station_match_json = station_match.json()
            if station_match_json:
                if 'rrCode' in station_match_json[0]:
                    return station_match_json[0]['rrCode'], station_match_json[0]['label']
                else:
                    return station_match_json[0]['id'].split('_')[-1], station_match_json[0]['label']
        raise ValueError('The station ' + self.name + ' does not exist')

    @staticmethod
    def get_station_code(station_name):
        response = requests.get('https://www.oui.sncf/booking/autocomplete-d2d?uc=fr-FR&searchField=origin&searchTerm',
                                data={'searchTerm': station_name})
        if response.status_code != 200:
            exit(response.status_code)
        return response.json()[0]['rrCode']

    @classmethod
    def get_farther_station(cls, departure: 'DirectDestination', arrival: 'DirectDestination',
                            intermediate_station: 'dict') -> 'Station':
        if departure.destinations[intermediate_station['station'].id]['duration'] > \
                arrival.destinations[intermediate_station['station'].id]['duration']:
            return departure.station
        else:
            return intermediate_station['station']


# Nimes (centre) = Nimes Pont du Gard
PARIS = {
    'station': Station(name='Paris', code='FRPAR', latitude=48.856614, longitude=2.3522219, identifier=8796001)
}
