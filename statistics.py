from sys import exit as sys_exit
from requests import get

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
            'authority': 'www.oui.sncf',
            'cache-control': 'max-age=0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-gpc': '1',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-dest': 'document',
            'accept-language': 'fr-FR,fr;q=0.9',
            'Cookie': Config.OUISNCF_STATS_COOKIE
        }
        response = get(
            'https://www.oui.sncf/api/gtw/aftersale/prd/vsa/api/v2/orders/oui-account?ascSort=false&localeParam=fr_FR&pageNumber=1&pageResultsCount=200&statusFilter=PASSED',
            headers=headers)
        if response.status_code == 200:
            self.data = response.json()
        else:
            sys_exit('Error: ' + str(response.status_code))

    def analyze(self):
        """
        Analyze the order history from oui.sncf account
        """
        for order in self.data['orders']:
            if 'trainFolders' in order:  # Order must contain train, exclude discount cards
                self.amount += order['trainFolders'][0]['amount']  # count total amount spend
                for segment in order['trainFolders'][0]['travels'][0]['segments']:
                    # for each segment in the travel
                    for station in ('origin', 'destination'):
                        if segment[station]['stationName'] in self.frequented_stations:
                            self.frequented_stations[segment[station]['stationName']] += 1
                            # if key exists increment value, else set value to 1
                        else:
                            self.frequented_stations[segment[station]['stationName']] = 1

        print(f'Total amount: {str(self.amount)} €')
        favorites_stations = sorted(self.frequented_stations.items(), key=lambda stations: stations[1], reverse=True)
        print(f'Favorites stations: {favorites_stations[:5]}')


s = Statistics()
s.analyze()
