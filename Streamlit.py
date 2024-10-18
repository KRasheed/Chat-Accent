# import streamlit as st
# import boto3
# import requests
# import os
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# # Get environment variables
# aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
# aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
# endpoint_name = os.getenv("SAGEMAKER_ENDPOINT_NAME")
# aws_region = os.getenv("AWS_REGION")

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

# # File uploader for reference speaker
# uploaded_audio = st.file_uploader("Upload Audio for Accent Conversion (WAV)", type=["wav"])

# # Play the uploaded audio for listening before processing
# if uploaded_audio is not None:
#     st.audio(uploaded_audio, format="audio/wav")


# if st.button("Convert Accent"):
#     if uploaded_audio is not None:
#         # Read the uploaded file
#         audio_bytes = uploaded_audio.read()

#         # Send the file to the SageMaker endpoint
#         with st.spinner("Processing..."):
#             try:
#                 response = client.invoke_endpoint(
#                     EndpointName=endpoint_name,
#                     ContentType='audio/wav',
#                     Body=audio_bytes  # Pass the audio file bytes
#                 )

#                 # Read and clean the result from the response (S3 URL expected)
#                 result = response['Body'].read().decode('utf-8').strip()

#                 # Remove any surrounding quotes (in case the URL is returned as a quoted string)
#                 if result.startswith('"') and result.endswith('"'):
#                     result = result[1:-1]

#                 # Debugging: Display the cleaned response in the Streamlit app
#                 st.write("SageMaker Response (cleaned and unquoted):", result)

#                 # Check if the response is a valid S3 URL
#                 if result.startswith('s3://'):
#                     # Parse the S3 bucket and object key from the S3 URL
#                     s3_url_parts = result.replace("s3://", "").split("/")
#                     bucket_name = s3_url_parts[0]
#                     object_key = "/".join(s3_url_parts[1:])

#                     # Generate a pre-signed URL to access the S3 object
#                     presigned_url = s3_client.generate_presigned_url(
#                         'get_object',
#                         Params={'Bucket': bucket_name, 'Key': object_key},
#                         ExpiresIn=3600  # URL expires in 1 hour
#                     )

#                     # Display the audio player and provide a download link
#                     st.audio(presigned_url, format="audio/wav")
#                     st.success("Audio conversion complete!")
                    
#                     # Provide a download link using the pre-signed URL
#                     audio_data = requests.get(presigned_url).content
#                     st.download_button("Download Converted Audio", audio_data, file_name="converted_voice.wav")
#                 else:
#                     st.error("Invalid response format from SageMaker. Expected an S3 URL.")
#             except Exception as e:
#                 st.error(f"Error invoking SageMaker endpoint: {str(e)}")
#     else:
#         st.error("Please upload an audio file.")
import streamlit as st
import boto3
import os
import json
from dotenv import load_dotenv
import requests

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

# File uploader for reference speaker
uploaded_audio = st.file_uploader("Upload Audio for Accent Conversion (WAV)", type=["wav"])

# Play the uploaded audio for listening before processing
if uploaded_audio is not None:
    st.audio(uploaded_audio, format="audio/wav")


def upload_to_s3(file, bucket_name, file_key):
    """Uploads a file to the specified S3 bucket."""
    try:
        # Directly upload the file object (BytesIO) from Streamlit to S3
        s3_client.upload_fileobj(file, bucket_name, file_key)
        
        # Generate the S3 URL in the 's3://' format
        s3_url = f's3://{bucket_name}/{file_key}'
        return s3_url
    except Exception as e:
        st.error(f"Failed to upload to S3: {str(e)}")
        return None


if st.button("Convert Accent"):
    if uploaded_audio is not None:
        # Define the S3 file key (this will be the path in the S3 bucket)
        s3_object_name = f"input-audio/{uploaded_audio.name}"  # S3 object name (e.g., input-audio/segment_4_converted.wav)
        
        # Upload the file to S3
        with st.spinner("Uploading audio to S3..."):
            s3_url = upload_to_s3(uploaded_audio, s3_bucket_name, s3_object_name)

        if s3_url:
            st.success(f"Audio uploaded to S3 at {s3_url}")

            # Prepare the payload with the S3 URL in 's3://' format
            payload = {
                'audio_url': s3_url  # e.g., 's3://chataccent-v1/input-audio/segment_4_converted.wav'
            }

            # Send the payload to the SageMaker endpoint
            with st.spinner("Processing..."):
                try:
                    response = client.invoke_endpoint(
                        EndpointName=endpoint_name,
                        ContentType='application/json',  # JSON format for the payload
                        Body=json.dumps(payload)  # Convert the payload to JSON
                    )

                    # Read and clean the result from the response
                    result = response['Body'].read().decode('utf-8').strip()

                    # Debugging: Display the cleaned response in the Streamlit app
                    st.write("SageMaker Response:", result)

                    # Check if the response is a valid S3 URL
                    if result.startswith('s3://'):
                        # Parse the S3 bucket and object key from the S3 URL
                        s3_url_parts = result.replace("s3://", "").split("/")
                        result_bucket_name = s3_url_parts[0]
                        result_object_key = "/".join(s3_url_parts[1:])

                        # Generate a pre-signed URL to access the S3 object
                        presigned_url = s3_client.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': result_bucket_name, 'Key': result_object_key},
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
            st.error("Failed to upload audio to S3.")
    else:
        st.error("Please upload an audio file.")
