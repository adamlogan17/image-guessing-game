- [image-guessing-game](#image-guessing-game)
  - [Create Service Account JSON](#create-service-account-json)
  - [Enable Google APIs](#enable-google-apis)
  - [TODOs](#todos)
  - [Useful Links](#useful-links)

# image-guessing-game

This is a python programme which will randomly crop an image and place these into a google slide, for an image guessing game

## Create Service Account JSON

Instructions below found [here](https://stackoverflow.com/questions/46287267/how-can-i-get-the-file-service-account-json-for-google-translate-api)

1. Go to <https://console.cloud.google.com/apis/credentials>
   1. (Optional) Create a new project
2. On the top left there is a blue "create credentials" button click it and select "service account key." (see below if its not there)
3. Choose the service account you want, that you created
4. Go to the 'Keys' tab
5. Select the 'ADD KEY' button
6. Select 'Generate new key'
7. It should allow give you a json to download

## Enable Google APIs

1. Go to <https://console.cloud.google.com/apis/credentials>
2. Ensure the same project as your service account JSON is selected
3. Go to 'Enabled APIs and services', in the side bar
4. Select '+ ENABLE APIS AND SERVICES'
5. Search for 'Google Slides API'
6. Hit 'Enable'
7. Search for 'Google Drive API'
8. Hit 'Enable'

## TODOs

- Decide if the `service` should be created in the `create_google_slide_with_image` function or outside it

- Finish adding all cropped images to google slides

- Add slack integration to get profile picture images
- Modify to use templates for google drive
- Separate what is currently in `main.py` into a different file called `image_cropping.py`
- Maybe make this it's own repo?
  - Need to make sure commits transfer
- Make into a web app
  - Allow users to upload a folder of images to use
  - Can download results as either `pdf`, microsoft powerpoint or as google slide file type

- Create a Dockerfile for the project

## Useful Links

- [Google Drive API Docs](https://developers.google.com/drive/api/reference/rest/v3)
- [Google Slides API docs](https://developers.google.com/slides/api/reference/rest)
- [Units for Slides](https://developers.google.com/slides/api/reference/rest/v1/Unit)
