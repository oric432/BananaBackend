import io

from PIL import Image


def get_image_dimensions(file):
    try:
        image_stream = io.BytesIO(file)

        # Open image using Pillow
        img = Image.open(image_stream)

        # Get image dimensions
        width, height = img.size

        return width, height
    except Exception as e:
        print(f"Error getting image dimensions: {e}")
        return None, None
