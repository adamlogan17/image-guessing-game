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

def create_google_slide_with_image(paths_to_images, presentation_title='New Presentation'):
    # NOTE: Maybe split this function up as it is very large

    # Authenticate and construct the service
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON, scopes=SCOPES)
    slide_service = build('slides', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # Defined here and only extended to, to allow for multiple requests to be batched
    alter_content_requests = []
    drive_images = []

    # Upload the image to Google Drive and get the public URL
    create_slides_requests = []
    for image_path in paths_to_images:
        image_url, drive_id = upload_image_to_drive(image_path, drive_service)
        drive_images.append({'image_url': image_url, 'drive_id': drive_id})

    # Create a new presentation
    presentation = slide_service.presentations().create(body={'title': presentation_title}).execute()
    presentation_id = presentation.get('presentationId')

    # Define the slide dimensions
    slide_width =  presentation.get('pageSize').get('width').get('magnitude')
    slide_height = presentation.get('pageSize').get('height').get('magnitude')

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
                    'objectId': object_id,  # Replace with the object ID of the title placeholder
                    'text': text,
                    'insertionIndex': 0 
                }
            })
            object_id = None

    # Creates slides for each photo
    for image in drive_images:
        create_slides_requests.append({
            'createSlide': {
                'slideLayoutReference': {
                    'predefinedLayout': 'BLANK'
                }
            }
        })
    # Should only use the below to create slides
    create_slides_response = slide_service.presentations().batchUpdate(presentationId=presentation_id, body={'requests': create_slides_requests}).execute()    

    # Adds the images to the presentation
    for i in range(0, len(drive_images)):
        image_url = drive_images[i].get('image_url')
        slide_id = create_slides_response['replies'][i]['createSlide']['objectId']
        image_id = 'image_{}'.format(i)
        alter_content_requests.extend([
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

    slide_service.presentations().batchUpdate(presentationId=presentation_id, body={'requests': alter_content_requests}).execute()

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
        drive_id = image.get('drive_id')
        delete_file_from_drive(drive_id, drive_service)

    print(f'Created presentation with ID: {presentation_id}')

if __name__ == '__main__':
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    clear_service_account_drive(drive_service)

    image_path = ['./images/AbbeyGardens_EN-GB0442009047_UHD.jpg', './images/AbiquaFalls_EN-GB6795791915_1920x1080.jpg']
    create_google_slide_with_image(image_path, presentation_title='Testing Guessing Game Presentation')
