import os
import google.generativeai as genai

import json
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])


def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini.

    See https://ai.google.dev/gemini-api/docs/prompting_with_media
    """
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file


def generate_image_title_dscrpt(image_path):
    # Create the model
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config,
        system_instruction='''analyze this image, give me title and description in json format, description should be short like this
         {
         "title":"title of image",
         "description":"short description of image"
         }
           ''',
    )

    # TODO Make these files available on the local file system
    # You may need to update the file paths
    files = [
        upload_to_gemini(image_path,
                         mime_type="image/png"),
    ]

    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    files[0]
                ]
            }

        ]
    )

    try:
        response = chat_session.send_message(
            """Analyze this image and follow the system instruction """
        )

        # Clean the response
        json_str = response.text.replace(
            '```json', '').replace('```', '').strip()

        # Parse with detailed error info
        result = json.loads(json_str)
        return {  # Ensure consistent structure
            "title": result.get("title", "Untitled"),
            "description": result.get("description", "No description"),
        }

    except json.JSONDecodeError as e:
        print(f"JSON Error: {e}\nResponse was: {response.text}")
        return {
            "title": "Untitled",
            "description": "No description available",
            "error": f"Invalid JSON: {str(e)}",
            "raw_response": response.text  # For debugging
        }
    except AttributeError as e:
        print(f"Empty response: {e}")
        return {
            "title": "Untitled",
            "description": "No response from API",
            "error": str(e)
        }


if __name__ == "__main__":
    result = generate_image_title_dscrpt(
        r"C:\Users\rajsu\OneDrive\Pictures\Screenshots\Screenshot 2025-01-30 120555.png")
    print(result)
