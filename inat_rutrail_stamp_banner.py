import os

from PIL import Image

start_folder = 116
end_folder = 116
crop_offset = (78, 0)
size = (1281, 540)

storing_folder = './rutrail/'
logo = Image.open(
    './inat-project/logo/rutrail-logo-rutrail-onwhite-circle-feather_wide.png', 'r'
)


def prepare_image(i):
    folder = os.path.join(storing_folder, str(i))
    if not os.path.exists(folder):
        print('Skip ' + str(i))
        return

    def prepare_image_list(folder):
        image_list = []
        for file in os.listdir(folder):
            if file.endswith('_full.jpg'):
                image_list.append(os.path.join(folder, file))
        return image_list

    def crop_image(image, offset, size):
        return image.crop(
            (offset[0], offset[1], offset[0] + size[0], offset[1] + size[1])
        )

    image_list = prepare_image_list(folder)
    for image in image_list:
        img = Image.open(image)
        img = crop_image(img, crop_offset, size)
        img.paste(logo, (-88, 45), mask=logo)
        img.save(image.replace('_full.jpg', '_cropped.jpg'))


for i in range(start_folder, end_folder + 1):
    print(f'Start with {i}...', end='')
    prepare_image(i)
    print('Done with ' + str(i))
