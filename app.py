import os
import subprocess
import time
from flask import Flask, request, jsonify, send_file
from openai import OpenAI

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def generate_unique_filename(extension="mp3"):
    timestamp = int(time.time())
    return f"temp_audio_{timestamp}.{extension}"

def download_audio_yt_dlp(youtube_url, output_filename):
    command = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", output_filename, youtube_url]
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
    finally:
        os.remove(file_path)

@app.route('/download_mp3', methods=['GET'])
def download_mp3():
    youtube_url = request.args.get('url')
    if not youtube_url:
        return "YouTube URL is required", 400

    output_filename = generate_unique_filename()
    download_audio_yt_dlp(youtube_url, output_filename)
    
    response = send_file(output_filename, mimetype="audio/mp3", as_attachment=True, download_name="download.mp3")
    os.remove(output_filename)  # Cleanup the file after sending
    return response

@app.route('/transcribe', methods=['GET'])
def transcribe():
    youtube_url = request.args.get('url')
    if not youtube_url:
        return "YouTube URL is required", 400

    output_filename = generate_unique_filename()
    download_audio_yt_dlp(youtube_url, output_filename)
    transcript = get_transcript(output_filename)

    if transcript:
        return jsonify({"transcript": transcript})
    else:
        return "Transcription failed", 500
        
@app.route('/transcribe_mp3_url', methods=['POST'])
def transcribe_mp3_url():
    data = request.get_json()  # Get data from the POST request body
    mp3_url = data.get('url')
    if not mp3_url:
        return "MP3 URL is required", 400

    try:
        output_filename = generate_unique_filename()
        download_mp3_file(mp3_url, output_filename)
        transcript = get_transcript(output_filename)

        if transcript:
            return jsonify({"transcript": transcript})
        else:
            return "Transcription failed", 500
    except Exception as e:
        print(f"Error during transcription: {e}")
        return str(e), 500

def download_mp3_file(mp3_url, output_filename):
    response = requests.get(mp3_url)
    if response.status_code == 200:
        with open(output_filename, 'wb') as f:
            f.write(response.content)
    else:
        raise Exception("Failed to download MP3 file")
        
if __name__ == '__main__':
    app.run(debug=True)
