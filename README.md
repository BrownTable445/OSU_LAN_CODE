# OSU LAN REAL-TIME TOURNAMENT GRAPHIC

## About
Imagine you want to host a tournament/lan. You can use an elimination tournament format, where winners of each round move on to the next. The issue with this approach is that it's time consuming to both plan and run. An alternative, easier approach is to host a multi and let everyone play on the same mappool. You can distribute prizes to top total scorers. As of May 2025, the osu tournament client doesn't provide this functionality, so this is why I created this script.

This script listens for matches and displays total scores in real time.

## Setup
Before running this script, you need to create an [OAuth client](https://osu.ppy.sh/docs/index.html#authentication)

Then, copy and paste your client id and secret into a .env file:

CLIENT_ID=...
CLIENT_SECRET=...

I highly recommend using a Python virtual environment when running the script. To do so, run
```
python3 -m venv .venv
```

To activate the virtual environment run
```
source .venv/bin/activate
```

To install dependencies, run 
```
pip install -r requirements.txt
```

## Run
To run the script, run
```
python tracker.py REPLACE_WITH_MATCH_ID
```

# Other

This backend script is made for 5/18/2025 and may not work as intended in the future. Such causes could be related to osu api changes. For example, when writing this script, I noticed that osu api would return Score objects that didn't have a total_score member, even when the documentation specified so. Instead, I had to do some detective work to find Score.score

If having any issues, feel free to make an issue request on Github or contact me at the UCDavis Rhythm Games Club Discord Server. I'm one of the officers.

![image](https://github.com/user-attachments/assets/805d5b32-632d-4284-a920-4c5afcbe6e59)

