import argparse
from image_cropping import crop_square_folder, get_images_from_folder
import os
import uuid
from google_slide_add_on import create_image_guess_slides

def guess_image_slides(image_folder, personal_email, presentation_title='Guess the Image!', keep_local_questions=False, keep_local_answers=True, keep_local_answers_on_error=True):
    # NOTE: Maybe change the 'keep' vars to 'remove' vars as the naming is pretty confusing currently

    if not os.path.exists(image_folder):
        print(f"Folder {image_folder} does not exist.")
        return

    output_dir = 'questions_{}'.format(uuid.uuid4())
    crop_square_folder(image_folder, output_dir, cropped_prefix='question')

    answers = get_images_from_folder(image_folder)
    questions = get_images_from_folder(output_dir)

    slide_images = []
    for question in questions:
        slide_images.append({
            'question': os.path.join(output_dir, question),
            'answer': os.path.join(image_folder, answers[questions.index(question)])
        })
    
    try:
        create_image_guess_slides(slide_images, personal_email, presentation_title=presentation_title)
    except Exception as e:
        keep_local_answers = keep_local_answers_on_error if not keep_local_answers else keep_local_answers
        print(f"Error creating Google Slides presentation: {e}")

    # Clean up, any files that were created when creating the slides
    if not keep_local_questions:
        remove_files_in_folder(output_dir)
    if not keep_local_answers:
        remove_files_in_folder(image_folder)
        

def remove_files_in_folder(folder_path):
    for f in os.listdir(folder_path):
        file_path = os.path.join(folder_path, f)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
    os.rmdir(folder_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a Google Slides presentation for a "Guess the Image" game.')
    parser.add_argument('image_folder', type=str, help='Path to the folder containing the images for the game.')
    parser.add_argument('personal_email', type=str, help='Personal email address to use for creating the Google Slides presentation.')
    parser.add_argument('--title', type=str, default='Guess the Image!', help='Title of the Google Slides presentation.')
    parser.add_argument('--keep_questions', action='store_true', help='Keep the cropped question images after creating the Google Slides presentation.')
    parser.add_argument('--remove_answers', action='store_false', help='Removes the original answer images after creating the Google Slides presentation.')
    args = parser.parse_args()


    guess_image_slides(args.image_folder, args.personal_email, presentation_title=args.title, keep_local_questions=args.keep_questions, keep_local_answers=args.remove_answers)