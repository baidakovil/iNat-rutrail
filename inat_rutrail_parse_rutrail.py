import os
import re
import time

import requests
import transliterate
from bs4 import BeautifulSoup, NavigableString

output_folder = 'rutrail'
start_trail = 88
end_trail = 121


def transliterate_cyrillic(text):
    text = text.replace(' ', ' ')
    text = text.replace(' ', '_')
    text = text.replace('—', '-')
    latin_text = transliterate.translit(language_code="ru", value=text, reversed=True)
    text = re.sub(r'[^a-zA-Z0-9-_\s]', '', latin_text)
    return text.lower()


def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)


def save_text_from_page(response, url, folder_name):
    soup = BeautifulSoup(response.content, 'html.parser')
    h1_span = soup.find('h1', class_='h1_center h1_trail')
    if h1_span:
        h1_span_text = h1_span.span.get_text()
        transliterated_text = transliterate_cyrillic(h1_span_text)
        with open(f"{folder_name}/trail_name.txt", "w") as file:
            file.write(
                url
                + '\n'
                + h1_span_text
                + '\n'
                + transliterated_text
                + '\n'
                + transliterated_text
                + '_rutrail_route_'
                + url.split('/')[-1]
            )
    else:
        assert 'No h1 tag found'


def save_all_images(response, folder_name):
    soup = BeautifulSoup(response.content, 'html.parser')
    div_with_images = soup.find('div', class_='js_trail_top_photos_view _photo')
    if div_with_images:
        image_tags = div_with_images.find_all('img')
        for i, img in enumerate(image_tags):
            if i == 0:
                image_src = img['src']
            else:
                image_src = img['data-src']
            image_name = image_src.split('/')[-1]
            with open(f"{folder_name}/{image_name}", "wb") as file:
                image_data = requests.get('https://rutrail.org/' + image_src).content
                file.write(image_data)
    else:
        assert 'No images found'


def save_gpx_file(response, url, folder_name):
    soup = BeautifulSoup(response.content, 'html.parser')
    div_gpx = soup.find('div', class_='trail_map_button')
    if div_gpx:
        gpx_link = div_gpx.find('a', class_='_button')['href']
        gpx_data = requests.get('https://rutrail.org' + gpx_link).content
        folder_name = os.path.join(output_folder, url.split('/')[-1])
        with open(f"{folder_name}/trail_track.gpx", "wb") as file:
            file.write(gpx_data)
    else:
        assert 'No gpx file found'


def download_pdf(response, folder_name):
    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        pdf_link = soup.find_all('div', class_='trail_map_button')[1].a['href']
        pdf_response = requests.get('https://rutrail.org' + pdf_link)
        pdf_filename = pdf_link.split('/')[-1][:-3]
        with open(os.path.join(folder_name, pdf_filename), "wb") as file:
            file.write(pdf_response.content)
    except:
        print('WARNING: Problem when downloading pdf')


def save_descr_text(response, folder_name):
    def process_tag(div, file):
        for tag in div.find_all(['h2', 'h3', 'p', 'ul', 'li', 'a']):
            if tag.name in ['h2', 'h3']:
                file.write(f'{"#" * int(tag.name[1])} {tag.get_text().lstrip()}\n')
            elif tag.name == 'p':
                process_paragraph(tag, file)
            elif tag.name == 'ul':
                for li in tag.find_all('li'):
                    file.write(f'* {li.get_text().lstrip()}\n')

    def process_paragraph(tag, file):
        for child in tag.children:
            if isinstance(child, NavigableString):
                file.write(child)
            elif child.name == 'a':
                if child["href"].startswith('/'):
                    file.write(
                        f'[{child.get_text()}](https://rutrail.org{child["href"]})'
                    )
                else:
                    file.write(f'[{child.get_text()}]({child["href"]})')
        file.write('\n')

    soup = BeautifulSoup(response.content, 'html.parser')
    with open(f"{folder_name}/description.md", "w") as file:
        div_with_text = soup.find('div', class_='_descr')
        if div_with_text:
            with open(f"{folder_name}/description.md", "w") as file:
                div_text = div_with_text.div.get_text() + '\n'
                file.write(div_text)
                read_div = soup.find_all('div', class_='read')
                if read_div:
                    for div in read_div:
                        process_tag(div, file)


def save_info_from_web_page(url):
    response = requests.get(url)
    if response.status_code != 404:
        folder_name = os.path.join(output_folder, url.split('/')[-1])
        create_folder(folder_name)
        save_text_from_page(response, url, folder_name)
        save_all_images(response, folder_name)
        save_gpx_file(response, url, folder_name)
        download_pdf(response, folder_name)
        save_descr_text(response, folder_name)
        print(f'Done with {url}')
    else:
        print(f'URL {url} responded 404')


for train in range(start_trail, end_trail + 1):
    url = f'https://rutrail.org/trails/{train}'
    save_info_from_web_page(url)
    time.sleep(10)
