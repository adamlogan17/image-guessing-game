import os
import random
from PIL import Image
import shutil

def createFileName(fileName, ext=".txt", folder_path=''):
    """
    Generates a unique file name based on the one provided

    Args:
        fileName (str): the file name (without extension)
        ext (str, optional): the extension of the file. Defaults to ".txt".
        folder_path (str, optional): the path to the folder where the file will be saved. Defaults to None.

    Returns:
        _type_: _description_
    """
    if os.path.exists(folder_path + '/' + fileName + ext):
        newName = fileName [::-1]
        version = ""
        lenOfName = len(fileName)
        for i in range(lenOfName):
            if newName[i].isdigit():
                version = newName[i] + version
            else:
                version = "0" if version == "" else version
                fileName = fileName[:lenOfName-i] + str(int(version)+1)
                return createFileName(fileName, ext=ext, folder_path=folder_path)
    else :
        return fileName

def crop_random_square(image_path, output_dir, output_ext=None, output_name=None, prefix='cropped'):
    # Open the image
    with Image.open(image_path) as img:
        width, height = img.size
        
        # Determine the minimum dimension of the image
        min_dim = min(width, height)
        
        # Determine the size of the square to crop (between 10% and 50% of the minimum dimension)
        square_size = random.randint(int(0.1 * min_dim), int(0.5 * min_dim))
        
        # Randomly select the top-left corner of the cropped square
        left = random.randint(0, width - square_size)
        top = random.randint(0, height - square_size)
        
        # Crop the square from the image
        cropped_img = img.crop((left, top, left + square_size, top + square_size))
        
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Set the output extension
        if output_ext is None:
            output_ext = os.path.splitext(image_path)[1]

                # Set the output name
        if output_name is None:
            image_name = os.path.splitext(os.path.basename(image_path))[0]
            separator = '_'
            if not prefix:
                separator = ''
            output_name = prefix + separator + image_name
        
        # Save the cropped image
        cropped_filename = createFileName(output_name, ext=output_ext, folder_path=output_dir) + output_ext
        output_path = os.path.join(output_dir, cropped_filename)
        cropped_img.save(output_path)
        print(f'Cropped image saved to {output_path}')

def get_images_from_folder(folder_path):
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))]
    return image_files

def crop_square_folder(folder_path, output_dir, out_ext=None, cropped_prefix=''):
    image_files = get_images_from_folder(folder_path)

    # Iterate over the image files and crop a random square from each
    for image_file in image_files:
        print(f'Cropping image: {image_file}')
        image_path = os.path.join(folder_path, image_file)
        crop_random_square(image_path, output_dir, output_ext=out_ext, prefix=cropped_prefix)



if __name__ == '__main__':
    # Example usage
    image_path = './images/AbbeyGardens_EN-GB0442009047_UHD.jpg'
    output_dir = 'questions'
    crop_random_square(image_path, output_dir)

    crop_square_folder('./images', 'questions')