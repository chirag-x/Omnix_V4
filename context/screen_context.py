# Omnix V4 module
from loguru import logger


class ScreenContext:

    def __init__(self):

        logger.info("Initializing Screen Context")

        self.ui_graph = []

    def update(self, analysis):

        if not analysis:
            return

        texts = analysis.get("texts", [])
        objects = analysis.get("objects", [])

        nodes = []

        for t in texts:

            nodes.append({
                "type": "text",
                "label": t.get("text"),
                "x": t.get("x"),
                "y": t.get("y")
            })

        for obj in objects:

            bbox = obj.get("bbox", [0, 0, 0, 0])

            x = (bbox[0] + bbox[2]) / 2
            y = (bbox[1] + bbox[3]) / 2

            nodes.append({
                "type": obj.get("type"),
                "label": obj.get("type"),
                "x": x,
                "y": y
            })

        self.ui_graph = nodes

    def get_nodes(self):

        return self.ui_graph

    def find_near(self, label, radius=120):

        matches = []

        for node in self.ui_graph:

            if label.lower() in str(node.get("label", "")).lower():

                x = node["x"]
                y = node["y"]

                for other in self.ui_graph:

                    dx = abs(other["x"] - x)
                    dy = abs(other["y"] - y)

                    if dx < radius and dy < radius and other != node:

                        matches.append(other)

        return matches

    def find_by_label(self, label):

        for node in self.ui_graph:

            if label.lower() in str(node.get("label", "")).lower():
                return node

        return None
