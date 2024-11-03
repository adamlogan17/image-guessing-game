import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the scope for Google Slides API and Google Drive API
SCOPES = ['https://www.googleapis.com/auth/presentations', 'https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_JSON = os.getenv('SERVICE_ACCOUNT_JSON')

# Stored as an environment variable so there is no accidental exposure of the email
PERSONAL_EMAIL = os.getenv('PERSONAL_EMAIL')

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

def create_google_slide_with_image(image_path, presentation_title='New Presentation'):
    # Authenticate and construct the service
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON, scopes=SCOPES)
    slide_service = build('slides', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # Defined here and only extended to, to allow for multiple requests to be batched
    add_image_requests = []

    # Upload the image to Google Drive and get the public URL
    image_url, drive_id = upload_image_to_drive(image_path, drive_service)

    # Create a new presentation
    presentation = slide_service.presentations().create(body={'title': presentation_title}).execute()
    presentation_id = presentation.get('presentationId')

    # Define the slide dimensions
    slide_width =  presentation.get('pageSize').get('width').get('magnitude')
    slide_height = presentation.get('pageSize').get('height').get('magnitude')

    first_slide_id = presentation.get('slides')[0].get('objectId')
    first_slide_objects = presentation.get('slides')[0].get('pageElements')

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
            add_image_requests.append({
                'insertText': {
                    'objectId': object_id,  # Replace with the object ID of the title placeholder
                    'text': text,
                    'insertionIndex': 0 
                }
            })
            object_id = None

    # Add a new slide
    create_slide_requests = [
        {
            'createSlide': {
                'slideLayoutReference': {
                    'predefinedLayout': 'BLANK'
                }
            }
        }
    ]
    response = slide_service.presentations().batchUpdate(presentationId=presentation_id, body={'requests': create_slide_requests}).execute()
    slide_id = response['replies'][0]['createSlide']['objectId']

    # Add the image to the slide
    image_id = 'image_1'
    add_image_requests.extend([
        {
            'createImage': {
                'objectId': image_id,
                'url': image_url,
                'elementProperties': {
                    'pageObjectId': slide_id,
                    'size': {
                        'height': {'magnitude': slide_height / 2, 'unit': 'EMU'},
                        'width': {'magnitude': slide_width / 2, 'unit': 'EMU'}
                    },
                    'transform': {
                        'scaleX': 1,
                        'scaleY': 1,
                        'translateX': slide_width / 4,
                        'translateY': slide_height / 4,
                        'unit': 'EMU'
                    }
                }
            }
        }
    ])

    print(add_image_requests)
    slide_service.presentations().batchUpdate(presentationId=presentation_id, body={'requests': add_image_requests}).execute()

    # Share the presentation with your personal Google account
    drive_service.permissions().create(
        fileId=presentation_id,
        body={
            'type': 'user',
            'role': 'writer',
            'emailAddress': PERSONAL_EMAIL
        }
    ).execute()

    delete_file_from_drive(drive_id, drive_service)

    print(f'Created presentation with ID: {presentation_id}')

if __name__ == '__main__':
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    clear_service_account_drive(drive_service)

    image_path = './images/AbbeyGardens_EN-GB0442009047_UHD.jpg'
    create_google_slide_with_image(image_path, presentation_title='Testing Guessing Game Presentation')
