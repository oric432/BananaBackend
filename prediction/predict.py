from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator
from PIL import Image
import uuid
import io
import numpy as np
from cloud import boto3_client


class_color_mapping = {
    "freshripe": (200, 255, 0),  # Yellow
    "freshunripe": (0, 255, 0),  # Green
    "overripe": (255, 165, 0),  # Orange
    "ripe": (255, 215, 0),  # Gold
    "rotten": (128, 0, 0),  # Dark Red
    "unripe": (0, 128, 0)  # Dark Green
}


def get_prediction(image_path):
    # Load a prediction
    model = YOLO('../runs/detect/train3/weights/best.pt')
    classes = model.names

    # Make it a stream
    image_stream = io.BytesIO(image_path)

    # Load the image
    image = Image.open(image_stream)

    # Transform to np array
    image_np = np.array(image)

    # Run inference on the image
    results = model.track(image_np, verbose=False)

    # (index, classification, prediction confidence)
    result_list = []

    # File name
    random_uuid = str(uuid.uuid4())

    # Process results generator
    predictions = results[0].boxes
    boxes = results[0].boxes.xywh.cpu()
    clss = results[0].boxes.cls.cpu().tolist()
    annotator = Annotator(image, line_width=5, font_size=30)

    i = 0
    for prediction, box, cls in zip(predictions, boxes, clss):
        result_list.append((i, classes[int(prediction.cls.item())], prediction.conf.item()))
        x, y, w, h = box
        label = str(i)
        i += 1
        x1, y1, x2, y2 = x - w / 2, y - h / 2, x + w / 2, y + h / 2
        annotator.box_label([x1, y1, x2, y2], label=label, color=class_color_mapping[result_list[i - 1][1]])

    # Get the annotated image
    annotated_image = annotator.result()

    # Convert the annotated image to a PIL image
    annotated_image_pil = Image.fromarray(annotated_image.__array__())

    # Convert the color mode to RGB
    annotated_image_rgb = annotated_image_pil.convert("RGB")

    # Save the annotated image to a BytesIO object
    annotated_image_stream = io.BytesIO()
    annotated_image_rgb.save(annotated_image_stream, format="JPEG")

    image_url, width, height = boto3_client.upload_image(annotated_image_stream.getvalue(), f'{random_uuid}.jpg')

    return result_list, image_url, width, height
