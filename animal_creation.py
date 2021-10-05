import collateral_adjectives
import requests
from bs4 import BeautifulSoup
import re

def get_link_and_download(animal_wiki_url, animal_name, href_dict):
    try:
        res = requests.get(f'https://en.wikipedia.org{animal_wiki_url}')
        soup = BeautifulSoup(res.text, 'html.parser')
        a = soup.find('a', class_ = 'image')
        if(a):
            img_link = a.img.get('src')
        else:
            infobox = soup.find('table', class_ = 'infobox')
            img_link = infobox.tbody.tr.next_sibling.next_sibling.a.img.get('src')
        download_and_store_img(img_link, animal_name, href_dict)
    except KeyboardInterrupt:
        print(KeyboardInterrupt.message)

def download_and_store_img(img_link, animal_name, href_dict):
    res = requests.get('https:' + img_link)
    local_address = './tmp/'+ re.sub('\/', '', animal_name) +'.jpg'
    href_dict[animal_name] = local_address
    with open(local_address, 'wb') as f:
        f.write(res.content)