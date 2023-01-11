from typing import TYPE_CHECKING

from proposal import console
from options import SearchOptions

if TYPE_CHECKING:
    from proposal import Proposal


class MultipleProposals:
    """
    Class that represents a multiple proposal.
    """

    def __init__(self, *proposals: 'Proposal'):
        self.proposals = proposals

    def print(self, opts: SearchOptions, color = True) -> None:
        """
        Prints the MultipleProposals object in a human-readable format
        :param opts:
        :param color: Allow alternating background color on every other line
        :return: None
        """

        first = self.proposals[0]
        second = self.proposals[1]

        # For the berth only option, we exclude Intercites de Nuit proposals without a berth
        if opts.berth_only:
            for seg in self.proposals:
                if seg.transporter == 'INTERCITES DE NUIT' and 'berths' not in seg.remaining_seats:
                    return
        style = " on rgb(0,83,167)" if color else " on rgb(4,39,112)"
        console.print(f'{first.departure_station.display_name.center(23)} ', style='default'+style, end='')
        console.print(f'{first.departure_date.strftime("%H:%M")}',style='bold yellow'+style, highlight=False, end='')
        console.print(f' → {first.arrival_station.display_name.center(23)}', style='default'+style, end='' )
        console.print(f' {first.arrival_date.strftime("%H:%M")} ', style='bold yellow'+style, highlight=False, end='')
        console.print(f' {first.transporter.center(10)} {first.vehicle_number.center(5)}' if opts.long else '' , style='default'+style, end='')

        # If connection stations are different, i.e. Nimes <-> Nimes Pont du Gard,
        # display the name of two connection stations
        # Else, display only the station name once
        if second.departure_station.display_name != first.arrival_station.display_name:
            console.print(f' ⭾ {second.departure_station.display_name.center(23)}', style='default'+style, end='')
            console.print(f' {second.departure_date.strftime("%H:%M")}', style='bold yellow'+style, highlight=False, end='')
        else:
            console.print(f' ⏲  {second.departure_date.strftime("%H:%M")}', style='bold yellow'+style, highlight=False, end='')

        console.print(f' → {second.arrival_station.display_name.center(23)} ', style='default'+style, end='' )
        console.print(f'{second.arrival_date.strftime("%H:%M")} ', style='bold yellow'+style, highlight=False, end='')
        console.print(
            f' {second.transporter.center(10)} {second.vehicle_number.center(5)}' if opts.long else '',
            f'| {second.display_seats() if second.get_remaining_seats() < first.get_remaining_seats() else first.display_seats()} ', style='default'+style
        )

    @staticmethod
    def display(segment1, segment2, berth_only: bool = False, long: bool = False, verbosity: bool = False) -> None:
        """
        :param segment1: list of proposals for the first segment
        :param segment2: list of proposals for the second segment
        :param berth_only: enable printing only the Intercites de Nuit proposals with a berth
        :param verbosity: enable more detailed printing
        :param long: enable printing of detailed proposals, with transporter and vehicle number
        :return:
        """
        background = True
        proposal_found = False
        for proposal_1 in segment1:
            for proposal_2 in segment2:
                if proposal_2.departure_date > proposal_1.arrival_date:
                    if not proposal_found and verbosity:
                        print("Segments 1 & 2 combined :")
                    MultipleProposals(proposal_1, proposal_2).print(
                        SearchOptions(berth_only=berth_only, long=long),  color=background)
                    proposal_found = True
                    if background:
                        background = False
                    else:
                        background = True
        if not proposal_found and verbosity:
            print("Connection is physically impossible between available proposals")
