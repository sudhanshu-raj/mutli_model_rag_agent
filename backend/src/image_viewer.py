from IPython.display import Image, display
import os


class ImageViewer:
    """
    This helps to view the image only from the path
    """

    def __init__(self, base_path="output/images"):
        self.base_path = base_path

    def show_image(self, image_ref):
        """Show image from reference like [Image: page_3.jpg]"""
        if "[Image:" in image_ref:
            filename = image_ref.split(": ")[1].replace("]", "").strip()
            img_path = os.path.join(self.base_path, filename)
            if os.path.exists(img_path):
                display(Image(filename=img_path))
            else:
                print(f"Image not found: {filename}")
