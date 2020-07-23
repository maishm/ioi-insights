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
import itertools
from dateutil.parser import parse

def get_post_content(url):     
    driver = webdriver.Chrome('chromedriver.exe')
    driver.get(url)
    total_pages = int(re.findall('\d+', driver.find_element_by_xpath("""/html/body/div[2]/table[1]/tbody/tr/td/div[2]/div/span[1]/a""").text)[0])
    # total_pages = 2
    current_page = int(driver.find_element_by_class_name("pagecurrent").text)
    POST_CONTENT = []
    USERNAME = []
    POSTED_AT = []
    while total_pages > current_page:
        driver.execute_script("[...document.querySelectorAll('.quotemain')].map(el => el.parentNode.removeChild(el))")
        driver.execute_script("[...document.querySelectorAll('.quotetop')].map(el => el.parentNode.removeChild(el))")
        driver.execute_script("[...document.querySelectorAll('.edit')].map(el => el.parentNode.removeChild(el))")
        thread_name = [e.text for e in driver.find_elements_by_xpath("//body/div[2]/div[7]/div[1]/p[2]/b")]
        post_content = [e.text for e in driver.find_elements_by_xpath("""//*[contains(@class, "postcolor post_text")]""")]
        for i in range(len(post_content)):
            POST_CONTENT.append(post_content[i])
        username = [e.text for e in driver.find_elements_by_xpath("""//*[contains(@class, "normalname")]""")]
        for i in range(len(username)):
            USERNAME.append(username[i])
        for i in range(1,20): 
            POSTED_AT.append([e.text for e in driver.find_elements_by_xpath(f"""//div[2]/div[7]/table[{i}]/tbody/tr[1]/td[2]/div[1]/span""")])
        driver.find_element_by_xpath('//*[@title="Next page"]').click()
        current_page += 1
    THREAD_NAME = list(itertools.repeat(thread_name[0], len(USERNAME)))
    zipped_list = zip(THREAD_NAME, USERNAME, POST_CONTENT, POSTED_AT)
    df = pd.DataFrame(zipped_list, columns=['thread_name', 'username', 'post_content', 'posted_at'])
    df['post_content'] = df['post_content'].apply(lambda x: x.replace('\n', ''))
    df['posted_at'] = df['posted_at'].apply(lambda x: x[0]) 
    df['thread_name'] = df['thread_name'].apply(lambda x: re.sub("[\(\[].*?[\)\]]", "", x))
    df.to_csv(f"data/post_data/{df['thread_name'][0]}.csv")
    return print(f"Successfully scraped {len(df)} rows of post data for {df['thread_name'][0]}.")


