from flask import Flask, request, send_file, jsonify
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
        s3_client.upload_file(file_path, bucket_name, object_name)
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None
    return f"https://{bucket_name}.s3.amazonaws.com/{object_name}"

def download_video_as_mp3(youtube_url):
    # Download video from YouTube
    video = YouTube(youtube_url)
    stream = video.streams.filter(only_audio=True).first()
    downloaded_file = stream.download(filename="temp")

    # Convert video to MP3
    video_clip = AudioFileClip(downloaded_file)
    temp_mp3_filename = "temp.mp3"
    video_clip.write_audiofile(temp_mp3_filename)

    return temp_mp3_filename

def get_transcript(s3_url):
    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=s3_url
        )
        return transcript['text']
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None

@app.route('/download_mp3', methods=['GET'])
def download_mp3():
    youtube_url = request.args.get('url')
    if not youtube_url:
        return "YouTube URL is required", 400

    mp3_file_path = download_video_as_mp3(youtube_url)
    s3_file_url = upload_file_to_s3(mp3_file_path, S3_BUCKET)

    if s3_file_url:
        return jsonify({"s3_url": s3_file_url})
    else:
        return "Failed to upload to S3", 500

@app.route('/transcribe', methods=['GET'])
def transcribe():
    youtube_url = request.args.get('url')
    if not youtube_url:
        return "YouTube URL is required", 400

    try:
        mp3_file_path = download_video_as_mp3(youtube_url)
        s3_file_url = upload_file_to_s3(mp3_file_path, S3_BUCKET)

        if not s3_file_url:
            return "Failed to upload to S3", 500

        transcript = get_transcript(s3_file_url)

        if transcript:
            return jsonify({"transcript": transcript})
        else:
            return "Transcription failed", 500
    except Exception as e:
        print(f"Error during transcription: {e}")
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)
