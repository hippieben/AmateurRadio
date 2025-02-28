parse.py a python script to download and parse FCC Amateur Radio License Data and select only active licenses and output the Callsign and the State into a sqlite db for use with WSJT-Z.  The maintainer of this software mistakenly includes call data that is not the active call, creating instances where a callsign will have several records from previous license grants, and thus state decodes that are incorrect.
The latest version downloads the FCC data for you and unzips it and cleans up the temp files after processing.  It will leave the new sqlite database in the current working directory.

Step 1: run python parse.py

Step 2: validate the output of the new sqlitedb with the sqlite.   sqlite USState.db        sqlite> select * from USState;  The resulting data should be formatted call|state

Step 3: replace the existing USState.db file in your share/wsjtx directory



I've also included a USState.db file you can use if you don't want to generate your own.
I'll update it periodically.
