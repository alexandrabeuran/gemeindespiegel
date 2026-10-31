class SourceError(Exception):
    """Source data is unreachable or invalid; the import must stop.

    The message is shown to the user as is, so it names the source and the
    offending municipality or grid operator.
    """


class ConfigError(Exception):
    """A setting is missing or invalid; the job stops before fetching anything."""
