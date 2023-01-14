"""
Code related to train travel statistics
"""
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
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/108.0.0.0 Safari/537.36',
            'cookie': Config.SNCFCONNECT_COOKIE,
            'x-bff-key': 'ah1MPO-izehIHD-QZZ9y88n-kku876'
        }
        response = post(
            'https://www.sncf-connect.com/bff/api/v1/trips',
            headers=headers, json = {}, timeout=10 )
        if response.status_code == 200:
            self.response = response.json()
            self.check_response()
        else:
            sys_exit('Error: ' + str(response.status_code) + str(response.text))

    def check_response(self) -> None:
        """
        Check if data include at least one passed trip in the response
        """
        if 'response' in self.response and 'passedTrips' in self.response['response']:
            if len(self.response['response']['passedTrips']) > 0:
                self.analyze()
            else:
                print('No trips found for your account. Are you sure you provide all your cookies ?')
                sys_exit(1)

    def analyze(self):
        """
        Analyze and parse response from SNCF Connect API
        """
        # get first trip date
        self.first_trip_date = self.response['response']['passedTrips'][-1]['sortDate']

        for trip_data in self.response['response']['passedTrips']: # let's iterate through all passed trip
            trip = trip_data['trip']
            self.parse_one_trip(trip)

    def parse_one_trip(self, trip) -> None:
        """
        Extract data from one trip
        :param trip: trip object to be parsed
        """
        # count total amount spend
        amount_str = trip['tripDetails']['outwardJourney']['priceLabel'].split('€')[0]
        self.amount += float(amount_str.replace(',','.'))

        # count most frequented stations
        for station in ('originLabel', 'destinationLabel'):
            if trip[station] in self.frequented_stations:  # if key exists increment value
                self.frequented_stations[trip[station]] += 1
            else:
                self.frequented_stations[trip[station]] = 1 # else initialize value to 1

        # count most frequented journeys
        if f"{trip['originLabel']} -> {trip['destinationLabel']}" in self.journeys:
            self.journeys[f"{trip['originLabel']} -> {trip['destinationLabel']}"] +=1
        else:
            self.journeys[f"{trip['originLabel']} -> {trip['destinationLabel']}"] = 1

        # count trip delay on arrival
        # if traveller messages ("tripIv" = information voyageur) exists
        if trip['tripIv']['disruptions']['messages']:
            for message in trip['tripIv']['disruptions']['messages']:
                if message['disruptionType'] == "DISRUPTION_DELAYED":
                    delay_on_arrival = int(message['title'].split(' min')[-2].split(' ')[-1]) # extract delay in string
                    # we count only the arrival delay, so string "retard au départ" must also contains "à l'arrivée"
                    if "au départ" in message['title']:
                        if "à l’arrivée" in message['title']:
                            self.delay_duration += delay_on_arrival
                            self.delay_count += 1
                    else: # if string like "Retard estimé à 60 min", consider as arrival delay
                        self.delay_duration += delay_on_arrival
                        self.delay_count += 1

        # count trip duration
        if trip['duration']:
            self.total_duration += Proposal.parse_duration(trip['duration'])

        # count transporters (with exclusion of 'correspondance')
        if 'correspondance' not in trip['transportersRecapLabel']:
            if f"{trip['transportersRecapLabel']}" in self.transporters:
                self.transporters[f"{trip['transportersRecapLabel']}"] +=1
            else:
                self.transporters[f"{trip['transportersRecapLabel']}"] = 1

    def show(self) -> None:
        """
        Show passed trips statistics
        """

        print(f"Total trips since {self.first_trip_date.split('T')[0]} :"
              f" passed {len(self.response['response']['passedTrips'])},"
              f" cancelled {len(self.response['response']['cancelledTrips'])}")
        print(f"Transporters : {self.transporters}")

        print(f"Total amount spend: {self.amount:.2f} €")

        favorites_stations = sorted(self.frequented_stations.items(), key=lambda stations: stations[1], reverse=True)
        print(f"Favorites stations: {favorites_stations[:10]}")

        favorite_journeys = sorted(self.journeys.items(), key=lambda journeys: journeys[1], reverse=True)
        print(f"Favorites journeys: {favorite_journeys[:10]}")

        print(f"Total time spend in SNCF trains: "
              f"{self.total_duration//60} hours ({self.total_duration//60/24:.2f} days)")

        print(f"Total delay: {self.delay_duration//60} hours, "
              f"{self.delay_count}/{len(self.response['response']['passedTrips'])} trains delayed")
        sys_exit(0)
