# -*- coding: utf-8 -*-
"""
Created on Thu Apr  7 13:12:12 2022

@author: jack.ogozaly
"""

#Packages Used
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
from bs4 import BeautifulSoup
import itertools
import requests
from tqdm import tqdm
import pandas as pd
import numpy as np
import re


#pip install python-pptx
from pptx import Presentation
from pptx.util import Inches
from pptx.util import Pt


# Welcome to Mr. Website Roboto, 

#Step 1: Identify some words that you think will be associated with 
#        websites that will need to be changed. 
keywords = ['PPQ 588', 'ePermit', 'PPQ 526', 'PPQ 525', 'PPQ 586', 'PPQ 587', 'PPQ 621', 
            'PPQ 585', 'PPQ 546', 'labels']

keywords = ['PPQ 588', 'ePermit']


#Step 2: Identify some words that if present 100% mean the website needs to be 
#        changed. 
keywords2 = ['epermit', 'epermits']


#Step 3: Run the script and let Mr. Website Roboto find what you're looking for!
print("Beep boop, let me boot up google chrome and get to scraping!")
#Download our chrome driver
driver = webdriver.Chrome(service= Service(ChromeDriverManager().install()))

#Use the search engine on the sight to find relevant links
links_list = []
for i in range(len(keywords)):
    #Navigate to APHIS homepage
    driver.get("https://www.aphis.usda.gov/aphis/home/")
    #Set window size to maximum so we can find the searchbar
    driver.maximize_window()
    #Stop program for 3 seconds just to let stuff load
    time.sleep(1)
    
    #Search for our keywords
    search_bar = driver.find_element(by=By.CSS_SELECTOR, value= "#searchBox")
    search_bar.send_keys(keywords[i])
    search_bar.send_keys(Keys.RETURN)
    
    while True:
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        #Create an empty list for our new links to go into
        links = []
        for link in soup.findAll('a'):
            links.append(link.get('href'))
        links_list.append(tuple(zip(links, [keywords[i] for x in range(len(links))])))
    
        try:
            #driver.find_element_by_class_name("next_page").click()
           driver.find_element(by=By.CLASS_NAME, value="next_page").click()
    
        except:
            break

#Exit out of our driver
driver.quit()

#Combine all the lists together
merged = list(itertools.chain(*links_list))
merged = [item for item in merged if item[0].startswith('https')]

#Find URLs that link to a pdf
pdf_links = [item for item in merged if item[0].endswith('pdf')]
#Find URLs that link to an excel sheet
excel_links = [item for item in merged if item[0].endswith('xlsx')]

#Filter out pdf and excel links, and create a list of clean urls to comb through
z = pdf_links + excel_links
web_links = [item for item in merged if item not in z]
links_to_search = [i[0] for i in web_links]
links_to_search = list(set(links_to_search))


#Convert keywords to search for to lowercase
for i in range(len(keywords2)):
    keywords2[i] = keywords2[i].lower()

#%%

#Create empty list for us to put the final links into
links_to_fix = []

print("Beep boop, now to search the links for your keywords")
#Go to every website we previously got, and search for the keywords
for i in tqdm(range(len(links_to_search))):
  URL= links_to_search[i]
  page = requests.get(URL)
  soup = BeautifulSoup(page.content, 'html.parser')
  text = soup.get_text().lower().strip()
  if any(word in text for word in keywords2):
      links_to_fix.append(URL)
      

print("Now I'm going to look through the links for any offending URLs")
#Go through the links and see if they link to other offending sites
df_list = []
for i in tqdm(range(len(links_to_search))):
    URL= links_to_search[i]
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    links = []
    for link in soup.findAll('a'):
       links.append(link.get('href'))
       
    links = list(filter(None, links))
    
    #Search the list of links to see if any of them mention epermits
    s = pd.Series(links, dtype = 'object')
    s = s.astype(str)
    s = s.str.lower()
    s = s[s.str.contains('|'.join(keywords2))]
    if s.empty:
        continue
    else: 
        df = pd.DataFrame({'Offending_Link' : s, 'Parent_URL': URL})
        df = df.drop_duplicates()
        df_list.append(df)

df = pd.concat(df_list)
df['Offending_Link'] = np.where(df['Offending_Link'].str.startswith('https'), 
                                df['Offending_Link'], 
                                'https://www.aphis.usda.gov/' + df['Offending_Link'])


#Find all links to search through
links_to_fix = links_to_fix + list(df['Offending_Link'].unique())
links_to_fix = list(set(links_to_fix))

