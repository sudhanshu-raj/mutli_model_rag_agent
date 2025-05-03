import whisper
import shutil
import os

# # Clear the cache directory
# cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "whisper")
# if os.path.exists(cache_dir):
#     shutil.rmtree(cache_dir)
#     print(f"Cleared Whisper cache at: {cache_dir}")

# # Create fresh directory
# os.makedirs(cache_dir, exist_ok=True)

# Use a path without spaces or special characters
custom_path = r"C:\ai_models\whisper"
model = whisper.load_model("medium", download_root=custom_path)
audio_file = r"C:\Users\rajsu\OneDrive\Documents\Sound Recordings\Recording (7).m4a"
result = model.transcribe(audio_file)
print("Detected Language:", result["language"])
print("Transcription:", result["text"])
