import streamlit as st
import boto3
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
endpoint_name = os.getenv("SAGEMAKER_ENDPOINT_NAME")
aws_region = os.getenv("AWS_REGION")

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

# File uploader for reference speaker
uploaded_audio = st.file_uploader("Upload Audio for Accent Conversion (WAV)", type=["wav"])

# Play the uploaded audio for listening before processing
if uploaded_audio is not None:
    st.audio(uploaded_audio, format="audio/wav")


if st.button("Convert Accent"):
    if uploaded_audio is not None:
        # Read the uploaded file
        audio_bytes = uploaded_audio.read()

        # Send the file to the SageMaker endpoint
        with st.spinner("Processing..."):
            try:
                response = client.invoke_endpoint(
                    EndpointName=endpoint_name,
                    ContentType='audio/wav',
                    Body=audio_bytes  # Pass the audio file bytes
                )

                # Read and clean the result from the response (S3 URL expected)
                result = response['Body'].read().decode('utf-8').strip()

                # Remove any surrounding quotes (in case the URL is returned as a quoted string)
                if result.startswith('"') and result.endswith('"'):
                    result = result[1:-1]

                # Debugging: Display the cleaned response in the Streamlit app
                st.write("SageMaker Response (cleaned and unquoted):", result)

                # Check if the response is a valid S3 URL
                if result.startswith('s3://'):
                    # Parse the S3 bucket and object key from the S3 URL
                    s3_url_parts = result.replace("s3://", "").split("/")
                    bucket_name = s3_url_parts[0]
                    object_key = "/".join(s3_url_parts[1:])

                    # Generate a pre-signed URL to access the S3 object
                    presigned_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': bucket_name, 'Key': object_key},
                        ExpiresIn=3600  # URL expires in 1 hour
                    )

                    # Display the audio player and provide a download link
                    st.audio(presigned_url, format="audio/wav")
                    st.success("Audio conversion complete!")
                    
                    # Provide a download link using the pre-signed URL
                    audio_data = requests.get(presigned_url).content
                    st.download_button("Download Converted Audio", audio_data, file_name="converted_voice.wav")
                else:
                    st.error("Invalid response format from SageMaker. Expected an S3 URL.")
            except Exception as e:
                st.error(f"Error invoking SageMaker endpoint: {str(e)}")
    else:
        st.error("Please upload an audio file.")
