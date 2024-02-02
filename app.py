from flask import Flask, request, send_file
from pytube import YouTube
from moviepy.editor import *
import os
import io
from openai import OpenAI

app = Flask(__name__)
openaikey = "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"
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
    client = openai.Audio

    # Write the BytesIO object to a temporary file
    temp_filename = "temp_audio_file.mp3"
    with open(temp_filename, "wb") as f:
        f.write(audio_file.read())

    try:
        # Use the file path for transcription
        with open(temp_filename, 'rb') as f:
            transcript = client.transcriptions.create(
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
    try:
        youtube_url = request.args.get('url')
        if not youtube_url:
            return "YouTube URL is required", 400

        mp3_file = download_video_as_mp3(youtube_url)
        transcript_text = get_transcript(mp3_file)
        return jsonify({"transcript": transcript_text})
    except Exception as e:
        app.logger.error(f"Error in transcribe: {e}")
        return str(e), 500

        
if __name__ == '__main__':
    app.run(debug=True)
