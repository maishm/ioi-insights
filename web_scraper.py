from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import time
import datetime
from dateutil.parser import parse

def get_forum_data(total_pages):  
    """Scrapes relevant property data from lowayat property talk. Specify pages you want to scrape.  
    If you want to scrape all pages, use total_pages = 'max'. 
    """
    driver = webdriver.Chrome('chromedriver.exe')
    driver.get('https://forum.lowyat.net/index.php?showforum=154&tag=Investment%2CHousehold')

    NAME = []
    REPLIES = []
    VIEWS = []
    LAST_POSTED_AT = []

    if total_pages == 'max':
        total_pages = int(re.findall('\d+', driver.find_element_by_xpath("""//*[@id="ipbwrapper"]/font/font/table[1]/tbody/tr/td/div[2]/span[1]/a""").text)[0])
    else: 
        total_pages = total_pages

    current_page = int(driver.find_element_by_class_name("pagecurrent").text)

    while total_pages > current_page:
        for i in range(6,30):
            name = driver.find_element_by_xpath(f'//div[2]/font/font/div[3]/table/tbody/tr[{i}]/td[3]/div/div[1]/a[1]')
            replies = driver.find_element_by_xpath(f'//div[2]/font/font/div[3]/table/tbody/tr[{i}]/td[4]/a')
            views = driver.find_element_by_xpath(f'//div[2]/font/font/div[3]/table/tbody/tr[{i}]/td[6]')
            last_posted_at = driver.find_element_by_xpath(f'//div[2]/font/font/div[3]/table/tbody/tr[{i}]/td[7]/span[1]')
            NAME.append(name.text)
            REPLIES.append(replies.text)
            VIEWS.append(views.text)
            LAST_POSTED_AT.append(last_posted_at.text.splitlines()[0])
        driver.find_element_by_xpath('//*[@title="Next page"]').click()
        current_page += 1 

    zipped_list = zip(NAME, REPLIES, VIEWS, LAST_POSTED_AT) 
    df = pd.DataFrame(data=zipped_list, columns=['name', 'replies','views','last_posted_at'])
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    for i in range(len(df)): 
        try: 
            df['last_posted_at'][i] = pd.to_datetime(df['last_posted_at'][i])
        except:
            if "Today" in str(df['last_posted_at'][i]): 
                df['last_posted_at'][i] = today
            elif "Yesterday" in str(df['last_posted_at'][i]): 
                df['last_posted_at'][i] = yesterday

    df.to_csv('data/forum_data.csv') 
    
    def clean_forum_data(df):
        df['name'] = df['name'].apply(lambda x: re.sub("[\(\[].*?[\)\]]", "", x))
        df['len_name'] = df['name'].apply(lambda x: len(x))
        df = df[df['len_name'] > 8]
        df['weird_characters'] = df['name'].apply(lambda x: "?" in x or "<" in x or "!" in x)
        df = df[df['weird_characters'] == False]
        df.dropna(subset = ["name"], inplace=True)
        df.to_csv('data/clean_forum_data.csv')
    
    clean_forum_data(df)
    
    return print(f"Successfully scraped and cleaned {len(df)} rows of data.")

