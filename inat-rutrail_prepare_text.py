import os
import time

import transliterate
from translate import Translator

template_path = './inat-project/project_text_template.txt'
output_file_prefix = 'project_info_'
description_filename = 'description.md'
trail_info_filename = 'trail_name.txt'
project_color = '#b1cb99'

start_folder = 43
end_folder = 121

translator = Translator(from_lang='ru', to_lang="en")


def transliterate_cyrillic(text):
    text = text.replace(' ', ' ')
    text = text.replace('  ', ' ')
    text = text.replace('  ', ' ')
    latin_text = transliterate.translit(language_code="ru", value=text, reversed=True)
    # text = re.sub(r'[^a-zA-Z0-9-_\s]', '', latin_text)
    return latin_text


def create_project_text(i, folder):
    def separator(text):
        fill = ':' * int((50 - len(text)) // 2)
        return '\n' + fill + text + fill + '\n'

    with open(template_path, 'r') as template_file:
        template_content = template_file.read()

    with open(os.path.join(folder, trail_info_filename), 'r') as trail_info_file:
        trail_url = trail_info_file.readline().strip()
        trail_name_rus = trail_info_file.readline().strip()
        _ = trail_info_file.readline()
        trail_place_name = trail_info_file.readline().strip()
        trail_region_rus = trail_info_file.readline().strip()
        if not trail_region_rus:
            trail_region_rus = trail_info_file.readline().strip()

    with open(os.path.join(folder, description_filename), 'r') as trail_desc_file:
        trail_desc = trail_desc_file.read()
        trail_desc_rus = trail_desc[: trail_desc.find('##')]
    trail_desc_eng = translator.translate(trail_desc_rus)

    project_name = trail_name_rus + ' — Маркированный маршрут RuTrail'
    trail_name_translit = transliterate_cyrillic(trail_name_rus)
    trail_name_eng = translator.translate(trail_name_rus)
    trail_region_eng = translator.translate(trail_region_rus)

    dict_replace = {
        'PROJECT_NAME': project_name,
        'TRAIL_URL': trail_url,
        'TRAIL_NAME_RUS': trail_name_rus,
        'TRAIL_NAME_ENG': trail_name_eng,
        'TRAIL_NAME_TRANSLIT': trail_name_translit,
        'TRAIL_REGION_RUS': trail_region_rus,
        'TRAIL_REGION_ENG': trail_region_eng,
        'TRAIL_DESC_RUS': trail_desc_rus,
        'TRAIL_DESC_ENG': trail_desc_eng,
    }

    for key, value in dict_replace.items():
        template_content = template_content.replace(key, value)

    output_file_path = f'{output_file_prefix}{i}.txt'
    with open(os.path.join(folder, output_file_path), 'w') as output_file:
        output_file.write(
            separator('PLACE NAME')
            + trail_place_name
            + separator('PROJECT NAME')
            + project_name
            + separator('PROJECT COLOR')
            + project_color
            + separator('PROJECT TEXT')
            + template_content
            + separator('DONT FORGET')
            + 'INCLUDE PLACES & ALLOW CASUAL!'
        )


def create_project_texts(start_folder, end_folder):
    print('Start create project texts')
    for i in range(start_folder, end_folder + 1):
        print('Start ' + str(i) + '...', end='')
        folder = f'./rutrail/{i}/'
        if not os.path.exists(folder):
            print('Skip ' + str(i))
            continue
        create_project_text(i, folder)
        print('Done with ' + str(i))
        time.sleep(5)


create_project_texts(start_folder, end_folder)
