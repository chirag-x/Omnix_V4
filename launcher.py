import os
import sys

# Redirect __pycache__
os.environ["PYTHONPYCACHEPREFIX"] = "temp/pycache"

os.makedirs("temp/pycache", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Ensure project root in path
sys.path.append(os.getcwd())

from main import main

if __name__ == "__main__":
    main()