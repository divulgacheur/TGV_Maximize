from datetime import datetime

import requests

from BColors import BColors
from Station import Station


class Proposal:
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
        self.minPrice = min_price
        self.departure_date = departure_date
        self.departure_station = departure_station
        self.arrival_date = arrival_date
        self.arrival_station = arrival_station
        self.transporter = transporter
        self.vehicle_number = vehicle_number
        self.remaining_seats = remaining_seats

    @staticmethod
    def parse_intercites_de_nuit_offers(second_class_offers: any) -> dict:
        remaining_seats = {}
        for offer in second_class_offers['offers']:
            if offer['amount'] == 0:
                placement_modes = offer['offerSegments'][0]['placement']['availablePlacementModes']
                if placement_modes[1]['availablePhysicalSpaces'][0]['linkedOfferKey'] is None:  # BERTH_SECOND
                    remaining_seats['berths'] = offer['remainingSeats'] if offer['remainingSeats'] is not None else 999
                elif placement_modes[2]['availablePhysicalSpaces'][0]['linkedOfferKey'] is None:  # SEAT_SECOND
                    remaining_seats['seats'] = offer['remainingSeats'] if offer['remainingSeats'] is not None else 999
        return remaining_seats

    @staticmethod
    def parse_proposal(proposal: any):
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
    def get_last_timetable(response: requests.Response):
        """
        Returns last departure timetable
        :response term: Search term
        :return: departure datetime for travelProposals passed in parameter
        """
        return response.json()['travelProposals'][-1]['departureDate']

    def display_seats(self) -> str:
        return " ".join(
            [(str(count) if count < 999 else 'more than 10') + ' ' + physical_space + ' remaining'
             for physical_space, count in self.remaining_seats.items()
             ])

    def print(self) -> None:
        """
        Print journey proposal, date, location, train information & price
        :proposal: Proposal
        :return: None
        """
        print(
            f'{BColors.OKGREEN}'
            f'{self.departure_station.name}' f' ({self.departure_date.strftime("%H:%M")}) → '
            f'{self.arrival_station.name} ({self.arrival_date.strftime("%H:%M")}) '
            f'{self.transporter} '
            f'{self.vehicle_number}',
            f'{self.display_seats()} '
            f'{BColors.ENDC}'
        )

    @staticmethod
    def filter_proposals(proposals: list[any], direct_journey_max_duration: int, get_unavailable: bool = False,
                         get_non_tgvmax: bool = False):

        filtered_proposals: list[Proposal] = []

        for proposal in proposals:
            if proposal['secondClassOffers'] and proposal['secondClassOffers']['offers']:
                proposal_obj = Proposal.parse_proposal(proposal)

                if proposal_obj.minPrice == 0:
                    if proposal_obj.duration > direct_journey_max_duration:
                        direct_journey_max_duration = proposal_obj.duration
                    filtered_proposals.append(proposal_obj)
                elif proposal_obj.minPrice == 99999:
                    if get_unavailable:
                        filtered_proposals.append(proposal_obj)
                else:
                    if get_non_tgvmax:
                        filtered_proposals.append(proposal_obj)
        return filtered_proposals

    @staticmethod
    def remove_duplicates(all_proposals, verbosity):
        filtered_proposals = []
        removed_count = 0
        for index, proposal in enumerate(all_proposals):
            if index != 0:
                latest_proposal = all_proposals[index - 1]
                if proposal.departure_date != latest_proposal.departure_date and \
                        proposal.duration != latest_proposal.duration:
                    # Do not add duplicate proposals where departure_date and duration are the same
                    filtered_proposals.append(proposal)
                else:
                    removed_count += 1
            else:
                filtered_proposals.append(proposal)
        print(removed_count, 'duplicates removed') if verbosity else None
        return filtered_proposals

    def get_remaining_seats(self) -> int:
        """
        Return remaining seats count for a proposal that can contain multiple physical spaces
        """
        return max(self.remaining_seats.keys())
