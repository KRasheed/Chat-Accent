# import streamlit as st
# import tempfile
# import os
# import boto3
# import requests
# import json
# from pydub import AudioSegment
# from dotenv import load_dotenv


# # Load environment variables from .env file
# load_dotenv()

# # Get environment variables
# aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
# aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
# endpoint_name = os.getenv("SAGEMAKER_ENDPOINT_NAME")
# aws_region = os.getenv("AWS_REGION")
# s3_bucket_name = os.getenv("S3_BUCKET_NAME")

# # Initialize the SageMaker runtime client
# client = boto3.client('sagemaker-runtime',
#                       region_name=aws_region,
#                       aws_access_key_id=aws_access_key_id, 
#                       aws_secret_access_key=aws_secret_access_key)

# # Initialize the S3 client
# s3_client = boto3.client('s3',
#                          region_name=aws_region,
#                          aws_access_key_id=aws_access_key_id, 
#                          aws_secret_access_key=aws_secret_access_key)

# st.title("Accent Conversion with Streamlit and SageMaker")

# # File uploader for audio files
# uploaded_audio = st.file_uploader("Upload Audio for Accent Conversion (MP3, MP4, WAV)", type=["mp3", "mp4", "wav"])

# # Play the uploaded audio for listening before processing
# if uploaded_audio is not None:
#     st.audio(uploaded_audio)

# def convert_to_wav(uploaded_audio):
#     # Create a temporary file to hold the WAV file
#     temp_wav_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    
#     # Check the MIME type and handle accordingly
#     if uploaded_audio.type == "audio/wav":  # WAV file, no conversion needed
#         with open(temp_wav_file.name, 'wb') as f:
#             f.write(uploaded_audio.read())  # Save the uploaded WAV file
#         return temp_wav_file.name
#     elif uploaded_audio.type == "audio/mpeg":  # MP3 file
#         audio = AudioSegment.from_mp3(uploaded_audio)
#     elif uploaded_audio.type == "audio/mp4":  # MP4 file
#         audio = AudioSegment.from_file(uploaded_audio, format="mp4")
#     else:
#         st.error(f"Unsupported audio format: {uploaded_audio.type}")
#         return None

#     # Export audio to WAV format if conversion is needed
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

import streamlit as st
import tempfile
import os
import boto3
import requests
import json
from pydub import AudioSegment
from dotenv import load_dotenv
from st_audiorec import st_audiorec  # Import the audio recorder component

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

st.title("Accent Conversion with Streamlit and SageMaker")

# Step 1: Ask the user to choose between recording or uploading
st.header("Record or Upload Audio")

choice = st.radio("Choose how to provide audio:", ("Record Audio", "Upload Audio"))

# Initialize variables to store the audio data
wav_audio_data = None
uploaded_audio = None

# Step 2: Show the audio recorder or file uploader based on the user's choice
if choice == "Record Audio":
    wav_audio_data = st_audiorec()  # Use the audio recorder
    if wav_audio_data is not None:
        st.audio(wav_audio_data, format='audio/wav')  # Play back the recorded audio
elif choice == "Upload Audio":
    uploaded_audio = st.file_uploader("Upload Audio for Accent Conversion (MP3, MP4, WAV)", type=["mp3", "mp4", "wav"])
    if uploaded_audio is not None:
        st.audio(uploaded_audio)  # Play back the uploaded audio

# Helper function to convert uploaded audio to WAV if needed
def convert_to_wav(uploaded_audio):
    temp_wav_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    
    if uploaded_audio.type == "audio/wav":
        with open(temp_wav_file.name, 'wb') as f:
            f.write(uploaded_audio.read())  # Save the uploaded WAV file
        return temp_wav_file.name
    elif uploaded_audio.type == "audio/mpeg":
        audio = AudioSegment.from_mp3(uploaded_audio)
    elif uploaded_audio.type == "audio/mp4":
        audio = AudioSegment.from_file(uploaded_audio, format="mp4")
    else:
        st.error(f"Unsupported audio format: {uploaded_audio.type}")
        return None

    audio.export(temp_wav_file.name, format="wav")
    
    return temp_wav_file.name

def upload_to_s3(file_path, bucket_name, file_key):
    """Uploads a file to the specified S3 bucket."""
    try:
        with open(file_path, "rb") as file:
            s3_client.upload_fileobj(file, bucket_name, file_key)
        s3_url = f's3://{bucket_name}/{file_key}'
        return s3_url
    except Exception as e:
        st.error(f"Failed to upload to S3: {str(e)}")
        return None

# Accent selection
accent = st.selectbox(
    "Select Accent:",
    ["British", "American"]
)

# Map the selected accent to the corresponding language code
language_mapping = {
    "British": "en-br",
    "American": "en-us"
}

language = language_mapping[accent]

# Conversion button and logic
if st.button("Convert Accent"):
    if uploaded_audio is not None or wav_audio_data is not None:
        if wav_audio_data is not None:
            # Save the recorded audio as a WAV file
            wav_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            with open(wav_audio_path, 'wb') as f:
                f.write(wav_audio_data)  # Save the recorded audio data

        elif uploaded_audio is not None:
            with st.spinner("Converting audio to WAV format..."):
                wav_audio_path = convert_to_wav(uploaded_audio)

        if wav_audio_path:
            s3_object_name = f"input-audio/{os.path.basename(wav_audio_path)}"

            with st.spinner("Uploading audio to S3..."):
                s3_url = upload_to_s3(wav_audio_path, s3_bucket_name, s3_object_name)

            if s3_url:
                st.success(f"Audio uploaded to S3 at {s3_url}")

                # Create the JSON payload with both the audio URL and selected language
                payload = {
                    "audio_url": s3_url,
                    "language": language
                }

                with st.spinner("Processing..."):
                    try:
                        # Invoke the SageMaker endpoint with the updated payload
                        response = client.invoke_endpoint(
                            EndpointName=endpoint_name,
                            ContentType='application/json',
                            Body=json.dumps(payload)
                        )

                        result = response['Body'].read().decode('utf-8').strip()

                        if result.startswith('"') and result.endswith('"'):
                            result = result[1:-1]

                        st.write("SageMaker Response (cleaned):", result)

                        if result.startswith('s3://'):
                            s3_url_parts = result.replace("s3://", "").split("/")
                            result_bucket_name = s3_url_parts[0]
                            result_object_key = "/".join(s3_url_parts[1:])

                            presigned_url = s3_client.generate_presigned_url(
                                'get_object',
                                Params={'Bucket': result_bucket_name, 'Key': result_object_key},
                                ExpiresIn=3600
                            )

                            st.audio(presigned_url, format="audio/wav")
                            st.success("Audio conversion complete!")

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
