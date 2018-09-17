""" Taken from https://github.com/maraujop/requests-oauth2 """


class OAuth2Error(Exception):
    pass


class ConfigurationError(OAuth2Error):
    pass
