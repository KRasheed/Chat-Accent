import streamlit as st
import sounddevice as sd
import wavio
import tempfile
import os
import boto3
import requests
import json
from pydub import AudioSegment
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Get environment variables
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
endpoint_name = os.getenv("SAGEMAKER_ENDPOINT_NAME")
aws_region = os.getenv("AWS_REGION")
s3_bucket_name = os.getenv("S3_BUCKET_NAME")

# Initialize the SageMaker runtime client
client = boto3.client('sagemaker-runtime',
                      region_name=aws_region,
                      aws_access_key_id=aws_access_key_id, 
                      aws_secret_access_key=aws_secret_access_key)

# Initialize the S3 client
s3_client = boto3.client('s3',
                         region_name=aws_region,
                         aws_access_key_id=aws_access_key_id, 
                         aws_secret_access_key=aws_secret_access_key)

# st.title("Accent Conversion with Streamlit and SageMaker")

# # File uploader for audio files
# uploaded_audio = st.file_uploader("Upload Audio for Accent Conversion (MP3, MP4, WAV)", type=["mp3", "mp4", "wav"])

# # Play the uploaded audio for listening before processing
# if uploaded_audio is not None:
#     st.audio(uploaded_audio)

# def convert_to_wav(uploaded_audio):
#     # Create a temporary file to hold the converted WAV
#     temp_wav_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")

#     # Check the MIME type and handle accordingly
#     if uploaded_audio.type == "audio/mpeg":  # This is the correct MIME type for mp3
#         audio = AudioSegment.from_mp3(uploaded_audio)
#     elif uploaded_audio.type == "audio/mp4":
#         audio = AudioSegment.from_file(uploaded_audio, format="mp4")
#     elif uploaded_audio.type == "audio/wav":
#         return uploaded_audio  # No conversion needed for WAV
#     else:
#         st.error(f"Unsupported audio format: {uploaded_audio.type}")
#         return None

#     # Export audio to WAV
#     audio.export(temp_wav_file.name, format="wav")
    
#     return temp_wav_file.name



# def upload_to_s3(file_path, bucket_name, file_key):
#     """Uploads a file to the specified S3 bucket."""
#     try:
#         with open(file_path, "rb") as file:
#             s3_client.upload_fileobj(file, bucket_name, file_key)
#         s3_url = f's3://{bucket_name}/{file_key}'
#         return s3_url
#     except Exception as e:
#         st.error(f"Failed to upload to S3: {str(e)}")
#         return None

# accent = st.selectbox(
#     "Select Accent:",
#     ["British", "American"]
# )

# # Map the selected accent to the corresponding language code
# language_mapping = {
#     "British": "en-br",
#     "American": "en-us"
# }

# language = language_mapping[accent]

# if st.button("Convert Accent"):
#     if uploaded_audio is not None:
#         with st.spinner("Converting audio to WAV format..."):
#             wav_audio_path = convert_to_wav(uploaded_audio)

#         if wav_audio_path:
#             s3_object_name = f"input-audio/{os.path.basename(wav_audio_path)}"

#             with st.spinner("Uploading audio to S3..."):
#                 s3_url = upload_to_s3(wav_audio_path, s3_bucket_name, s3_object_name)

#             if s3_url:
#                 st.success(f"Audio uploaded to S3 at {s3_url}")

#                 # Create the JSON payload with both the audio URL and selected language
#                 payload = {
#                     "audio_url": s3_url,
#                     "language": language
#                 }

#                 with st.spinner("Processing..."):
#                     try:
#                         # Invoke the SageMaker endpoint with the updated payload
#                         response = client.invoke_endpoint(
#                             EndpointName=endpoint_name,
#                             ContentType='application/json',
#                             Body=json.dumps(payload)
#                         )

#                         result = response['Body'].read().decode('utf-8').strip()

#                         if result.startswith('"') and result.endswith('"'):
#                             result = result[1:-1]

#                         st.write("SageMaker Response (cleaned):", result)

#                         if result.startswith('s3://'):
#                             s3_url_parts = result.replace("s3://", "").split("/")
#                             result_bucket_name = s3_url_parts[0]
#                             result_object_key = "/".join(s3_url_parts[1:])

#                             presigned_url = s3_client.generate_presigned_url(
#                                 'get_object',
#                                 Params={'Bucket': result_bucket_name, 'Key': result_object_key},
#                                 ExpiresIn=3600
#                             )

#                             st.audio(presigned_url, format="audio/wav")
#                             st.success("Audio conversion complete!")

#                             audio_data = requests.get(presigned_url).content
#                             st.download_button("Download Converted Audio", audio_data, file_name="converted_voice.wav")
#                         else:
#                             st.error("Invalid response format from SageMaker. Expected an S3 URL.")
#                     except Exception as e:
#                         st.error(f"Error invoking SageMaker endpoint: {str(e)}")
#             else:
#                 st.error("Failed to upload audio to S3.")
#         else:
#             st.error("Failed to convert audio to WAV.")
#     else:
#         st.error("Please upload an audio file.")

# Global variable to store audio recording
is_recording = False
recording_data = None

