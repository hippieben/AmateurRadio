parse.py a python script to parse FCC Amateur Radio License Data and select only active licenses and output the Callsign and the State into a sqlite db for use with WSJT-Z.  The maintainer of this software mistakenly includes call data that is not the active call, creating instances where a callsign will have several records from previous license grants, and thus state decodes that are incorrect.

Step 1: Download and uncompress the zipfile from the FCC.
ftp://wirelessftp.fcc.gov/pub/uls/complete/l_amat.zip

Step 2: copy parse.py to that directory and run it with python parse.py

Step 3: validate the output of the new sqlitedb with the sqlite.   sqlite USState.db        sqlite> select * from USState;  The resulting data should be formatted call|state

Step 4: replace the existing USState.db file in your share/wsjtx directory



I've also included a USState.db file you can use if you don't want to generate your own.
I'll update it periodically.
