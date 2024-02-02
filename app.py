from flask import Flask, request, send_file
from pytube import YouTube
from moviepy.editor import *
import os
import io

app = Flask(__name__)

def download_video_as_mp3(youtube_url):
    # Download video from YouTube
    video = YouTube(youtube_url)
    stream = video.streams.filter(only_audio=True).first()
    downloaded_file = stream.download(filename="temp")

    # Convert video to MP3
    video_clip = AudioFileClip(downloaded_file)
    mp3_file = io.BytesIO()
    video_clip.write_audiofile(mp3_file, format="mp3")
    mp3_file.seek(0)

    # Remove the temporary file
    os.remove(downloaded_file)

    return mp3_file

@app.route('/download_mp3', methods=['GET'])
def download_mp3():
    youtube_url = request.args.get('url')
    if not youtube_url:
        return "YouTube URL is required", 400

    mp3_file = download_video_as_mp3(youtube_url)
    
    return send_file(mp3_file, mimetype="audio/mp3", as_attachment=True, download_name="download.mp3")

if __name__ == '__main__':
    app.run(debug=True)
