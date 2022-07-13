from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
from datetime import timedelta
import re
import random
import string
import json
from datetime import datetime as dt

UNITS = {'s':'seconds', 'm':'minutes', 'h':'hours', 'd':'days', 'w':'weeks'}
def convert_to_minute(s):
    return int(timedelta(**{
        UNITS.get(m.group('unit').lower(), 'seconds'): float(m.group('val'))
        for m in re.finditer(r'(?P<val>\d+(\.\d+)?)(?P<unit>[smhdw]?)', s, flags=re.I)
    }).total_seconds()/60)


def city_to_airport(city):
    airport_code=pd.read_excel("src/airportcodes.xlsx")
    airport_code["City"]=airport_code["City"].str.lower()
    lst = airport_code["City"].to_list()
    i=0
    code=[]
    for x in lst:
        i += 1 
        if city.lower() in x:
            code.append(airport_code["Code"][i-1])
    return code

def low(x):
    return x.lower()

def search_flight_round(origin,destination,startdate,returndate,sort=None):

    if sort == None:
        url = "https://www.momondo.com/flight-search/" + origin + "-" + destination + "/" + startdate + "/" + returndate+"?sort=bestflight_a"
    elif sort == "cheapest":
        url = "https://www.momondo.com/flight-search/" + origin + "-" + destination + "/" + startdate + "/" + returndate+"?sort=price_a"
    elif sort == "duration":
        url = "https://www.momondo.com/flight-search/" + origin + "-" + destination + "/" + startdate + "/" + returndate+"?sort=duration_a"

    options = Options()
    options.headless = False

    driver = webdriver.Firefox(executable_path="/Users/aliakay/Documents/geckodriver",options=options)
    driver.implicitly_wait(40)
    driver.get(url)
    print(url)
    soup=BeautifulSoup(driver.page_source, 'lxml')
    driver.close()

    regex_airline = re.compile("mainInfo")
    airline_list = soup.find_all('div', attrs={'class': regex_airline})

    list1=[]
    for div in airline_list:
        list1=list(filter(None, div.getText().split('\n')))

    print(list1)
    if len(list1)>0:
        message = ' '.join(word for word in list1)
    else:
        message=""
    regex = re.compile("price-text")
    price_list = soup.find_all('span', attrs={'class': regex})
    price = []
    for div in price_list:
        price.append(div.getText().split('\n')[1])

    if len(price)>0:
        price_message=price[0]
    else:
        price_message=""

    message = message + "-------> " + price_message
    return message


def search_flight(origin,destination,startdate,sort=None):

    if sort == None:
        url = "https://www.momondo.com/flight-search/" + origin + "-" + destination + "/" + startdate + "/" +"?sort=bestflight_a"
    elif sort == "cheapest":
        url = "https://www.momondo.com/flight-search/" + origin + "-" + destination + "/" + startdate + "/" +"?sort=price_a"
    elif sort == "duration":
        url = "https://www.momondo.com/flight-search/" + origin + "-" + destination + "/" + startdate + "/" +"?sort=duration_a"

    options = Options()
    options.headless = False

    driver = webdriver.Firefox(executable_path="/Users/aliakay/Documents/geckodriver",options=options)
    driver.implicitly_wait(40)
    driver.get(url)
    print(url)
    soup=BeautifulSoup(driver.page_source, 'lxml')
    driver.close()
    regex_airline = re.compile("mainInfo")
    airline_list = soup.find_all('div', attrs={'class': regex_airline})
    list1=[]
    for div in airline_list:
        list1=list(filter(None, div.getText().split('\n')))

    print(list1)
    if len(list1)>0:
        message = ' '.join(word for word in list1)
    else:
        message=""
    regex = re.compile("price-text")
    price_list = soup.find_all('span', attrs={'class': regex})
    price = []
    for div in price_list:
        price.append(div.getText().split('\n')[1])

    if len(price)>0:
        price_message=price[0]
    else:
        price_message= ""

    print(message)
    message = message + "-------> " + price_message
    
    return message

def random_char(y):
        word=[''.join(random.choice(string.ascii_letters) for x in range(y))]
        numbers=["{}".format(random.randint(0,9)) for i in range(3)]
        numbers=''.join(numbers)
        PNR=word[0].upper()+numbers
        return PNR
