""" Taken from https://github.com/maraujop/requests-oauth2 """

from . import OAuth2


class GoogleClient(OAuth2):
    """Google oauth2"""
    site = "https://accounts.google.com"
    authorization_url = "/o/oauth2/auth"
    token_url = "/o/oauth2/token"
    scope_sep = " "


class FacebookClient(OAuth2):
    """Facebook oauth2"""
    site = "https://www.facebook.com/"
    authorization_url = "/dialog/oauth"
    token_url = "/oauth/access_token"
    scope_sep = " "


class InstagramClient(OAuth2):
    """Instagram oauth2"""
    site = "https://api.instagram.com"
    authorization_url = "/oauth/authorize"
    token_url = "/oauth/access_token"
    scope_sep = " "


class EurecomGitLabClient(OAuth2):
    """GitLab oauth2"""
    site = "https://gitlab.eurecom.fr"
    authorization_url = "/oauth/authorize"
    token_url = "/oauth/token"
    userinfo_url = site + '/oauth/userinfo'
    scope_sep = " "
