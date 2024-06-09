import io
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os
from utils import image_utils
from utils.types_utils import ImageWithMetadata

# Load environment variables from .env file
load_dotenv()

# Access environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_S3_REGION = os.getenv("AWS_S3_REGION")

s3_client = boto3.client(
    's3',
    region_name=AWS_S3_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)


# Upload image to S3 and return URL
def upload_image(file, file_name):
    try:
        image_stream = io.BytesIO(file)

        # Get width and height for the image
        width, height = image_utils.get_image_dimensions(file)

        # Upload image to S3
        s3_client.put_object(
            Bucket=AWS_S3_BUCKET_NAME,
            Key=file_name,
            Body=image_stream,
            ContentType="image/jpeg",
            Metadata={"width": str(width), "height": str(height)},  # Store dimensions as metadata
        )

        # Generate URL for the uploaded image
        image_url = f'https://{AWS_S3_BUCKET_NAME}.s3.{AWS_S3_REGION}.amazonaws.com/{file_name}'

        return image_url, width, height
    except ClientError as e:
        print(f"Error uploading image: {e}")
        return None


# Get list of all images in S3 bucket
def get_all_images(page=1, per_page=10):
    try:
        images = []
        # Calculate offset
        offset = (page - 1) * per_page

        # List objects with pagination
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(
            Bucket=AWS_S3_BUCKET_NAME
        )

        object_list = []
        for page in page_iterator:
            object_list.extend(page.get('Contents', []))

        for index, obj in enumerate(object_list):
            if index >= offset and len(images) < per_page:
                # Get object metadata
                metadata = s3_client.head_object(
                    Bucket=AWS_S3_BUCKET_NAME,
                    Key=obj['Key']
                )['Metadata']

                # Get dimensions from metadata
                width = metadata.get("width")
                height = metadata.get("height")

                # Generate URL for each object
                image_url = f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_S3_REGION}.amazonaws.com/{obj['Key']}"
                images.append(ImageWithMetadata(url=image_url, width=width, height=height))

        return images

    except ClientError as e:
        print(f"Error fetching images: {e}")
        return None
