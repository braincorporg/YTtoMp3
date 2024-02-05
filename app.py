from flask import Flask, request, send_file
from pytube import YouTube
from moviepy.editor import *
import os
import io
from openai import OpenAI
import boto3


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
app = Flask(__name__)

# Configure S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

S3_BUCKET = 'hermesai.braincorp'

def upload_file_to_s3(file_path, bucket_name, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_path)
    
    try:
        response = s3_client.upload_file(file_path, bucket_name, object_name)
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None
    return f"s3://{bucket_name}/{object_name}"
    
def download_video_as_mp3(youtube_url):
    # Download video from YouTube
    video = YouTube(youtube_url)
    stream = video.streams.filter(only_audio=True).first()
    downloaded_file = stream.download(filename="temp")

    # Convert video to MP3
    video_clip = AudioFileClip(downloaded_file)
    temp_mp3_filename = "temp.mp3"
    video_clip.write_audiofile(temp_mp3_filename)

    # Read the MP3 file into a BytesIO object
    with open(temp_mp3_filename, 'rb') as f:
        mp3_file = io.BytesIO(f.read())

    # Remove the temporary files
    os.remove(downloaded_file)
    os.remove(temp_mp3_filename)

    mp3_file.seek(0)
    return mp3_file


def get_transcript(audio_file):
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Write the BytesIO object to a temporary file
    temp_filename = "temp_audio_file.mp3"
    with open(temp_filename, "wb") as f:
        f.write(audio_file.read())

    try:
        # Use the file path for transcription
        with open(temp_filename, 'rb') as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=f
            )
        return transcript['text']
    finally:
        # Clean up: remove the temporary file
        os.remove(temp_filename)

    
@app.route('/download_mp3', methods=['GET'])
def download_mp3():
    youtube_url = request.args.get('url')
    if not youtube_url:
        return "YouTube URL is required", 400

    mp3_file = download_video_as_mp3(youtube_url)
    
    return send_file(mp3_file, mimetype="audio/mp3", as_attachment=True, download_name="download.mp3")
@app.route('/transcribe', methods=['GET'])
def transcribe():
    youtube_url = request.args.get('url')
    if not youtube_url:
        return "YouTube URL is required", 400
    print("Received YouTube URL:", youtube_url)
    try:
        # Download the video as mp3 and get BytesIO object
        mp3_file = download_video_as_mp3(youtube_url)
        print("MP3 file downloaded and converted.")  # Debug 2
        # Create a temporary file to hold the mp3 data
        temp_filename = "temp_audio_for_transcription.mp3"
        with open(temp_filename, "wb") as temp_file:
            temp_file.write(mp3_file.read())
        
        # Reset the BytesIO object position to the start
        mp3_file.seek(0)
        print("File pointer reset.")
        # Now, instead of passing BytesIO directly, use the temporary file
        transcript = ""
        with open(temp_filename, 'rb') as f:
            transcript = OpenAI(api_key=OPENAI_API_KEY).audio.transcriptions.create(
                model="whisper-1", 
                file=f
            )['text']
        print("Transcription API called successfully.")  # Debug 4
        # Cleanup: Remove the temporary file after use
        os.remove(temp_filename)

        return jsonify({"transcript": transcript})
    except Exception as e:
        print(f"Error during transcription: {e}")  # Improved error logging
        return str(e), 500


        
if __name__ == '__main__':
    app.run(debug=True)
