
import shutil
import os

def remove_files(output_path):
    if os.path.exists(output_path):
        try:
            if os.path.isdir(output_path):
                shutil.rmtree(output_path)  # Remove directory and all its contents
                print(f"Removed directory: {output_path}")
            else:
                os.remove(output_path)  # Remove single file
                print(f"Removed file: {output_path}")
        except Exception as cleanup_error:
            print(f"Error cleaning up output: {cleanup_error}")
    else:
        print(f"Output path does not exist: {output_path}")
