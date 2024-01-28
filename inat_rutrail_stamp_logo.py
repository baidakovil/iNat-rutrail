import os
import re

import transliterate
from PIL import Image, ImageDraw, ImageFont

start_folder = 1
end_folder = 121
umbrella_text = ['inat', 'ru', 'trail']

source_logo_folder = './inat-project/logo/'
storing_folder = './rutrail/'
font_path = os.path.join(source_logo_folder, 'UbuntuMono-RI.ttf')
white_bg_path = os.path.join(source_logo_folder, 'rutrail-logo-background.png')
ducktrails_path = os.path.join(source_logo_folder, 'rutrail-logo-ducktrails_hacky.png')


trail_name_file = 'trail_name.txt'

font_size = 535
text_color = (172, 165, 9)
umbrella_text_color = (214, 33, 90)

horizontal_offset = 50
vertical_offset_start = -40
vertical_offset_step = 500
myFont = ImageFont.truetype(font_path, font_size)
duck = Image.open(ducktrails_path, 'r')


def prepare_logos_texts(folder):
    def transliterate_cyrillic(text):
        text = text.replace(' ', ' ')
        text = text.replace('  ', ' ')
        text = text.replace('  ', ' ')
        text = text.replace('—', '-')
        latin_text = transliterate.translit(
            language_code="ru", value=text, reversed=True
        )
        text = re.sub(r'[^a-zA-Z0-9-_\s]', '', latin_text)
        return text.lower()

    def split_five(text):
        logo_text = []
        start_offset = 0
        end_offset = 5
        for i in range(0, 3):
            add_text = text[start_offset:end_offset]
            if add_text.startswith(' '):
                add_text = add_text[1:]
                add_text += text[end_offset : end_offset + 1]
                end_offset += 1
            logo_text.append(add_text)
            start_offset = end_offset
            end_offset += 5
        return logo_text

    file_path = os.path.join(folder, trail_name_file)
    try:
        with open(file_path, "r") as file:
            second_line = file.readlines()[1].strip()
            second_line_transliterated = transliterate_cyrillic(second_line)
            print(second_line)
            print(transliterate_cyrillic(second_line_transliterated))
            print(split_five(second_line_transliterated))
    except FileNotFoundError:
        print('Folder not found: ', file_path, end='')
        return None

    return split_five(second_line_transliterated)


def prepare_image(i):
    folder = os.path.join(storing_folder, str(i))
    text = umbrella_text if i == 1 else prepare_logos_texts(folder)
    background = Image.open(white_bg_path, 'r')
    output_path = os.path.join(folder, f'project_logo_{i}.png')
    if text:
        I1 = ImageDraw.Draw(background)
        for i_line, five in enumerate(text):
            offset = (
                horizontal_offset,
                vertical_offset_start + vertical_offset_step * i_line,
            )
            I1.text(
                offset,
                five,
                font=myFont,
                fill=umbrella_text_color if i == 1 else text_color,
                stroke_width=1,
            )
        background.paste(duck, (0, 0), mask=duck)
        background.save(output_path)
        print(f'Image saved to {output_path}')
        print('*' * 10)
    else:
        print('...Skip')


for i in range(start_folder, end_folder + 1):
    prepare_image(i)
