from bs4 import BeautifulSoup
import requests
import re
import threading
import os
from os import path
from urllib3.exceptions import NewConnectionError, MaxRetryError
import sys
import codecs


class CollateralAdjectives:
    def __init__(self, url):
        res = requests.get(url)
        # Parse the html and get the table
        soup = BeautifulSoup(res.text, 'html.parser')
        tb = soup.find_all('tbody')[2]
        self.raw_tr_list = tb.find_all('tr')
        # Slice redundant tags
        self.tr_list = self.raw_tr_list[2:]
        self.result_dictionary = {}
        self.url_dictionary = {}
        self.my_list = []
        self.project_path = os.path.dirname(os.path.realpath(__file__))

    def get_animals(self):
        for tr in self.tr_list:
            if tr.td:
                animal_name = tr.td.a.text
                self.url_dictionary[animal_name] = tr.td.a.get('href')
            # Use css selector for collateral adjective
            collateral_adjective = tr.select_one('td:nth-of-type(6)')
            if collateral_adjective:
                # Cleaning text from [] or ()
                collateral_adjective_names = re.sub('\[.*\]', '', collateral_adjective.text)
                collateral_adjective_names = re.sub('\(.*\)', '', collateral_adjective_names)
                # Split collateral adjectives if more than one per animal
                collateral_adjective_names = collateral_adjective_names.split()

                for name in collateral_adjective_names:
                    # Rename '?' from wiki to UNKNOWN collateral adjective
                    name = re.sub('\?', 'UNKNOWN', name)
                    if name in self.result_dictionary:
                        self.result_dictionary[name].append(animal_name)
                    else:
                        self.result_dictionary[name] = [animal_name]

    def create_link_download_image(self, animal_wikipedia_url, animal_name):
        res = requests.get(f'http://en.wikipedia.org{animal_wikipedia_url}')
        soup = BeautifulSoup(res.text, 'html.parser')
        a = soup.find('a', class_='image')
        if a:
            image_link = a.img.get('src')
        else:
            infobox = soup.find('table', class_='infobox')
            image_link = infobox.tbody.tr.next_sibling.next_sibling.a.img.get('src')
        self.store_image_in_tmp_dir(image_link, animal_name)

    def store_image_in_tmp_dir(self, image_link, animal_name):
        image_path = path.join(self.project_path, "tmp")
        if not os.path.exists(image_path):
            try:
                os.makedirs(image_path)
            except OSError as e:
                print(f"Failed to create folder: {e}")

        res = requests.get(f'http:{image_link}')
        local_address = f'{image_path}\{animal_name}.jpg'
        self.url_dictionary[animal_name] = local_address
        with open(self.url_dictionary[animal_name], 'wb') as file:
            file.write(res.content)

    def create_list_of_strings_for_output(self):
        for collateral_adj, animal_name in self.result_dictionary.items():
            for animal in animal_name:
                tmp_str = f'Collateral adjective:{collateral_adj}<br>The animals: {animal}<br>' \
                          f'Link \'{animal}\' img:{self.url_dictionary[animal]}<br><br>'
                self.my_list.append(tmp_str)

    def create_output(self):
        output_path = path.join(self.project_path, "output")
        if not os.path.exists(output_path):
            try:
                os.makedirs(output_path)
            except OSError as e:
                print(f"Failed to create folder: {e}")
        output_path = path.join(output_path, "output.html")

        with open(output_path, "w+") as file:
            for item in self.my_list:
                try:
                    file.write(item)
                    #file.write('<br>')
                except UnicodeEncodeError:
                    if sys.stdout.encoding != 'cp850':
                        sys.stdout = codecs.getwriter('cp850')(sys.stdout.buffer, 'strict')
                    if sys.stderr.encoding != 'cp850':
                        sys.stderr = codecs.getwriter('cp850')(sys.stderr.buffer, 'strict')


def main():
    p = CollateralAdjectives(url='http://en.wikipedia.org/wiki/List_of_animal_names')
    p.get_animals()

    thread_list = []
    for animal_name, animal_wikipedia_url in p.url_dictionary.items():
        try:
            thread = threading.Thread(target=p.create_link_download_image,
                                      args=[animal_wikipedia_url, animal_name])
            thread.start()
            thread_list.append(thread)
        except MaxRetryError:
            raise

    for thread in thread_list:
        thread.join()

    # Creating list of strings of the collateral adjectives of animals and links to image
    p.create_list_of_strings_for_output()
    p.create_output()

if __name__ == '__main__':
    main()
