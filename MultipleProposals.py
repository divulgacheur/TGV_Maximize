from BColors import BColors
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Proposal import Proposal


class MultipleProposals:
    def __init__(self, *proposals: 'Proposal'):
        self.proposals = proposals

    def display(self) -> None:
        first = self.proposals[0]
        second = self.proposals[1]

        print(
            f'{BColors.OKGREEN}'
            f'{first.departure_station.name}' 
            f'({first.departure_date.strftime("%H:%M")}) → '
            f'{first.arrival_station.name} ({first.arrival_date.strftime("%H:%M")}) ', end='')

        # If connections stations are different, i.e. Nimes <-> Nimes Pont du Gard
        if second.departure_station.code != first.arrival_station.code:
            print(f' ⭾ {second.departure_station.name} ({second.departure_date.strftime("%H:%M")}) ',
                  end='')  # Display the name of two connection stations
        else:
            print(f'({second.departure_date.strftime("%H:%M")}) ', end='')  # If not, display only the station name once
        print(
            f'→ {second.arrival_station.name} ({second.arrival_date.strftime("%H:%M")}) '
            f'| {second.display_seats() if second.remaining_seats < first.remaining_seats else first.display_seats()} '
            f'{BColors.ENDC}'
            )
