# Omnix V4 module
from ultralytics import YOLO
from loguru import logger
import numpy as np
from pathlib import Path


class UIDetector:

    def __init__(self):

        logger.info("Loading YOLO vision model")

        model_path = "vision/models/yolov8n.pt"
        self.model = YOLO(model_path)

    def detect(self, frame):

        # Ensure frame has 3 channels
        if frame.shape[2] == 4:
            frame = frame[:, :, :3]

        results = self.model(frame)

        objects = []

        for r in results:
            boxes = r.boxes

            for box in boxes:

                cls = int(box.cls[0])
                conf = float(box.conf[0])

                # Ignore weak detections
                if conf < 0.4:
                    continue

                name = self.model.names[cls]

                bbox = box.xyxy[0].tolist()

                # Calculate center coordinates
                x = (bbox[0] + bbox[2]) / 2
                y = (bbox[1] + bbox[3]) / 2

                width = abs(bbox[2] - bbox[0])
                height = abs(bbox[3] - bbox[1])

                objects.append({
                    "type": name,
                    "confidence": conf,
                    "bbox": bbox,
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height
                })

        return objects
