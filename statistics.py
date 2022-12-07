from sys import exit as sys_exit
from requests import post

from config import Config


class Statistics:
    """
    Statistics class about
    """
    amount = 0
    frequented_stations = {}

    # noinspection SpellCheckingInspection
    def __init__(self):

        headers = {
        'authority': 'www.sncf-connect.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'fr-FR,fr;q=0.9',
        'cache-control': 'no-cache',

    }


        response = post(
            'https://www.sncf-connect.com/bff/api/v1/trips',
            headers=headers, json = {}        )
        if response.status_code == 200:
            self.data = response.json()
        else:
            sys_exit('Error: ' + str(response.status_code))

    def analyze(self):
        """
        Analyze the order history from oui.sncf account
        """
        if 'response' in self.data and 'cancelledTrips' in self.data['response']:
            for trip in self.data['response']['cancelledTrips']:
                print(trip)

    #         self.amount += self.data['passedTrips'][0]['amount']  # count total amount spend
    #         for segment in order['trainFolders'][0]['travels'][0]['segments']:
    #             # for each segment in the travel
    #             for station in ('origin', 'destination'):
    #                 if segment[station]['stationName'] in self.frequented_stations:
    #                     self.frequented_stations[segment[station]['stationName']] += 1
    #                     # if key exists increment value, else set value to 1
    #                 else:
    #                     self.frequented_stations[segment[station]['stationName']] = 1
    #
    # print(f'Total amount: {str(self.amount)} €')
    # favorites_stations = sorted(self.frequented_stations.items(), key=lambda stations: stations[1], reverse=True)
    # print(f'Favorites stations: {favorites_stations[:5]}')


s = Statistics()
s.analyze()
