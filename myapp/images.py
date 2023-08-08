from PIL import Image


def image_compress():
    im = Image.open(file)
    compessed_image_path = 'C:/repos/cloud/test/' + "cloud_" + image
    im.save(compessed_image_path, optimize=True, quality=50, lossless = True)

def create_thumbnail():
    size = (256, 256)
    image = "blue.jpG"
    im = Image.open(image)
    im.thumbnail(size)
    im.save('thumbnail.jpg')