# Function to start recording audio
def start_recording(sample_rate=44100):
    global is_recording, recording_data
    is_recording = True
    st.write("Recording... Click Stop Recording to finish.")
    recording_data = sd.rec(int(30 * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()  # Recording for a max of 30 seconds, but can be stopped manually
    return recording_data, sample_rate

# Function to stop recording audio
def stop_recording():
    global is_recording
    if is_recording:
        sd.stop()
        is_recording = False
        st.success("Recording stopped.")

# Function to save audio recording to a file
def save_audio(filename, recording, sample_rate):
    wavio.write(filename, recording, sample_rate, sampwidth=2)  # Save as WAV file

# Function to upload audio to S3
def upload_to_s3(file_path, bucket_name, object_name):
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(file_path, bucket_name, object_name)
        s3_url = f"s3://{bucket_name}/{object_name}"
        return s3_url
    except Exception as e:
        st.error(f"Error uploading to S3: {str(e)}")
        return None

# Function to convert uploaded audio to WAV format
def convert_to_wav(uploaded_audio):
    temp_wav_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")

    if uploaded_audio.type == "audio/mpeg":
        audio = AudioSegment.from_mp3(uploaded_audio)
    elif uploaded_audio.type == "audio/mp4":
        audio = AudioSegment.from_file(uploaded_audio, format="mp4")
    elif uploaded_audio.type == "audio/wav":
        return uploaded_audio
    else:
        st.error(f"Unsupported audio format: {uploaded_audio.type}")
        return None

    audio.export(temp_wav_file.name, format="wav")
    return temp_wav_file.name

# Streamlit app logic
st.title("Accent Conversion Application")

# Audio input method selection
audio_option = st.radio("Choose how to provide the audio:", ("Upload Audio File", "Record Audio"))

uploaded_audio = None
if audio_option == "Upload Audio File":
    uploaded_audio = st.file_uploader("Upload an audio file", type=["mp3", "wav", "mp4"])
elif audio_option == "Record Audio":
    if st.button("Start Recording"):
        recording_data, sample_rate = start_recording()
    
    if st.button("Stop Recording"):
        stop_recording()
        save_audio("recorded_audio.wav", recording_data, sample_rate)
        st.audio("recorded_audio.wav", format="audio/wav")
        uploaded_audio = "recorded_audio.wav"

# Language selection dropdown
language = st.selectbox("Select Accent", options=["British", "American"])

# Map selected accent to the corresponding language code
language_code = "en-br" if language == "British" else "en-us"


# Button to convert the accent
if st.button("Convert Accent"):
    if uploaded_audio is not None:
        if audio_option == "Upload Audio File" and uploaded_audio is not None:
            with st.spinner("Converting uploaded audio to WAV format..."):
                wav_audio_path = convert_to_wav(uploaded_audio)
        elif audio_option == "Record Audio" and uploaded_audio is not None:
            with st.spinner("Saving recorded audio..."):
                wav_audio_path = uploaded_audio  # recorded_audio.wav is saved earlier

        if wav_audio_path:
            # Upload the audio file to S3
            s3_object_name = f"input-audio/{os.path.basename(wav_audio_path)}"
            with st.spinner("Uploading audio to S3..."):
                s3_url = upload_to_s3(wav_audio_path, s3_bucket_name, s3_object_name)

            if s3_url:
                st.success(f"Audio uploaded to S3 at {s3_url}")

                # Create payload with both audio URL and language code
                payload = {
                    'audio_url': s3_url,
                    'language': language_code
                }

                with st.spinner("Processing..."):
                    try:
                        # Invoke SageMaker endpoint
                        response = client.invoke_endpoint(
                            EndpointName=endpoint_name,
                            ContentType='application/json',
                            Body=json.dumps(payload)
                        )

                        # Process and clean up the response
                        result = response['Body'].read().decode('utf-8').strip()

                        if result.startswith('"') and result.endswith('"'):
                            result = result[1:-1]

                        st.write("SageMaker Response (cleaned):", result)

                        # Check if the result is an S3 URL to the converted audio
                        if result.startswith('s3://'):
                            s3_url_parts = result.replace("s3://", "").split("/")
                            result_bucket_name = s3_url_parts[0]
                            result_object_key = "/".join(s3_url_parts[1:])

                            # Generate a presigned URL to play and download the converted audio
                            presigned_url = s3_client.generate_presigned_url(
                                'get_object',
                                Params={'Bucket': result_bucket_name, 'Key': result_object_key},
                                ExpiresIn=3600
                            )

                            st.audio(presigned_url, format="audio/wav")
                            st.success("Audio conversion complete!")

                            # Provide a download button for the converted audio
                            audio_data = requests.get(presigned_url).content
                            st.download_button("Download Converted Audio", audio_data, file_name="converted_voice.wav")
                        else:
                            st.error("Invalid response format from SageMaker. Expected an S3 URL.")
                    except Exception as e:
                        st.error(f"Error invoking SageMaker endpoint: {str(e)}")
            else:
                st.error("Failed to upload audio to S3.")
        else:
            st.error("Failed to convert audio to WAV.")
    else:
        st.error("Please upload or record an audio file.")
