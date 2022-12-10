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
        'authority': 'www.sncf-connect.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'fr-FR,fr;q=0.7',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'https://www.sncf-connect.com',
        'pragma': 'no-cache',
        'referer': 'https://www.sncf-connect.com/app/home/shop/results/outward',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'x-api-env': 'production',
        'x-app-version': '20221126.0.0-2022112600-4bb6b49271',
        'x-bff-key': 'ah1MPO-izehIHD-QZZ9y88n-kku876',
        'x-market-locale': 'fr_FR',
        'cookie': Config.SNCFCONNECT_COOKIE,
        }

        data = {
            'schedule': {
                'outward': {
                    'date': dpt_date,
                    'arrivalAt': False,
                },
            },
            'mainJourney': {
                'origin': {
                    'label': 'Do not remove',
                    'id': 'RESARAIL_STA_' + dpt_station,
                    'geolocation': False,
                },
                'destination': {
                    'label': 'Do not remove',
                    'id': 'RESARAIL_STA_' + arr_station,
                    'geolocation': False,
                },
            },
            'passengers': [
                {
                    'id': '67161bc1-0e7a-40c8-8ff6-f66efaa77242',
                    'customerId': '100025623302',
                    'dateOfBirth': Config.BIRTH_DATE,
                    'discountCards': [
                        {
                            'code': 'TGV_MAX',
                            'number': Config.TGVMAX_CARD_NUMBER,
                            'label': 'MAX JEUNE',
                        },
                    ],
                    'typology': 'YOUNG',
                    'displayName': '',
                    'firstName': '',
                    'lastName': '',
                    'initials': '',
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

        response = requests.post('https://www.sncf-connect.com/bff/api/v1/itineraries',
                                 headers=headers, json=data)
        if response.status_code != 200:
            print(BColors.FAIL + 'Error: HTTP', str(response.status_code) + BColors.ENDC)
            if verbosity:
                print(response.text)
            if response.status_code == 403:
                print('Too many requests. Resolve captcha at '
                      'https://oui.sncf/billet-train and recover your new cookies')

                datadome_cookie = captcha.resolve(response.json()['url'])
                Config.update_cookies_from_dict("SNCFCONNECT_COOKIE", datadome_cookie)

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
    def parse_date(obj: any, year: str):
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
            [(str(count) if count < 999 else '+10') + ' ' + physical_space
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
