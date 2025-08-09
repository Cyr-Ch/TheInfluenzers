from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import google_auth_oauthlib.flow
from config import CLIENT_SECRET_FILE

def youtube_authenticate():
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    credentials = flow.run_console()
    return build("youtube", "v3", credentials=credentials)

def upload_video(youtube, file_path, title, description, tags):
    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    media_file = MediaFileUpload(file_path, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media_file
    )
    response = request.execute()
    print(f"Upload successful: https://youtu.be/{response['id']}")
    return response
