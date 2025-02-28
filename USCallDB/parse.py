import os
import requests
import zipfile
import pandas as pd
import sqlite3
import tempfile
import shutil
from io import BytesIO

def download_and_unzip(url):
    """
    Downloads a ZIP file from the given URL and extracts it into a temporary directory.
    """
    try:
        extract_dir = tempfile.mkdtemp()  # Create a persistent temporary directory

        # Download the ZIP file
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        
        # Open the ZIP file from the response content
        with zipfile.ZipFile(BytesIO(response.content), 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        print(f"Files extracted to: {extract_dir}")
        
        return extract_dir  # Return the persistent directory path
    
    except requests.RequestException as e:
        print(f"Download error: {e}")
    except zipfile.BadZipFile:
        print("Error: The downloaded file is not a valid ZIP archive.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def process_fcc_data(hd_file, en_file, db_file):
    """
    Processes FCC data files in chunks and saves the filtered data to an SQLite database.
    
    Parameters:
    hd_file (str): Path to the HD.dat file.
    en_file (str): Path to the EN.dat file.
    db_file (str): Path to the SQLite database file.
    """
    # Load and filter the HD.dat file in chunks
    hd_columns = list(range(10))  # Adjust as needed
    unique_ids = set()

    chunk_size = 100000  # Process 100,000 rows at a time

    for chunk in pd.read_csv(hd_file, delimiter='|', header=None, usecols=hd_columns, dtype=str, chunksize=chunk_size):
        filtered_chunk = chunk[chunk[5] == 'A']
        unique_ids.update(filtered_chunk[1])

    # Convert unique_ids to a list for efficient lookup
    unique_ids = list(unique_ids)

    # Load and filter the EN.dat file in chunks
    en_columns = list(range(20))  # Adjust as needed
    output_df_list = []

    for chunk in pd.read_csv(en_file, delimiter='|', header=None, usecols=en_columns, dtype=str, chunksize=chunk_size):
        filtered_chunk = chunk[chunk[1].isin(unique_ids)]
        output_df_list.append(filtered_chunk[[4, 17]])  # Keep only needed columns

    # Combine all chunks and rename columns
    if output_df_list:
        output_df = pd.concat(output_df_list, ignore_index=True)
        output_df.columns = ["call", "state"]

        # Save to SQLite database in the current working directory
        db_file = os.path.join(os.getcwd(), "USState.db")
        conn = sqlite3.connect(db_file)
        output_df.to_sql("USState", conn, if_exists="replace", index=False, dtype={"call": "TEXT", "state": "TEXT"}, chunksize=1000)
        conn.close()

        print(f"Data successfully saved to {db_file} in the USState table.")
    else:
        print("No matching records found in EN.dat.")

# Example usage
if __name__ == "__main__":
    zip_url = "https://data.fcc.gov/download/pub/uls/complete/l_amat.zip"  # Replace with the actual URL
    extracted_dir = download_and_unzip(zip_url)
    
    if extracted_dir:
        # Define file paths
        hd_file = os.path.join(extracted_dir, "HD.dat")
        en_file = os.path.join(extracted_dir, "EN.dat")
        
        # Process the extracted FCC data
        if os.path.exists(hd_file) and os.path.exists(en_file):
            process_fcc_data(hd_file, en_file, "USState.db")
        else:
            print("Required files HD.dat and EN.dat not found in the extracted directory.")
        
        # Clean up temporary directory
        shutil.rmtree(extracted_dir)
        print(f"Temporary directory {extracted_dir} deleted.")