#%%

print("Now to see where exactly it's saying your keywords")
#Go through the links that mention epermits and see if it's because of the banner or some other reason
why_it_needs_revision = []
for i in tqdm(range(len(links_to_fix))):
    URL= links_to_fix[i]
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    text = soup.get_text().lower().strip()
        
    #Find the offending pattern
    pattern = re.compile(r'\b(?:%s)\b' % '|'.join(keywords2), re.IGNORECASE)
    
    if soup.find(text=pattern) is not None:
        dictionary = soup.find(text=pattern).__dict__
        
        if str(dictionary['parent']) == '''<a href="/aphis/resources/permits" role="menuitem" tabindex="-1">Permits (ePermits and eFile)</a>''':
            why_it_needs_revision.append("Banner")
        else:
            why_it_needs_revision.append("TBD")
    else: 
        why_it_needs_revision.append("Unsure")


#%%




print("Now to see where exactly it's saying your keywords")
#Go through the links that mention epermits and see if it's because of the banner or some other reason
why_it_needs_revision = []
for i in tqdm(range(len(links_to_fix))):
    URL= links_to_fix[i]
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    text = soup.get_text().lower().strip()
        
    #Find the offending pattern
    pattern = re.compile(r'\b(?:%s)\b' % '|'.join(keywords2), re.IGNORECASE)
    
    try:
        searched_text = soup.find_all(text=pattern)
        
        if searched_text[0] == "Permits (ePermits and eFile)" and len(searched_text) == 1:
            why_it_needs_revision.append("Banner")
        else: 
            why_it_needs_revision.append("TBD")
    except: 
        why_it_needs_revision.append("Unsure")
        
        


all_links_to_change = pd.DataFrame({'Offending_Link': links_to_fix,
                                    'What_To_Fix': why_it_needs_revision})






#%%

URL= 'https://www.aphis.usda.gov//aphis/resources/sa_epermits/eauth-epermits'
page = requests.get(URL)
soup = BeautifulSoup(page.content, 'html.parser')
text = soup.get_text().lower().strip()
    
#Find the offending pattern
pattern = re.compile(r'\b(?:%s)\b' % '|'.join(keywords2), re.IGNORECASE)
dictionary = soup.find_all(text=pattern).__dict__


#print(soup.find_all(text=pattern))


img = soup.find_all(text=pattern)

for imgs in img:
    print(imgs)


if img[0] == "Permits (ePermits and eFile)" and len(img) == 1:
    print("hello")
else: 
    print("nah")



#%%

print(img.parent)

#%%
print(str(dictionary['parent']))



#%%

all_links_to_change = pd.DataFrame({'Offending_Link': links_to_fix,
                                    'What_To_Fix': why_it_needs_revision})




#%%


all_links_to_change = pd.concat([all_links_to_change, df])



X = Presentation()
Layout = X.slide_layouts[0] 
first_slide = X.slides.add_slide(Layout)
first_slide.shapes.title.text = "Website Text Changes"
first_slide.placeholders[1].text = "Created by Mr. Website Roboto"

driver = webdriver.Chrome(service= Service(ChromeDriverManager().install()))

for i in range(20): 
    
    driver.get(links_to_fix[i])
    screenshot = driver.save_screenshot('my_screenshot.png')
    
    Second_Layout = X.slide_layouts[6]
    second_slide = X.slides.add_slide(Second_Layout)
    
    #Add in URL text
    textbox = second_slide.shapes.add_textbox(Inches(10), Inches(1),Inches(3), Inches(1)) 
    textframe = textbox.text_frame
    textframe.word_wrap = True
    paragraph = textframe.add_paragraph()
    paragraph.text = 'URL: ' + links_to_fix[i]
    paragraph.font.size = Pt(12.5)
    
    
    pic = second_slide.shapes.add_picture('my_screenshot.png', left= Inches(2), top= Inches(0),
                                          width=Inches(6), height=Inches(7.8))



X.save("First_presentation.pptx")


#%%

import re

for i in range(60):
    URL= links_to_fix[i]
    print(i)
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    text = soup.get_text().lower().strip()
    
    
    #pattern = re.compile(r'epermit',  re.IGNORECASE)
    
    pattern = re.compile(r'\b(?:%s)\b' % '|'.join(keywords2), re.IGNORECASE)
    
    
    dictionary = soup.find(text=pattern).__dict__
    print(dictionary['parent'])


#%%