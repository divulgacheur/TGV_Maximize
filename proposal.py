from datetime import datetime
from sys import exit as sys_exit
import requests

from bcolors import BColors
from station import Station
from config import Config


class Proposal:
    """
    Train travel Proposal class
    """

    duration: int
    min_price: int
    departure_date: datetime
    departure_station: Station
    arrival_date: datetime
    arrival_station: Station
    transporter: str
    vehicle_number: str
    remaining_seats: dict

    def __init__(self, duration, min_price, departure_date, departure_station, arrival_date,
                 arrival_station, transporter, vehicle_number, remaining_seats):
        """
        Initialize a Proposal object
        """

        self.duration = duration
        self.min_price = min_price
        self.departure_date = departure_date
        self.departure_station = departure_station
        self.arrival_date = arrival_date
        self.arrival_station = arrival_station
        self.transporter = transporter
        self.vehicle_number = vehicle_number
        self.remaining_seats = remaining_seats

    @staticmethod
    def parse_intercites_de_nuit(second_class_offers: any) -> dict:
        """
        Parse Intercités de nuit offers to get exact number of seats and berths
        :param second_class_offers: JSON object of the offers
        :return: dict with seats and berths
        """
        remaining = {}
        for offer in second_class_offers:
            if float(offer['priceLabel'].split(' ')[0].replace(",", ".") ) == 0:
                for message in offer['messages']:
                    physical_space = offer['comfortClass']['physicalSpaceLabel']
                    if 'Plus que' in message['message']:
                        remaining_quantity = [int(s) for s in message['message'].split() if s.isdigit()][0]
                    else:
                        remaining_quantity = 999
                    remaining[physical_space] = remaining_quantity

        return remaining

    @staticmethod
    def get_next(dpt_station, arr_station, dpt_date, verbosity) -> requests.Response:
        """
        Get next proposal response from oui.sncf API
        :param dpt_station: departure station code (5 letters)
        :param arr_station: arrival station code (5 letters)
        :param dpt_date: departure date (YYYY-MM-DDTHH:MM:SS)
        :param verbosity: enable verbosity
        :return: JSON response of the request
        """

        headers = {
            'Host': 'www.sncf-connect.com', 
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0', 
            'Accept': 'application/json, text/plain, */*', 'Accept-Language': 'fr,en-US;q=0.7,en;q=0.3', 'Accept-Encoding': 'gzip, deflate, br', 
            'x-bff-key': 'ah1MPO-izehIHD-QZZ9y88n-kku876', 'x-client-channel': 'web', 'x-client-app-id': 'front-web', 
            'x-api-env': 'production', 'x-market-locale': 'fr_FR',
            'x-email-hidden': '358C5C06A9357683EAF0119515C81AAE0A942BB5', 
            'x-email-strong': '9b0b6129b4c95891f8965bc7ad8d537ae9a1c71f3fa26da516c246afd17b765e', 
            'x-email-stronger': '860f0711e955b6bdb08000f7b4cba8c6b4eda78b5eb14e2bafae05510838f055', 
            'x-con-s': 'CPfztUAPfztUAAHABBENChCgAAAAAAAAAAAAAAAAAAEDoAMAAQSAIQAYAAgkAUgAwABBIANABgACCQAqADAAEEgBEAGAAIJABIAMAAQSAGQAYAAgkAAA.YAAAAAAAAAAA', 
            'x-con-id': 'fbac099fd2cccb74601b3c50ca1f697e78f', 'x-con-ex': 'fbab7d18833206847f893fb8a0d355225a5', 'x-app-version': '20220903.0.0-2022090300-641abe9ff5', 
            'x-device-os-version': 'Linux (x86_64)', 'x-device-class': 'desktop', 
            'x-attribution-referrer': 'https://www.sncf-connect.com/', 
            'x-nav-previous-page': 'Homepage', 'x-nav-current-path': '/app/home/search', 
            'x-visitor-type': '1', 'Origin': 'https://www.sncf-connect.com', 'DNT': '1', 
            'Connection': 'keep-alive', 'Referer': 'https://www.sncf-connect.com/app/home/search?destinationLabel=Paris&destinationId=CITY_FR_6455259', 
            'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'Pragma': 'no-cache', 'Cache-Control': 'no-cache', 'Content-Length': '0'
        }

        ####  reauthentification  ######
        session = requests.Session()
        headers["Cookie"] = Config.REAUTHENTICATE
        response = session.post("https://www.sncf-connect.com/bff/api/v1/web-refresh/reauthenticate",
                                   headers=headers)
        if response.status_code != 200:
            print("__Secure-refresh-account-tokem in REAUTHENTICATE in the .env file is misconfigured ! ")
        Config.update_cookies_from_dict("REAUTHENTICATE", session.cookies.get_dict())

        headers["Cookie"] = Config.REAUTHENTICATE

        data = {
            'schedule': {
                'outward': {
                    'date': dpt_date,
                    'arrivalAt': False,
                },
            },
            'mainJourney': {
                'origin': {
                    'label': 'Montpellier',
                    'id': 'RESARAIL_STA_' + dpt_station,
                    'geolocation': False,
                },
                'destination': {
                    'label': 'Besançon Franche-Comté TGV (à 16km de Besançon centre)',
                    'id': 'RESARAIL_STA_' + arr_station,
                    'geolocation': False,
                },
            },
            'passengers': [
                {
                    'id': '67161bc1-0e7a-40c8-8ff6-f66efaa77242',
                    'customerId': '100025623309',
                    'dateOfBirth': '2000-07-17',
                    'discountCards': [
                        {
                            'code': 'HAPPY_CARD',
                            'number': Config.TGVMAX_CARD_NUMBER,
                            'label': 'MAX JEUNE',
                        },
                        {
                            'code': 'ODS_PASS_ZOU!_ETUDES',
                            'label': 'SUD Provence-Alpes-Côte d’Azur - Pass ZOU! Etudes',
                        },
                    ],
                    'typology': 'YOUNG',
                    'displayName': 'Theo Peltier',
                    'firstName': 'Theo',
                    'lastName': 'Peltier',
                    'initials': 'TP',
                    'withoutSeatAssignment': False,
                },
            ],
            'pets': [],
            'itineraryId': 'c23d46e2-5fcb-4ca3-80a9-da412f6ccedb',
            'branch': 'SHOP',
            'forceDisplayResults': True,
            'directJourney': True,
            'trainExpected': True,
            'wishBike': False,
            'strictMode': False,
        }

        response = session.post('https://www.sncf-connect.com/bff/api/v1/itineraries',
                                 headers=headers, json=data)
        Config.update_cookies_from_dict("REAUTHENTICATE", session.cookies.get_dict())

        if response.status_code == 404:
            return False
        elif response.status_code != 200:
            print(BColors.FAIL + 'Error: HTTP', str(response.status_code) + BColors.ENDC)
            if verbosity:
                print(response.text)
            if response.status_code == 403:
                print(response.text)
            sys_exit('Error in the request to get proposal')
        return response

    @staticmethod
    def parse_duration(string):
        hours = 0
        if 'h' in string:
            hours, minutes = string.split('h')
        else:
            minutes = string.split(' min')[0]
        return int(hours) * 60 + int(minutes)

    @staticmethod
    def parse_date(obj: object, year: str):

        date_string = obj['dateLabel'].split(': ')[-1] + ' ' + year + '/' + obj['timeLabel']
        return datetime.strptime(date_string, '%a %d %b %Y/%H:%M')

    @staticmethod
    def parse_proposal(proposal: any) -> 'Proposal':
        """
        Parse JSON proposal and return a Proposal object
        :param proposal: JSON object of the proposal
        :return: proposal object
        """
        duration = Proposal.parse_duration(proposal['durationLabel'])
        min_price = float(proposal['bestPriceLabel'].split(' €')[0].replace(',', '.'))
        departure_year = proposal['travelId'].split('-')[0]
        departure_date = Proposal.parse_date(proposal['departure'], departure_year)
        departure_station = proposal['departure']['originStationLabel']
        arrival_date = Proposal.parse_date(proposal['arrival'], proposal['travelId'].split('-')[0])
        arrival_station = proposal['arrival']['destinationStationLabel']
        second_class_offer = proposal['secondComfortClassOffers']['offers']
        transporter = proposal['timeline']['segments'][0]['transporter']['description']
        vehicle_number = proposal['timeline']['segments'][0]['transporter']['number']
        if transporter == 'INTERCITES DE NUIT':
            # Because Intercites de nuit offers has berths there are parsed differently
            remaining_seats = Proposal.parse_intercites_de_nuit(second_class_offer)
        else:
            if 'bestPriceRemainingSeatsLabel' in proposal and proposal['bestPriceRemainingSeatsLabel'].split(' ')[0].isdigit():
                seats = int(proposal['bestPriceRemainingSeatsLabel'].split(' ')[0])
            else:
                seats = 999
            remaining_seats = {'seats': seats if seats is not None else 999}
            # 999 is a magic number to indicate that there are more than 10 seats

        return Proposal(duration, min_price, departure_date, departure_station, arrival_date,
                        arrival_station, transporter, vehicle_number, remaining_seats)

    @staticmethod
    def get_last_timetable(response: requests.Response) -> str:
        """
        Returns last departure timetable
        :response: response of the request to get proposal
        :return: departure datetime for travelProposals passed in parameter
        """
        return response.json()['longDistance']['proposals']['proposals'][-1]['travelId'].split('_')[
                   0] + ':00'

    def display_seats(self) -> str:
        """
        Returns remaining seats as a string for all physical spaces available,
         which can be seats or berths
        """
        return " and ".join(
            [(str(count) if count < 999 else 'more than 10') + ' ' + physical_space
             for physical_space, count in self.remaining_seats.items()
             ]) + ' remaining'

    @staticmethod
    def display(proposals: ['Proposal'] or None, berth_only: bool = False, long: bool = False):
        """
        Display the proposals in a table
        :param proposals:
        :param berth_only:
        :param long:
        :return:
        """

        if proposals:
            for proposal in proposals:
                if berth_only and proposal.transporter == 'INTERCITES DE NUIT':
                    if 'berths' in proposal.remaining_seats:
                        proposal.print(long=long)
                else:
                    proposal.print(long=long)

    def print(self, long: bool) -> None:
        """
        Prints the proposal object in a human-readable format
        :param long: enable printing of detailed proposals, including transporter and vehicle number
        :return: None
        """
        print(
            f'{BColors.OKGREEN}'
            f'{self.departure_station} ({self.departure_date.strftime("%H:%M")}) → '
            f'{self.arrival_station} ({self.arrival_date.strftime("%H:%M")})',
            f'{self.transporter} {self.vehicle_number}' if long else '',
            f'| {self.display_seats()} ',
            f'{BColors.ENDC}'
        )

    @staticmethod
    def filter(proposals: [any], direct_journey_max_duration: int, get_unavailable: bool = False,
               get_non_tgvmax: bool = False) -> ['Proposal']:
        """
        Filter proposals by duration and price
        :proposals: JSON array of proposals
        :return: list of Proposal objects
        """

        filtered_proposals: [Proposal] = []

        for proposal in proposals:
            if proposal['status'] and proposal['status']['isBookable']:
                proposal_obj = Proposal.parse_proposal(proposal)

                if proposal_obj.min_price == 0:
                    if proposal_obj.duration > direct_journey_max_duration:
                        direct_journey_max_duration = proposal_obj.duration
                    filtered_proposals.append(proposal_obj)
                elif proposal_obj.min_price == 99999:
                    if get_unavailable:
                        filtered_proposals.append(proposal_obj)
                else:
                    if get_non_tgvmax:
                        filtered_proposals.append(proposal_obj)
        return filtered_proposals

    @staticmethod
    def remove_duplicates(all_proposals: ['Proposal'], verbosity: bool = False) -> ['Proposal']:
        """
        Remove proposals with same departure and arrival time in duplicate
        :all_proposals: list of Proposal objects
        :return: list of Proposal objects
        """
        filtered_proposals = []
        removed_count = 0
        for index, proposal in enumerate(all_proposals):
            if index != 0:
                latest_proposal = filtered_proposals[-1]
                if proposal.departure_date != latest_proposal.departure_date and \
                        proposal.arrival_date != latest_proposal.arrival_date:
                    # Do not add duplicate proposals where departure_date and duration are the same
                    filtered_proposals.append(proposal)
                else:
                    removed_count += 1
            else:
                filtered_proposals.append(proposal)
        if verbosity:
            print(f'{removed_count} duplicates removed')
        return filtered_proposals

    def get_remaining_seats(self) -> int:
        """
        Return maximum remaining seats number for all physical spaces available for a proposal
        :return: number of seats
        """
        return max(self.remaining_seats.values())
