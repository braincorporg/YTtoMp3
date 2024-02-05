import os
import subprocess
from flask import Flask, request, jsonify, send_file
from moviepy.editor import *
from openai import OpenAI

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def download_audio_youtube_dl(youtube_url, output_filename):
    # Construct the youtube-dl command
    command = ["youtube-dl", "-x", "--audio-format", "mp3", "-o", output_filename, youtube_url]
    subprocess.run(command, check=True)

def get_transcript(file_path):
    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        with open(file_path, 'rb') as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=f
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

    output_filename = "temp_audio.mp3"
    download_audio_youtube_dl(youtube_url, output_filename)
    
    return send_file(output_filename, mimetype="audio/mp3", as_attachment=True, download_name="download.mp3")

@app.route('/transcribe', methods=['GET'])
def transcribe():
    youtube_url = request.args.get('url')
    if not youtube_url:
        return "YouTube URL is required", 400

    try:
        output_filename = "temp_audio.mp3"
        download_audio_youtube_dl(youtube_url, output_filename)
        transcript = get_transcript(output_filename)

        if transcript:
            return jsonify({"transcript": transcript})
        else:
            return "Transcription failed", 500
    except Exception as e:
        print(f"Error during transcription: {e}")
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)
