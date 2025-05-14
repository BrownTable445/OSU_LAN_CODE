from flask import Flask, render_template, jsonify
from ossapi import Ossapi
import os
from dotenv import load_dotenv
import traceback
import schedule
import time
from collections import defaultdict
from threading import Thread
import json

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Create templates directory if it doesn't exist
os.makedirs('templates', exist_ok=True)

# Create the HTML template file
with open('templates/leaderboard.html', 'w') as f:
    f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSU Multi Leaderboard</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: black;
            color: white;
            overflow: hidden;
            margin: 0;
            padding: 20px;
        }
        
        .leaderboard-container {
            width: 100%;
            max-width: 800px;
            margin: 0 auto;
        }
        
        .title {
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.7);
        }
        
        .bar-container {
            height: 50px;
            margin-bottom: 10px;
            position: relative;
            display: flex;
            align-items: center;
            border-radius: 5px;
            overflow: hidden;
            transition: all 0.5s ease;
        }
        
        .bar {
            height: 100%;
            background: linear-gradient(90deg, #66AAFF, #0066FF);
            transition: width 1s ease;
            position: absolute;
            top: 0;
            left: 0;
            z-index: 1;
        }
        
        .player-info {
            position: relative;
            z-index: 2;
            display: flex;
            align-items: center;
            width: 100%;
            padding: 0 15px;
        }
        
        .rank {
            font-size: 20px;
            font-weight: bold;
            width: 40px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.9);
        }
        
        .player-name {
            flex-grow: 1;
            font-size: 18px;
            font-weight: bold;
            margin-left: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.9);
        }
        
        .score {
            font-size: 20px;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.9);
        }
        
        .avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background-color: #333;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            border: 2px solid white;
        }
        
        .avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .match-name {
            text-align: center;
            font-size: 16px;
            margin-bottom: 10px;
            opacity: 0.9;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.7);
        }
        
        .subinfo {
            font-size: 14px;
            opacity: 0.8;
            margin-left: 5px;
        }
    </style>
</head>
<body>
    <div class="leaderboard-container">
        <div class="title">OSU! MULTI LEADERBOARD</div>
        <div id="match-name" class="match-name"></div>
        <div id="leaderboard"></div>
    </div>

    <script>
        // Initialize players array
        let players = [];
        
        // Function to update the leaderboard display
        function updateLeaderboard() {
            const leaderboard = document.getElementById('leaderboard');
            leaderboard.innerHTML = '';
            
            // For ranking points, lower is better so we need to find the lowest score
            const minScore = Math.min(...players.map(player => player.score), 100);
            
            // We want the bar to be inversely proportional to score
            // Calculate max possible bar width for the lowest (best) score
            players.forEach((player, index) => {
                // Create bar container
                const barContainer = document.createElement('div');
                barContainer.className = 'bar-container';
                
                // Create the actual bar - inverse scaling (lower score = longer bar)
                const bar = document.createElement('div');
                bar.className = 'bar';
                
                // For ranking points (where lower is better)
                // We need to invert the scale - lowest score gets 100% width
                // Calculate percentage for each player based on best score
                const barWidth = (minScore / player.score) * 100;
                bar.style.width = `${barWidth}%`;
                
                // Create player info container
                const playerInfo = document.createElement('div');
                playerInfo.className = 'player-info';
                
                // Create rank display
                const rank = document.createElement('div');
                rank.className = 'rank';
                rank.textContent = `#${index + 1}`;
                
                // Create avatar
                const avatar = document.createElement('div');
                avatar.className = 'avatar';
                if (player.avatar) {
                    const img = document.createElement('img');
                    img.src = player.avatar;
                    img.alt = player.name;
                    avatar.appendChild(img);
                } else {
                    avatar.textContent = player.name.charAt(0).toUpperCase();
                }
                
                // Create player name
                const playerName = document.createElement('div');
                playerName.className = 'player-name';
                playerName.textContent = player.name;
                
                // Create score display
                const score = document.createElement('div');
                score.className = 'score';
                score.innerHTML = `${player.score} <span class="subinfo">pts</span>`;
                
                // Assemble the elements
                playerInfo.appendChild(rank);
                playerInfo.appendChild(avatar);
                playerInfo.appendChild(playerName);
                playerInfo.appendChild(score);
                
                barContainer.appendChild(bar);
                barContainer.appendChild(playerInfo);
                
                leaderboard.appendChild(barContainer);
            });
        }
        
        // Function to fetch scores from the API
        async function fetchScores() {
            try {
                const response = await fetch('/api/scores');
                const data = await response.json();
                
                // Update match name
                document.getElementById('match-name').textContent = data.match_name + " - Position-Based Ranking";
                
                // Update players array with new data including avatars
                players = Object.entries(data.scores).map(([name, score], index) => ({
                    id: index,
                    name: name,
                    score: score,
                    avatar: data.avatars[name] || ""
                }));
                
                // Sort players by score in ascending order (lower is better for ranking points)
                players.sort((a, b) => a.score - b.score);
                
                // Update leaderboard
                updateLeaderboard();
            } catch (error) {
                console.error('Error fetching scores:', error);
            }
        }
        
        // Fetch scores initially and then every 5 seconds
        fetchScores();
        setInterval(fetchScores, 5000);
    </script>
