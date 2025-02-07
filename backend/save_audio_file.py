import argparse
import os

# overwrite env variable
os.environ['POSTGRES_HOST'] = 'localhost'

from db import session
from crud.crud_audio import crud_audio

def save_blob_to_file(output_file, id):
    # Get the database session without using context manager
    db = next(session.get_db())
    try:
        audio = crud_audio.get(db, id)

        if audio:
            waveform = audio.waveform
            original_waveform = audio.original_waveform

            # Prepend filename with 'original_' from output_file path into original_path
            original_path = os.path.join(os.path.dirname(output_file), 'original_' + os.path.basename(output_file))
            # Write the BLOB data to a file
            with open(output_file, "wb") as file:
                file.write(waveform)
            with open(original_path, "wb") as file:
                file.write(original_waveform)
            
            print(f"BLOB data saved to {output_file}")
        else:
            print(f"No data found for the filename: {id}")
    finally:
        db.close()

if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(description="Save a BLOB from SQLite to a file.")
    parser.add_argument("--id", required=True, help="The id to query in the database.")
    
    # Parse arguments
    args = parser.parse_args()

    # Call the function with the command-line argument
    save_blob_to_file("../data/" + args.id + '.wav', args.id)
