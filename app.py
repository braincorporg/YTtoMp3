from flask import Flask, request, Response
from pytube import YouTube
from moviepy.editor import *
import io

app = Flask(__name__)

def stream_video_as_mp3(youtube_url):
    video = YouTube(youtube_url)
    stream = video.streams.filter(only_audio=True).first()
    buffer = io.BytesIO()
    video_clip = AudioFileClip(stream.url, fps=44100, nbytes=2, nchannels=2)
    video_clip.write_audiofile(buffer, codec='libmp3lame')
    buffer.seek(0)
    return buffer

@app.route('/download_mp3', methods=['GET'])
def download_mp3():
    youtube_url = request.args.get('url')
    if not youtube_url:
        return "YouTube URL is required", 400

    try:
        mp3_stream = stream_video_as_mp3(youtube_url)
        return Response(mp3_stream, mimetype="audio/mp3")
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)
