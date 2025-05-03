import os
import config as cfg
from dotenv import load_dotenv
load_dotenv()
origin="http://localhost:5173"  # Replace with the actual origin you want to check

allowed_origin = origin if origin in cfg.FRONTEND_ORIGINS else cfg.FRONTEND_ORIGINS
print(allowed_origin)  # This will print the allowed origin based on the condition