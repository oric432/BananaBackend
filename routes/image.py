import io
import cv2
from PIL import Image
from fastapi import UploadFile, APIRouter, HTTPException
from ..cloud.boto3_client import get_all_images
from ..prediction import predict
import json
import sqlite3
from typing import List
from ..utils.types_utils import ClassificationResult, ImageWithClassification, PaginatedImages, ImageWithMetadata
from datetime import datetime

router = APIRouter(
    prefix="/bananas",
    tags=["bananas"]
)

UPLOAD_DIR = 'uploads'
DATABASE_PATH = "BananaDB.db"


@router.post("/upload_image", response_model=ImageWithClassification)
async def upload_banana_image(file: UploadFile) -> ImageWithClassification:
    """
    Pass image through prediction, get a result, and return an image with classification.
    """

    try:
        # Get file in binary representation
        contents = await file.read()

        # Get model's predictions
        results, image_url, width, height = predict.get_prediction(contents)

        # Transform results to json
        classification_results_json = json.dumps(results)

        classification_results = []
        for index, cls, conf in results:
            classification_results.append(ClassificationResult(index=index, label=cls, confidence=conf))

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        datetime_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("INSERT INTO image_classification (file_name, classification_results, date, width, height)"
                       " VALUES (?, ?, ?, ?, ?)",
                       (image_url, classification_results_json, datetime_now,
                        width, height))
        conn.commit()

        cursor.close()
        conn.close()

        # Return the classification result along with the image bytes
        return ImageWithClassification(date=datetime_now,
                                       image=ImageWithMetadata(url=image_url, width=width, height=height),
                                       classification=classification_results)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all_data", response_model=List[ImageWithClassification])
async def get_all_data() -> List[ImageWithClassification]:
    """
    Retrieve all data from the database and return it.
    """

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Retrieve all data from the table
        cursor.execute("SELECT * FROM image_classification")
        rows = cursor.fetchall()

        parsed_data = []

        for row in rows:
            classification_results = []
            for index, cls, conf in json.loads(row[1]):
                classification_results.append(ClassificationResult(index=index, label=cls, confidence=conf))

            image_classification = ImageWithClassification(
                date=row[2],
                image=ImageWithMetadata(url=row[0], width=row[3], height=row[4]),
                classification=classification_results)
            parsed_data.append(image_classification)

        cursor.close()
        conn.close()

        return parsed_data
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_images", response_model=PaginatedImages)
async def get_images(page: int = 1, per_page: int = 10) -> PaginatedImages:
    images = get_all_images(page, per_page)
    if images:
        return PaginatedImages(images=images)
    else:
        raise HTTPException(status_code=404, detail="No images found")


@router.get("/get_status", response_model=ImageWithClassification)
async def get_banana_status() -> ImageWithClassification:
    """
    Capture image from server's camera, pass through the prediction, and return image with classification.
    """
    # Open the default camera (usually 0)
    cap = cv2.VideoCapture(0)

    # Check if the camera is opened successfully
    if not cap.isOpened():
        print("Error: Could not open camera")

    # Capture a frame
    ret, frame = cap.read()

    # Convert the frame to PIL Image
    image = Image.fromarray(frame)

    # Convert the PIL Image to bytes
    with io.BytesIO() as output:
        image.save(output, format="JPEG")
        image_stream = output.getvalue()

    # Pass the image_stream to the prediction function
    results, image_url, width, height = predict.get_prediction(image_stream)
    # Transform results to json
    classification_results_json = json.dumps(results)

    classification_results = []
    for index, cls, conf in results:
        classification_results.append(ClassificationResult(index=index, label=cls, confidence=conf))

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    datetime_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("INSERT INTO image_classification (file_name, classification_results, date, width, height)"
                   " VALUES (?, ?, ?, ?, ?)",
                   (image_url, classification_results_json, datetime_now,
                    width, height))
    conn.commit()

    cursor.close()
    conn.close()
    cap.release()

    # Return the classification result along with the image bytes
    return ImageWithClassification(date=datetime_now,
                                   image=ImageWithMetadata(url=image_url, width=width, height=height),
                                   classification=classification_results)
