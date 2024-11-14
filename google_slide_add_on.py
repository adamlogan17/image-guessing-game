import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv
import copy
import uuid

# Load environment variables from .env file
load_dotenv()

# Define the scope for Google Slides API and Google Drive API
SCOPES = ['https://www.googleapis.com/auth/presentations', 'https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_JSON = os.getenv('SERVICE_ACCOUNT_JSON')

# Stored as an environment variable so there is no accidental exposure of the email
PERSONAL_EMAIL = os.getenv('PERSONAL_EMAIL')

def convert_emu_to_pt(emu):
    return emu / 12700 

def upload_image_to_drive(image_path, service):
    file_metadata = {'name': os.path.basename(image_path)}
    media = MediaFileUpload(image_path, mimetype='image/jpeg')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = file.get('id')
    
    # Make the file publicly accessible
    service.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()
    
    # Get the public URL of the uploaded image
    image_url = f'https://drive.google.com/uc?id={file_id}'
    return image_url, file_id

def delete_file_from_drive(image_id, service):
    try:
        service.files().delete(fileId=image_id).execute()
        print(f'File with ID {image_id} was deleted permanently.')
    except Exception as e:
        print(f'An error occurred: {e}')

def clear_service_account_drive(service):
    files = service.files().list().execute().get('files', [])
    for file in files:
        delete_file_from_drive(file.get('id'), service)

def batch_create_image_slides(presentation, drive_images, service, requests):
    presentation_id = presentation.get('presentationId')

    create_slides_requests = []

    # Adds the images to the presentation
    for image in drive_images:
        image_url = image.get('image_url', None)
        slide_id = 'slide_{}'.format(uuid.uuid4())
        text_id = 'text_{}'.format(uuid.uuid4())
        
        single_slide_request = copy.deepcopy(requests)
        for request in single_slide_request:
            image_id = 'image_{}'.format(uuid.uuid4())
            if request.get('createImage'):
                request['createImage']['url'] = image_url if image_url else image.get(request['createImage']['url']).get('image_url')
                request['createImage']['objectId'] = image_id
                request['createImage']['elementProperties']['pageObjectId'] = slide_id
            if request.get('createShape'):
                request['createShape']['objectId'] = text_id
                request['createShape']['elementProperties']['pageObjectId'] = slide_id
            if request.get('insertText'):
                request['insertText']['objectId'] = text_id

        create_slides_requests.extend([
            {
                'createSlide': {
                    'objectId': slide_id,
                    'slideLayoutReference': {
                        'predefinedLayout': 'BLANK'
                    }
                }
            }
        ])

        create_slides_requests.extend(single_slide_request)

    service.presentations().batchUpdate(presentationId=presentation_id, body={'requests': create_slides_requests}).execute()

def create_google_slide_with_image(question_images, presentation_title='New Presentation'):
    # Authenticate and construct the service
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON, scopes=SCOPES)
    slide_service = build('slides', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # Defined here and only extended to, to allow for multiple requests to be batched
    alter_content_requests = []
    drive_images = []

    # Upload the image to Google Drive and get the public URL
    for image_path in question_images:
        element = {}
        for key in image_path:
            image_url, drive_id = upload_image_to_drive(image_path.get(key), drive_service)
            element[key] = {'image_url': image_url, 'drive_id': drive_id}
        drive_images.append(element)

    # Create a new presentation
    presentation = slide_service.presentations().create(body={'title': presentation_title}).execute()
    presentation_id = presentation.get('presentationId')

    slide_width =  presentation.get('pageSize').get('width').get('magnitude')
    slide_height = presentation.get('pageSize').get('height').get('magnitude')
    x_center = slide_width / 2
    y_center = slide_height / 2

    first_slide_objects = presentation.get('slides')[0].get('pageElements')

    # Adds text to the title slide
    object_id = None
    for object in first_slide_objects:
        if object.get('shape'):
            if object.get('shape').get('placeholder').get('type') == 'CENTERED_TITLE':
                object_id = object.get('objectId')
                text = 'Guess the Image!'
            if object.get('shape').get('placeholder').get('type') == 'SUBTITLE':
                object_id = object.get('objectId')
                text = "Created using 'image-guessing-game' by @adamlogan17"
        if object_id:
            alter_content_requests.append({
                'insertText': {
                    'objectId': object_id,
                    'text': text,
                    'insertionIndex': 0
                }
            })
            object_id = None
    
    slide_service.presentations().batchUpdate(presentationId=presentation_id, body={'requests': alter_content_requests}).execute()

    image_size = {
        'height': {'magnitude': slide_height / 2, 'unit': 'EMU'},
        'width': {'magnitude': slide_width / 2, 'unit': 'EMU'}
    }

    question_slides = [
        {
            'createImage': {
                'url': 'question',
                'elementProperties': {
                    'size': image_size,
                    'transform': {
                        'scaleX': 1,
                        'scaleY': 1,
                        'translateX': x_center - (image_size['width']['magnitude'] / 2),
                        'translateY': y_center - (image_size['height']['magnitude'] / 2),
                        'unit': 'EMU'
                    }
                }
            }
        },
        {
            "createShape": {
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "size": {
                        "width": {
                            "magnitude": 200,
                            "unit": "PT"
                        },
                        "height": {
                            "magnitude": 50,
                            "unit": "PT"
                        }
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": 20, 
                        "translateY": 20, 
                        "unit": "PT"
                    }
                }
            }
        },
        {
            'insertText': {
                'text': 'What is this image?',
                'insertionIndex': 0
            }
        }
    ]

    batch_create_image_slides(presentation, drive_images, slide_service, question_slides)

    image_size = {
        'height': {'magnitude': slide_height / 2.5, 'unit': 'EMU'},
        'width': {'magnitude': slide_width / 2.5, 'unit': 'EMU'}
    }

    space_distance = 25
    x_left_image = convert_emu_to_pt(x_center - image_size['width']['magnitude'] - space_distance)
    y_image = convert_emu_to_pt(y_center - (image_size['height']['magnitude'] / 2))
    x_right_image = x_left_image + convert_emu_to_pt(image_size['width']['magnitude']) + space_distance

    answer_slides = [
        {
            'createImage': {
                'url': 'question',
                'elementProperties': {
                    'size': image_size,
                    'transform': {
                        'scaleX': 1,
                        'scaleY': 1,
                        'translateX': x_left_image,
                        'translateY': y_image,
                        'unit': 'PT'
                    }
                }
            }
        },
        {
            'createImage': {
                'url': 'answer',
                'elementProperties': {
                    'size': image_size,
                    'transform': {
                        'scaleX': 1,
                        'scaleY': 1,
                        'translateX': x_right_image,
                        'translateY': y_image,
                        'unit': 'PT'
                    }
                }
            }
        },
        {
            "createShape": {
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "size": {
                        "width": {
                            "magnitude": 200,
                            "unit": "PT"
                        },
                        "height": {
                            "magnitude": 50,
                            "unit": "PT"
                        }
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": 20, 
                        "translateY": 20, 
                        "unit": "PT"
                    }
                }
            }
        },
        {
            'insertText': {
                'text': 'Answer',
                'insertionIndex': 0
            }
        }
    ]

    batch_create_image_slides(presentation, drive_images, slide_service, answer_slides)

    # Share the presentation with your personal Google account
    drive_service.permissions().create(
        fileId=presentation_id,
        body={
            'type': 'user',
            'role': 'writer',
            'emailAddress': PERSONAL_EMAIL
        }
    ).execute()

    for image in drive_images:
        for key in image:
            drive_id = image.get(key).get('drive_id')
            delete_file_from_drive(drive_id, drive_service)

    print(f'Created presentation with ID: {presentation_id}')

if __name__ == '__main__':
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    clear_service_account_drive(drive_service)

    questions = [
        {
            'question': './images/AbbeyGardens_EN-GB0442009047_UHD.jpg',
            'answer': './images/AbiquaFalls_EN-GB6795791915_1920x1080.jpg'
        },
        {
            'question': './images/AdelieDiving_EN-GB6436349406_1920x1080.jpg',
            'answer': './images/AlfanzinaLighthouse_EN-GB7045122942_UHD.jpg'
        }
    ]

    create_google_slide_with_image(questions, presentation_title='Testing Guessing Game Presentation')
