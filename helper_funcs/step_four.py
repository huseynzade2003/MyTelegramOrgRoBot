import random
import requests


def create_new_tg_app(
        stel_token,
        tg_app_hash,
        app_title,
        app_shortname,
        app_url,
        app_platform,
        app_desc
):

    """ yeni bir my.telegram.org/apps yaradır
    təqdim olunan parametrlərdən istifadə etmək """
    request_url = "https://my.telegram.org/apps/create"
    custom_header = {
        "Cookie": stel_token
    }
    request_data = {
        "hash": tg_app_hash,
        "app_title": app_title,
        "app_shortname": app_shortname,
        "app_url": app_url,
        "app_platform": random.choice(app_platform),
        "app_desc": app_desc
    }
    response_c = requests.post(
        request_url,
        data=request_data,
        headers=custom_header
    )
    return response_c
