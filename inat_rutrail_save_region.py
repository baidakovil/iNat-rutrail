import os

import requests
from bs4 import BeautifulSoup


def parse_webpage_and_save_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all divs with class "read read__maxw"
    read_divs = soup.find_all('div', class_='read read__maxw')

    for i, read_div in enumerate(read_divs):
        if read_div:
            try:
                # Find all divs with class "js_trail js_trail_121 trail_listed" inside the read_div
                trail_divs = read_div.find_all(
                    'div',
                    class_=lambda value: value
                    and value.startswith('js_trail js_trail_')
                    and value.endswith(' trail_listed'),
                )

                for j, trail_div in enumerate(trail_divs):
                    info_div = trail_div.find('div', class_='_info')
                    if info_div:
                        trail_url = trail_div.find('div', class_='_image').find('a')[
                            'href'
                        ]
                        trail_name = trail_url.split('/')[
                            -2
                        ]  # Extract the trail name from the URL

                        text_to_save = info_div.get_text().strip()

                        # Append the text to the existing file
                        file_path = f'./rutrail/{trail_name}/trail_name.txt'
                        try:
                            with open(file_path, 'a') as file:
                                file.write(text_to_save + '\n')
                        except FileNotFoundError:
                            pass
                    else:
                        print(f"No '_info' div found for trail {i+1}, sub-trail {j+1}")
            except AttributeError:
                pass


# Example usage
parse_webpage_and_save_text('https://rutrail.org/trails/#view=list')
