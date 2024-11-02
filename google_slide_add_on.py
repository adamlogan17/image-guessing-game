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
    return image_url

def create_google_slide_with_image(image_path, presentation_title='New Presentation'):
    # Authenticate and construct the service
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON, scopes=SCOPES)
    service = build('slides', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # Upload the image to Google Drive and get the public URL
    image_url = upload_image_to_drive(image_path, drive_service)

    # Create a new presentation
    presentation = service.presentations().create(body={'title': presentation_title}).execute()
    presentation_id = presentation['presentationId']

    # Define the slide dimensions
    slide_width = 9600000  # 10 inches in EMUs
    slide_height = 5400000  # 5.625 inches in EMUs

    # Add a new slide
    requests = [
        {
            'createSlide': {
                'slideLayoutReference': {
                    'predefinedLayout': 'BLANK'
                }
            }
        }
    ]
    response = service.presentations().batchUpdate(presentationId=presentation_id, body={'requests': requests}).execute()
    slide_id = response['replies'][0]['createSlide']['objectId']

    # Add the image to the slide
    image_id = 'image_1'
    requests = [
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
    ]
    service.presentations().batchUpdate(presentationId=presentation_id, body={'requests': requests}).execute()

    # Share the presentation with your personal Google account
    drive_service.permissions().create(
        fileId=presentation_id,
        body={
            'type': 'user',
            'role': 'writer',
            'emailAddress': PERSONAL_EMAIL
        }
    ).execute()

    print(f'Created presentation with ID: {presentation_id}')

if __name__ == '__main__':
    # Example usage
    image_path = './images/AbbeyGardens_EN-GB0442009047_UHD.jpg'
    create_google_slide_with_image(image_path, presentation_title='Testing Guessing Game Presentation')