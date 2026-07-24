# Omnix V4 module
import os
import shutil
from loguru import logger


class FileController:

    @staticmethod
    def create_file(path):

        logger.info(f"Creating file: {path}")

        open(path, "w").close()

        return "success"

    @staticmethod
    def delete_file(path):

        logger.info(f"Deleting file: {path}")

        os.remove(path)

        return "success"

    @staticmethod
    def move_file(src, dst):

        logger.info(f"Moving file from {src} to {dst}")

        shutil.move(src, dst)

        return "success"

    @staticmethod
    def list_files(folder):

        logger.info(f"Listing files in {folder}")

        return os.listdir(folder)

    @staticmethod
    def search_file(filename, root="C:/Users"):

        logger.info(f"Searching for file: {filename}")

        matches = []

        for root_dir, dirs, files in os.walk(root):

            if filename in files:
                matches.append(os.path.join(root_dir, filename))

        return matches