</body>
</html>''')

# Global variables to store data
match_name = ""
user_ranking_points = defaultdict(int)  # Store ranking points (lower is better)
player_map_count = defaultdict(int)     # Track how many maps each player has participated in
player_avatars = {}                     # Store player avatar URLs

# Initialize API
client_id = int(os.getenv("CLIENT_ID"))
client_secret = os.getenv("CLIENT_SECRET")
api = Ossapi(client_id, client_secret, "http://localhost:3914/")

@app.route('/')
def index():
    return render_template('leaderboard.html')

@app.route('/api/scores')
def get_scores():
    # Return ranking points, avatars, and match name as JSON
    return jsonify({
        'scores': user_ranking_points,
        'avatars': player_avatars,
        'match_name': match_name
    })

def update_total_scores(room_id):
    global match_name, user_ranking_points, player_map_count, player_avatars
    
    try:
        match_response = api.match(room_id)
        match_name = match_response.match.name

        user_id_to_name = defaultdict(str)
        
        # Collect user data including avatars
        for user in match_response.users:
            user_id_to_name[user.id] = user.username
            # Fetch and store the user's avatar URL
            try:
                user_data = api.user(user.id)
                if hasattr(user_data, 'avatar_url') and user_data.avatar_url:
                    player_avatars[user.username] = user_data.avatar_url
            except Exception as e:
                print(f"Could not fetch avatar for {user.username}: {e}")

        # Reset scores before recalculating
        user_ranking_points = defaultdict(int)
        player_map_count = defaultdict(int)

        # Process each game (map)
        for event in match_response.events:
            match_game = event.game
            if match_game is not None:
                # Get all scores for the current map and sort by score
                map_scores = []
                for score in match_game.scores:
                    player_name = user_id_to_name[score.user_id]
                    map_scores.append((player_name, score.score))
                    # Count maps played for each player
                    player_map_count[player_name] += 1
                
                # Sort scores for this map in descending order
                map_scores.sort(key=lambda x: x[1], reverse=True)
                
                # Assign ranking points (position number) to each player
                for position, (player_name, _) in enumerate(map_scores, 1):
                    user_ranking_points[player_name] += position
        
        # Normalize scores for players who haven't played all maps
        # (Optional) Uncomment if you want to penalize players who missed maps
        """
        max_maps = max(player_map_count.values()) if player_map_count else 1
        for player in user_ranking_points:
            if player_map_count[player] < max_maps:
                # Add penalty points (e.g., last place + 1) for each missed map
                user_ranking_points[player] += (len(user_ranking_points) + 1) * (max_maps - player_map_count[player])
        """
                
        # Sort ranking points in ascending order (lower is better)
        user_ranking_points = dict(sorted(user_ranking_points.items(), key=lambda item: item[1]))
        print("Ranking points (lower is better):", user_ranking_points)
    except Exception as e:
        print(f"Error updating scores: {e}")
        traceback.print_exc()

def scheduler_thread(room_id):
    schedule.every(10).seconds.do(update_total_scores, room_id)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    print("You can find room id by inviting yourself through '/invite YOUR_USERNAME' in your multiplay channel after you create it")
    room_id = input("Please enter room id: ")
    
    # Initial update of scores
    update_total_scores(room_id)
    
    # Start the scheduler in a separate thread
    scheduler = Thread(target=scheduler_thread, args=(room_id,))
    scheduler.daemon = True
    scheduler.start()
    
    # Start the Flask app
    print("\n=== OSU! Multi Position-Based Leaderboard ===")
    print(f"Connected to: {match_name}")
    print("Position-based scoring system: Lower points = better rank")
    print("\nOpen your browser to http://localhost:5000 to view the leaderboard")
    print("Add this URL as a browser source in OBS: http://localhost:5000")
    print("\nPress Ctrl+C to exit")
    
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    main()