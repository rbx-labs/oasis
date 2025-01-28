import sqlite3
import argparse

def save_blob_to_file(database_path, table_name, blob_column, output_file, filename):
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Query to fetch the BLOB data
        query = f"SELECT {blob_column} FROM {table_name} WHERE filename = ?"
        cursor.execute(query, (filename,))

        # Fetch the result
        result = cursor.fetchone()
        if result and result[0]:
            blob_data = result[0]

            # Write the BLOB data to a file
            with open(output_file, "wb") as file:
                file.write(blob_data)
            
            print(f"BLOB data saved to {output_file}")
        else:
            print(f"No data found for the filename: {filename}")
    
    except sqlite3.Error as e:
        print(f"Error: {e}")
    
    finally:
        # Close the connection
        if conn:
            conn.close()

if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(description="Save a BLOB from SQLite to a file.")
    parser.add_argument("--filename", required=True, help="The filename to query in the database.")
    
    # Parse arguments
    args = parser.parse_args()

    # Path to your SQLite database
    database_path = "./data/sql_app.db"

    # Table containing the BLOB
    table_name = "audios"

    # Column with the BLOB data
    blob_column = "waveform"

    # Call the function with the command-line argument
    save_blob_to_file(database_path, table_name, blob_column, "./data/" + args.filename, args.filename)
