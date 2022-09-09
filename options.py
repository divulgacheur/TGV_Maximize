class SearchOptions:
    """
    Class to define options for searching
    """
    via: str
    berth_only: bool = False
    long: bool = False
    direct_only: bool = False
    max_duration: int

    def __init__(self, via=None, max_duration=None, berth_only=False, long=False,
                 direct_only=False, verbosity=False, quiet=False, debug = False) -> None:
        self.via = via
        self.berth_only = berth_only
        self.long = long
        self.direct_only = direct_only
        self.max_duration = max_duration
        self.verbosity = verbosity
        self.quiet = quiet
        self.debug = debug


class PromptOptions:
    """
    Class to define options for prompting
    """

    verbosity: bool
    quiet: bool
    debug: bool

    def __init__(self, verbosity, quiet, debug):
        self.verbosity = verbosity
        self.quiet = quiet
        self.debug = debug
