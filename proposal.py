from datetime import datetime
from json import dumps as json_dumps
from sys import exit as sys_exit
import requests

from BColors import BColors
from Station import Station
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

    def __init__(self, duration, min_price, departure_date, departure_station, arrival_date, arrival_station,
                 transporter, vehicle_number, remaining_seats):
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
    def parse_intercites_de_nuit_offers(second_class_offers: any) -> dict:
        """
        Parse Intercités de nuit offers to get exact number of seats and berths
        :param second_class_offers: JSON object of the offers
        :return: dict with seats and berths
        """
        remaining_seats = {}
        for offer in second_class_offers['offers']:
            if offer['amount'] == 0:
                placement_modes = offer['offerSegments'][0]['placement']['availablePlacementModes']
                if placement_modes[1]['availablePhysicalSpaces'][0]['linkedOfferKey'] is None:  # BERTH_SECOND
                    # if there is no linked offer, the berth offer is this one
                    remaining_seats['berths'] = offer['remainingSeats'] if offer['remainingSeats'] is not None else 999
                    # if remainingSeats is not set, it means there is no limit
                    # 999 is a magic number, it means that there are more than 10 berths available
                elif placement_modes[2]['availablePhysicalSpaces'][0]['linkedOfferKey'] is None:  # SEAT_SECOND
                    # if there is no linked offer, the seat offer is this one
                    remaining_seats['seats'] = offer['remainingSeats'] if offer['remainingSeats'] is not None else 999
        return remaining_seats

    @staticmethod
    def get_next(departure_station, arrival_station, departure_date, verbosity) -> requests.Response:
        """
        Get next proposal response from oui.sncf API
        :param departure_station: departure station code (5 letters)
        :param arrival_station: arrival station code (5 letters)
        :param departure_date: departure date (YYYY-MM-DDTHH:MM:SS)
        :param verbosity: enable verbosity
        :return: JSON response of the request
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.oui.sncf/proposition/outward/train?wishId=95edb29e-9529-4e54-9645-01d0040da16d',
            'content-type': 'application/json',
            'x-client-app-id': 'VSD',
            'x-client-channel': 'web',
            'x-market-locale': 'fr_FR',
            'x-vsd-locale': 'fr_FR',
            'X-INSTANA-L': '1,correlationType=web;correlationId=afc550728eb5e772',
            'Origin': 'https://www.oui.sncf',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'TE': 'trailers',
            'Cookie': Config.OUISNCF_COOKIE
        }
        data = {'context': {'features': [], 'paginationContext': {'travelSchedule': {'departureDate': departure_date}}},
                'wish': {'id': '8938068f-7816-4ee3-8176-1c35e6a81245',
                         'mainJourney': {'origin': {'codes': {'RESARAIL': {'code': departure_station}}},
                                         'destination': {'codes': {'RESARAIL': {'code': arrival_station}}},
                                         'via': None},
                         'directTravel': True,
                         'schedule': {'outward': departure_date, 'outwardType': 'DEPARTURE_FROM', 'inward': None,
                                      'inwardType': 'DEPARTURE_FROM'}, 'travelClass': 'SECOND',
                         'passengers': [{'id': '0', 'typology': 'YOUNG', 'firstname': '', 'lastname': '',
                                         'dateOfBirth': Config.BIRTH_DATE, 'age': 21,
                                         'discountCards': [{'code': 'HAPPY_CARD', 'number': Config.TGVMAX_CARD_NUMBER,
                                                            'dateOfBirth': Config.BIRTH_DATE}],
                                         'bicycle': None}],
                         'checkBestPrices': False, 'salesMarket': 'fr-FR',
                         'channel': 'web', 'pets': [], 'context': {'sumoForTrain': {'eligible': True}}
                         }
                }

        response = requests.post('https://www.oui.sncf/api/vsd/travels/outward/train/next', headers=headers,
                                 data=json_dumps(data))
        if response.status_code != 200:
            print(BColors.FAIL + 'Error: HTTP', str(response.status_code) + BColors.ENDC)
            if verbosity:
                print(response.text)
            if response.status_code == 403:
                print(
                    'Too many requests. Resolve captcha at https://oui.sncf/billet-train and recover your new cookies')
            sys_exit('Error in the request to get proposal')
        return response

    @staticmethod
    def parse_proposal(proposal: any) -> 'Proposal':
        """
        Parse JSON proposal and return a Proposal object
        :param proposal: JSON object of the proposal
        :return: proposal object
        """
        duration = proposal['duration'] / 60
        min_price = proposal['minPrice']
        departure_date = datetime.strptime(proposal['departureDate'], '%Y-%m-%dT%H:%M:00')
        departure_station = Station(str.lower(proposal['origin']['station']['label']),
                                    proposal['origin']['latitude'],
                                    proposal['origin']['longitude'],
                                    code=proposal['origin']['station']['metaData']['PAO']['code'],
                                    )
        arrival_date = datetime.strptime(proposal['arrivalDate'], '%Y-%m-%dT%H:%M:00')
        arrival_station = Station(str.lower(proposal['destination']['station']['label']),
                                  proposal['destination']['latitude'],
                                  proposal['destination']['longitude'],
                                  code=proposal['destination']['station']['metaData']['PAO']['code'],
                                  )
        transporter = proposal['secondClassOffers']['offers'][0]['offerSegments'][0]['transporter']
        vehicle_number = proposal['secondClassOffers']['offers'][0]['offerSegments'][0]['vehicleNumber']
        if transporter == 'INTERCITES DE NUIT':  # Intercites de nuit offers are parsed differently than other offers
            remaining_seats = Proposal.parse_intercites_de_nuit_offers(proposal['secondClassOffers'])
        else:
            seats = proposal['secondClassOffers']['offers'][0]['remainingSeats']
            remaining_seats = {'seats': seats if seats is not None else 999}

        return Proposal(duration, min_price, departure_date, departure_station, arrival_date, arrival_station,
                        transporter, vehicle_number, remaining_seats)

    @staticmethod
    def get_last_timetable(response: requests.Response) -> str:
        """
        Returns last departure timetable
        :response: response of the request to get proposal
        :return: departure datetime for travelProposals passed in parameter
        """
        return response.json()['travelProposals'][-1]['departureDate']

    def display_seats(self) -> str:
        """
        Returns remaining seats as a string for all physical spaces available, which can be seats or berths
        """
        return " and ".join(
            [(str(count) if count < 999 else 'more than 10') + ' ' + physical_space
             for physical_space, count in self.remaining_seats.items()
             ]) + ' remaining'

    def print(self, long: bool) -> None:
        """
        Prints the proposal object in a human-readable format
        :param long: enable printing of detailed proposals, including the transporter and the vehicle number
        :return: None
        """
        print(
            f'{BColors.OKGREEN}'
            f'{self.departure_station.name}' f' ({self.departure_date.strftime("%H:%M")}) → '
            f'{self.arrival_station.name} ({self.arrival_date.strftime("%H:%M")})',
            f'{self.transporter} {self.vehicle_number}' if long else '',
            f'| {self.display_seats()} ',
            f'{BColors.ENDC}'
        )

    @staticmethod
    def filter_proposals(proposals: list[any], direct_journey_max_duration: int, get_unavailable: bool = False,
                         get_non_tgvmax: bool = False) -> list['Proposal']:
        """
        Filter proposals by duration and price
        :proposals: JSON array of proposals
        :return: list of Proposal objects
        """

        filtered_proposals: list[Proposal] = []

        for proposal in proposals:
            if proposal['secondClassOffers'] and proposal['secondClassOffers']['offers']:
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
    def remove_duplicates(all_proposals: list['Proposal'], verbosity: bool = False) -> list['Proposal']:
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
