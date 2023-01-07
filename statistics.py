from sys import exit as sys_exit
from requests import post

from config import Config
from proposal import Proposal


class Statistics:
    """
    Statistics class about passed trips on SNCF Connect
    """
    amount = 0
    count = 0
    frequented_stations = {}
    journeys = {}
    delay_duration = 0
    delay_count = 0
    total_duration = 0
    first_trip_date = ""
    transporters = {}


    # noinspection SpellCheckingInspection
    def __init__(self):

        headers = {
            'authority': 'www.sncf-connect.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'fr-FR,fr;q=0.9',
            'cache-control': 'no-cache',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'cookie': Config.SNCFCONNECT_COOKIE,
            'x-bff-key': 'ah1MPO-izehIHD-QZZ9y88n-kku876'
        }
        response = post(
            'https://www.sncf-connect.com/bff/api/v1/trips',
            headers=headers, json = {} )
        if response.status_code == 200:
            self.data = response.json()
        else:
            sys_exit('Error: ' + str(response.status_code) + str(response.text))

    def analyze(self):
        """
        Analyze response
        """
        if 'response' in self.data and 'passedTrips' in self.data['response'] and self.data['response']['passedTrips']: # if response field exists
            # get first trip date
            self.first_trip_date = self.data['response']['passedTrips'][-1]['sortDate']

            for trip in self.data['response']['passedTrips']: # let's iterate through all passed trips
                # count total amount spend
                self.amount += float(trip['trip']['tripDetails']['outwardJourney']['priceLabel'].split('€')[0].replace(',','.'))

                # count most frequented stations
                for station in ('originLabel', 'destinationLabel'):
                    if trip['trip'][station] in self.frequented_stations:
                        self.frequented_stations[trip['trip'][station]] += 1 # if key exists increment count value
                    else:
                        self.frequented_stations[trip['trip'][station]] = 1 # else set value to 1

                # count most frequented journeys
                if f"{trip['trip']['originLabel']} -> {trip['trip']['destinationLabel']}" in self.journeys:
                    self.journeys[f"{trip['trip']['originLabel']} -> {trip['trip']['destinationLabel']}"] +=1
                else:
                    self.journeys[f"{trip['trip']['originLabel']} -> {trip['trip']['destinationLabel']}"] = 1

                # count trip delay on arrival
                if trip['trip']['tripIv']['disruptions']['messages']: # if traveller messages ("tripIv" = information voyageur) exists
                    for message in trip['trip']['tripIv']['disruptions']['messages']:
                        if message['disruptionType'] == "DISRUPTION_DELAYED":
                            delay_on_arrival = int(message['title'].split(' min')[-2].split(' ')[-1]) # extract delay in string
                            # we count only the arrival delay, so string "retard au départ" must also contains "à l'arrivée"
                            if "au départ" in message['title']:
                                if "à l’arrivée" in message['title']:
                                    self.delay_duration += delay_on_arrival
                                    self.delay_count += 1
                                else:
                                    pass
                            else: # if string like "Retard estimé à 60 min", consider as arrival delay
                                self.delay_duration += delay_on_arrival
                                self.delay_count += 1

                # count trip duration
                if trip['trip']['duration']:
                    self.total_duration += Proposal.parse_duration(trip['trip']['duration'])

                # count transporters
                if 'correspondance' not in trip['trip']['transportersRecapLabel']: # exclude 'correspondance' transporter
                    if f"{trip['trip']['transportersRecapLabel']}" in self.transporters:
                        self.transporters[f"{trip['trip']['transportersRecapLabel']}"] +=1
                    else:
                        self.transporters[f"{trip['trip']['transportersRecapLabel']}"] = 1


            print(f"Total trips since {self.first_trip_date.split('T')[0]} :"
                  f" passed {len(self.data['response']['passedTrips'])},"
                  f" cancelled {len(self.data['response']['cancelledTrips'])}")
            print(f"Transporters : {self.transporters}")

            print(f"Total amount spend: { '{:.2f}'.format(self.amount)} €")

            favorites_stations = sorted(self.frequented_stations.items(), key=lambda stations: stations[1], reverse=True)
            print(f"Favorites stations: {favorites_stations[:10]}")

            favorite_journeys = sorted(self.journeys.items(), key=lambda journeys: journeys[1], reverse=True)
            print(f"Favorites journeys: {favorite_journeys[:10]}")

            print(f"Total time spend in SNCF trains: {self.total_duration//60} hours ({self.total_duration//60/24:.2f} days)")
            print(f"Total delay: {self.delay_duration//60} hours, {self.delay_count}/{len(self.data['response']['passedTrips'])} trains delayed")

        else:
            print('No trips found for your account. Are you sure you provide all your cookies ?')
