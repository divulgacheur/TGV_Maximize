"""
Captcha resolver related code
"""
from json import loads
from seleniumwire import webdriver

def resolve(captcha_url: str) -> str:
    """
    Open a browser window the user and navigate to the URL provided.
    Return cookie provided on captcha successfully
    :param captcha_url: url to navigate to
    :return:
    """
    print("A window will be opened with a captcha. Resolve it and come back in the script")
    web_browser = webdriver.Firefox()
    web_browser.get(captcha_url) # Navigate to this url
    print("Press enter if you resolved successfully the captcha. Instead, please exit the script")
    input()
    datadome = None
    for request_sent in web_browser.requests:
        if request_sent.url.startswith('https://geo.captcha-delivery.com/captcha/check'):
            json_datadome = request_sent.response.body
            datadome = loads(json_datadome)
            print(datadome['cookie'].split(';')[0])
    if datadome is not None:
        return datadome['cookie'].split(';')[0]
    raise ValueError('Captcha has not been successfully resolved')
