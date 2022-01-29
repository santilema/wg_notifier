import numpy as np
import pandas as pd
import requests
import bs4
import re
import telegram_send

#Filtered website with renting offers.
res = requests.get('https://www.wg-gesucht.de/1-zimmer-wohnungen-und-wohnungen-und-haeuser-in-Passau.104.1+2+3.1.0.html?offer_filter=1&city_id=104&sort_column=0&noDeact=1&categories%5B%5D=1&categories%5B%5D=2&categories%5B%5D=3&rent_types%5B%5D=0&sMin=25&rMax=700&fur=1&img_only=1')
res.raise_for_status
soup = bs4.BeautifulSoup(res.text, 'html.parser')

#Listing of desired attributes
IDs = []
titles = []
links = []
prices = []
sq_mtr = []

#Scraping method
def collect_houses(page):
    soup = bs4.BeautifulSoup(page, 'html.parser')

    div_tags = soup.find_all('div')
    ids = []
    for div in div_tags:
     ID = div.get('id')
     if re.match("liste-details-ad-[0-9]{7}", str(ID)):
         ids.append(ID)

    #Collecting attributes (title, price, link, size) of each house
    for id in ids:
        title_selector = ('#' + str(id) + ' > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > h3:nth-child(1) > a:nth-child(1)')
        title = soup.select(title_selector)

        #"Subsoup" to extract the relative link from the title tag.
        subsoup = bs4.BeautifulSoup(str(title), 'html.parser')
        pre_link = subsoup.find(href=True)
        link = ('https://www.wg-gesucht.de' + str(pre_link['href'])) #Full link of the house.

        price_selector = ('#' + str(id) + ' > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > b:nth-child(1)')
        price = soup.select(price_selector)

        size_selector = ('#' + str(id) + ' > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(3) > b:nth-child(1)')
        size = soup.select(size_selector)
        
        IDs.append(id[-7:])
        titles.append(title[0].text)
        links.append(link)
        prices.append(price[0].text)
        sq_mtr.append(size[0].text) 

#Scraping the 1st page:
collect_houses(res.text)

#Are there more pages?
pagination = soup.find_all("a", class_ = "a-pagination")

#Scraping the second page
if len(pagination) >= 1:
    soup2 = bs4.BeautifulSoup(str(pagination[0]), 'html.parser')
    extracted = soup2.find(href=True)
    nxt_page = ('https://www.wg-gesucht.de/' + str(extracted['href']))
    #Scraping the second page:
    collect_houses((requests.get(nxt_page)).text)

#Scraping the third page
elif len(pagination) >= 2:
    soup3 = bs4.BeautifulSoup(str(pagination[1]), 'html.parser')
    extracted2 = soup3.find(href=True)
    third_page = ('https://www.wg-gesucht.de/' + str(extracted2['href']))
    #Scraping the third page:
    collect_houses((requests.get(third_page)).text)


#Creating and cleaning the dataFrame
df = pd.DataFrame(list(zip(IDs, titles, links, prices, sq_mtr)),
                  columns = ['Id', 'Title', 'Link', 'Price', 'Size'])
df = df.set_index('Id')
df['Title'] = df['Title'].replace(r'\n', '', regex=True)
df['Title'] = df['Title'].replace(r'(\s\s\s)+', '', regex=True)

#Reading csv previously saved
last_df = pd.read_csv('wohnungen_db.csv')
last_df = last_df.set_index('Id')

#Looking for changes between latest and previous indexes
new_houses = []


for i in list(df.index):
    if int(i) not in list(last_df.index):
        new_houses.append(int(i))


for n in new_houses:
    x = df.loc[str(n)]
    message = str(x['Link']) #I just want the link alone to display in the mssg.
    print(message)
    telegram_send.send(messages=[message])

#Exporting csv (updating the db)
df.to_csv('wohnungen_db.csv', encoding = 'utf-8')