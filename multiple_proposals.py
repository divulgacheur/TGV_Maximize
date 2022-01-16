from typing import TYPE_CHECKING

from bcolors import BColors
from options import SearchOptions

if TYPE_CHECKING:
    from proposal import Proposal


class MultipleProposals:
    """
    Class that represents a multiple proposal.
    """

    def __init__(self, *proposals: 'Proposal'):
        self.proposals = proposals

    def print(self, opts: SearchOptions) -> None:
        """
        Prints the MultipleProposals object in a human-readable format
        :param opts:
        :return: None
        """

        first = self.proposals[0]
        second = self.proposals[1]

        # For the berth only option, we exclude Intercites de Nuit proposals without a berth
        if opts.berth_only:
            for seg in self.proposals:
                if seg.transporter == 'INTERCITES DE NUIT' and 'berths' not in seg.remaining_seats:
                    return

        print(
            f'{BColors.OKGREEN}'
            f'{first.departure_station.name} '
            f'({first.departure_date.strftime("%H:%M")}) → '
            f'{first.arrival_station.name} ({first.arrival_date.strftime("%H:%M")})',
            f'{first.transporter} {first.vehicle_number}' if opts.long else '',
            f'⭾ {second.departure_station.name} ({second.departure_date.strftime("%H:%M")})'
            if second.departure_station.code != first.arrival_station.code
            else f'⏲  ({second.departure_date.strftime("%H:%M")})',
            # If connection stations are different, i.e. Nimes <-> Nimes Pont du Gard,
            # display the name of two connection stations
            # Else, display only the station name once
            f'→ {second.arrival_station.name} ({second.arrival_date.strftime("%H:%M")})',
            f'{second.transporter} {second.vehicle_number}' if opts.long else '',
            f'| {second.display_seats() if second.get_remaining_seats() < first.get_remaining_seats() else first.display_seats()} ',
            f'{BColors.ENDC}',
        )

    @staticmethod
    def display(segment1, segment2, berth_only: bool = False, long: bool = False) -> None:
        """
        :param segment1: list of proposals for the first segment
        :param segment2: list of proposals for the second segment
        :param berth_only: enable printing only the Intercites de Nuit proposals with a berth
        :param long: enable printing of detailed proposals, with transporter and vehicle number
        :return:
        """
        for proposal_1 in segment1:
            for proposal_2 in segment2:
                if proposal_2.departure_date > proposal_1.arrival_date:
                    MultipleProposals(proposal_1, proposal_2).print(
                        SearchOptions(berth_only=berth_only,
                                      long=long)
                    )
