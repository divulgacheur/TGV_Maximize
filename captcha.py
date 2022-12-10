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
    driver = webdriver.Firefox()
    driver.get(captcha_url)
    print("Press enter if you resolved successfully the captcha. Instead, exit the script")
    input()
    requests_sent = driver.requests
    datadome = None
    for request in requests_sent:
        if request.url.startswith('https://geo.captcha-delivery.com/captcha/check'):
            json_datadome = request.response.body
            datadome = loads(json_datadome)
            print(datadome['cookie'])
    if datadome is not None:
        return datadome['cookie']
    raise ValueError('Captcha has not been successfully resolved')
