import pandas as pd
import sqlite3

# Define file paths
hd_file = "HD.dat"
en_file = "EN.dat"
db_file = "USState.db"

# Load the hd.dat file with specified dtype
hd_columns = list(range(10))  # Adjust as needed
hd_df = pd.read_csv(hd_file, delimiter='|', header=None, usecols=hd_columns, dtype=str)

# Filter rows where the 6th column (index 5) contains 'A'
filtered_hd_df = hd_df[hd_df[5] == 'A']

# Get unique identifiers from the 2nd column (index 1)
unique_ids = set(filtered_hd_df[1])

# Load the en.dat file with specified dtype
en_columns = list(range(20))  # Adjust as needed
en_df = pd.read_csv(en_file, delimiter='|', header=None, usecols=en_columns, dtype=str)

# Filter en.dat where the 2nd column (index 1) matches unique_ids
filtered_en_df = en_df[en_df[1].isin(unique_ids)]

# Select the 5th (index 4) and 18th (index 17) columns and rename them
output_df = filtered_en_df[[4, 17]]
output_df.columns = ["call", "state"]

# Save to SQLite database
conn = sqlite3.connect(db_file)
output_df.to_sql("USState", conn, if_exists="replace", index=False)
conn.close()

print("Data successfully saved to USState.db in the USState table.")

