We have a Python virtual environment set up to prevent project conflicts
To activate the venv, run

source .venv/bin/activate

Tracker.py updates the leaderboard at most every 10 seconds. There's no need to update it every second.

This backend script is made for 5/18/2025 and may not work as intended in the future. Such causes could be related to osu api changes. For example, when writing this script, I noticed that osu api would return Score objects that didn't have a total_score member, even when the documentation specified so. Instead, I had to do some detective work to find Score.score

If having any issues, feel free to make an issue request on Github or contact me at the UCDavis Rhythm Games Club Discord Server. I'm one of the officers.

To open frontend run

explorer.exe bar_char.html