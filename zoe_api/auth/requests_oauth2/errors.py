""" Taken from https://github.com/maraujop/requests-oauth2 """


class OAuth2Error(Exception):
    """OAuth error."""
    pass


class ConfigurationError(OAuth2Error):
    """OAuth configuration error."""
    pass
