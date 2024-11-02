import os
import random
from PIL import Image

def createFileName(fileName, ext=".txt"):
    """
    Generates a unique file name based on the one provided
    Args:
        fileName (str): the file name (without extension)
        ext (str, optional): the extension of the file. Defaults to ".txt".
    Returns:
        _type_: _description_
    """
    if os.path.exists(fileName + ext):
        newName = fileName [::-1]
        version = ""
        lenOfName = len(fileName)
        for i in range(lenOfName):
            if newName[i].isdigit():
                version = newName[i] + version
            else:
                version = "0" if version == "" else version
                fileName = fileName[:lenOfName-i] + str(int(version)+1)
                return createFileName(fileName)
    else :
        return fileName
def crop_random_square(image_path, output_dir, out_ext='.png'):
    # Open the image
    with Image.open(image_path) as img:
        width, height = img.size
        
        # Determine the minimum dimension of the image
        min_dim = min(width, height)
        
        # Determine the size of the square to crop (between 10% and 100% of the minimum dimension)
        square_size = random.randint(int(0.1 * min_dim), min_dim)
        
        # Randomly select the top-left corner of the cropped square
        left = random.randint(0, width - square_size)
        top = random.randint(0, height - square_size)
        
        # Crop the square from the image
        cropped_img = img.crop((left, top, left + square_size, top + square_size))
        
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the cropped image
        cropped_filename = createFileName('cropped_image', ext=out_ext) + out_ext
        print(cropped_filename)
        output_path = os.path.join(output_dir, cropped_filename)
        cropped_img.save(output_path)
        print(f'Cropped image saved to {output_path}')
if __name__ == '__main__':
    # Example usage
    image_path = './images/AbbeyGardens_EN-GB0442009047_UHD.jpg'
    output_dir = 'questions'
    crop_random_square(image_path, output_dir)