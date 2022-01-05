from BColors import BColors
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Proposal import Proposal


class MultipleProposals:
    def __init__(self, *proposals: 'Proposal'):
        self.proposals = proposals

    def print(self, berth_only: bool = False, long: bool = False) -> None:
        first = self.proposals[0]
        second = self.proposals[1]

        if berth_only:
            if first.transporter == 'INTERCITES DE NUIT' and 'berths' not in first.remaining_seats:
                return None
            if second.transporter == 'INTERCITES DE NUIT' and 'berths' not in second.remaining_seats:
                return None

        print(
            f'{BColors.OKGREEN}'
            f'{first.departure_station.name} ' 
            f'({first.departure_date.strftime("%H:%M")}) → '
            f'{first.arrival_station.name} ({first.arrival_date.strftime("%H:%M")})',
            f'{first.transporter} {first.vehicle_number}' if long else None,
            end='')

        # If connection stations are different, i.e. Nimes <-> Nimes Pont du Gard
        if second.departure_station.code != first.arrival_station.code:
            print(f' ⭾ {second.departure_station.name} ({second.departure_date.strftime("%H:%M")})',
                  end='')  # Display the name of two connection stations
        else:
            print(f' ⏲  ({second.departure_date.strftime("%H:%M")})', end='')  # Display only the station name once
        print(
            f' → {second.arrival_station.name} ({second.arrival_date.strftime("%H:%M")})'
            f' {second.transporter} {second.vehicle_number}' if long else None,
            f'| {second.display_seats() if second.get_remaining_seats() < first.get_remaining_seats() else first.display_seats()} '
            f'{BColors.ENDC}'
            )

    @staticmethod
    def display(first_segment, second_segment, berth_only: bool = False, long: bool = False) -> None:
        for first_proposal in first_segment:
            for second_proposal in second_segment:
                if second_proposal.departure_date > first_proposal.arrival_date:
                    MultipleProposals(first_proposal, second_proposal).print(berth_only=berth_only, long=long)
