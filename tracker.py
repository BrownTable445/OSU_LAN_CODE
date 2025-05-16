from flask import Flask, render_template, jsonify
from ossapi import Ossapi
import os
import sys
import argparse
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
            margin: 0;
            padding: 20px;
        }
        
        .leaderboard-container {
            width: 100%;
            max-width: 800px;
            margin: 0 auto;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .title {
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.7);
        }
        
        #leaderboard {
            overflow-y: auto;
            flex-grow: 1;
            padding-right: 10px;
            /* Customize scrollbar */
            scrollbar-width: thin;
            scrollbar-color: rgba(255, 255, 255, 0.3) transparent;
        }
        
        /* Scrollbar styles for Webkit browsers */
        #leaderboard::-webkit-scrollbar {
            width: 8px;
        }
        
        #leaderboard::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 4px;
        }
        
        #leaderboard::-webkit-scrollbar-thumb {
            background-color: rgba(255, 255, 255, 0.3);
            border-radius: 4px;
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
            transition: width 1s ease;
            position: absolute;
            top: 0;
            left: 0;
            z-index: 1;
        }
        
        /* Different colors based on rank range */
        .rank-1-999 {
            background: linear-gradient(90deg, #FF0000, #FF6B6B); /* Red - Top players */
        }
        
        .rank-1000-9999 {
            background: linear-gradient(90deg, #FF9900, #FFD166); /* Orange - Very good players */
        }
        
        .rank-10000-49999 {
            background: linear-gradient(90deg, #FFFF00, #FFFF99); /* Yellow - Good players */
        }
        
        .rank-50000-99999 {
            background: linear-gradient(90deg, #00AA7F, #06D6A0); /* Green - Above average */
        }
        
        .rank-100000-499999 {
            background: linear-gradient(90deg, #073B4C, #118AB2); /* Blue - Average */
        }
        
        .rank-500000-999999 {
            background: linear-gradient(90deg, #7209B7, #9B5DE5); /* Purple - Below average */
        }
        
        .rank-1000000-9999999 {
            background: linear-gradient(90deg, #D90429, #F15BB5); /* Pink - Casual players */
        }
        
        .rank-more {
            background: linear-gradient(90deg, #E76F51, #E9C46A); /* Amber/Coral - Beginners or unranked */
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
        
        .osu-rank {
            font-size: 12px;
            opacity: 0.8;
            margin-left: 10px;
            background-color: rgba(0, 0, 0, 0.5);
            padding: 2px 6px;
            border-radius: 10px;
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
        
        // Auto-scroll variables
        let autoScrollEnabled = true;
        let autoScrollInterval = null;
        let scrollSpeed = 1; // pixels per tick
        
        // Function to get rank class based on player's OSU rank
        function getRankClass(rank) {
            if (!rank || rank === 0) return 'rank-more';
            
            if (rank >= 1 && rank <= 999) {
                return 'rank-1-999';
            } else if (rank >= 1000 && rank <= 9999) {
                return 'rank-1000-9999';
            } else if (rank >= 10000 && rank <= 49999) {
                return 'rank-10000-49999';
            } else if (rank >= 50000 && rank <= 99999) {
                return 'rank-50000-99999';
            } else if (rank >= 100000 && rank <= 499999) {
                return 'rank-100000-499999';
            } else if (rank >= 500000 && rank <= 999999) {
                return 'rank-500000-999999';
            } else if (rank >= 1000000 && rank <= 9999999) {
                return 'rank-1000000-9999999';
            } else {
                return 'rank-more';
            }
        }
        
        // Function to update the leaderboard display
        function updateLeaderboard() {
            const leaderboard = document.getElementById('leaderboard');
            leaderboard.innerHTML = '';
            
            // Find the maximum score for scaling bars
            const maxScore = Math.max(...players.map(player => player.score), 1);
            
            players.forEach((player, index) => {
                // Create bar container
                const barContainer = document.createElement('div');
                barContainer.className = 'bar-container';
                
                // Create the actual bar
                const bar = document.createElement('div');
                bar.className = 'bar';
                
                // Determine rank class based on player's OSU rank
                bar.classList.add(getRankClass(player.osuRank));
                
                // Calculate width based on player's score relative to max score
                const barWidth = (player.score / maxScore) * 100;
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
                
                // Add OSU rank if available
                if (player.osuRank && player.osuRank > 0) {
                    const osuRankBadge = document.createElement('span');
                    osuRankBadge.className = 'osu-rank';
                    osuRankBadge.textContent = `#${player.osuRank.toLocaleString()}`;
                    playerName.appendChild(osuRankBadge);
                }
                
                // Format score with commas for better readability
                const formattedScore = player.score.toLocaleString();
                
                // Create score display
                const score = document.createElement('div');
                score.className = 'score';
                score.innerHTML = `${formattedScore} <span class="subinfo">pts</span>`;
                
                // Assemble the elements
                playerInfo.appendChild(rank);
                playerInfo.appendChild(avatar);
                playerInfo.appendChild(playerName);
                playerInfo.appendChild(score);
                
                barContainer.appendChild(bar);
                barContainer.appendChild(playerInfo);
                
                leaderboard.appendChild(barContainer);
            });
            
            // Start auto-scrolling if enabled
            startAutoScroll();
        }
        
        // Function to manage auto-scrolling
        function startAutoScroll() {
            // Clear any existing interval
            if (autoScrollInterval) {
                clearInterval(autoScrollInterval);
            }
            
            // Only start if enabled
            if (autoScrollEnabled) {
                const leaderboard = document.getElementById('leaderboard');
                // Reset to top
                leaderboard.scrollTop = 0;
                
                // Start a new interval
                autoScrollInterval = setInterval(() => {
                    // If we've scrolled to the bottom, go back to top
                    if (leaderboard.scrollTop >= (leaderboard.scrollHeight - leaderboard.clientHeight)) {
                        leaderboard.scrollTop = 0;
                    } else {
                        // Otherwise continue scrolling down
                        leaderboard.scrollTop += scrollSpeed;
                    }
                }, 30); // Adjust timing for smoother scrolling
            }
        }
        
        // Toggle auto-scroll on space key (convenient for OBS setup)
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space') {
                autoScrollEnabled = !autoScrollEnabled;
                if (autoScrollEnabled) {
                    startAutoScroll();
                } else if (autoScrollInterval) {
                    clearInterval(autoScrollInterval);
                }
            }
        });
        
        // Handle manual scrolling - disable auto-scroll when user scrolls
        document.getElementById('leaderboard').addEventListener('wheel', () => {
            autoScrollEnabled = false;
            if (autoScrollInterval) {
                clearInterval(autoScrollInterval);
            }
        });
        
        // Function to fetch scores from the API
        async function fetchScores() {
            try {
                const response = await fetch('/api/scores');
                const data = await response.json();
                
                // Update match name
                document.getElementById('match-name').textContent = data.match_name + " - Total Score Ranking";
                
                // Update players array with new data including avatars and ranks
                players = Object.entries(data.scores).map(([name, score], index) => ({
                    id: index,
                    name: name,
                    score: score,
                    avatar: data.avatars[name] || "",
                    osuRank: data.ranks[name] || 0
                }));
                
                // Sort players by score in descending order (higher is better for total score)
                players.sort((a, b) => b.score - a.score);
                
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
user_total_scores = defaultdict(int)   # Store total scores (higher is better)
player_avatars = {}                    # Store player avatar URLs
player_ranks = {}                      # Store player OSU ranks

# Initialize API
client_id = int(os.getenv("CLIENT_ID"))
client_secret = os.getenv("CLIENT_SECRET")
api = Ossapi(client_id, client_secret, "http://localhost:3914/")

@app.route('/')
def index():
    return render_template('leaderboard.html')

@app.route('/api/scores')
def get_scores():
    # Return total scores, avatars, ranks, and match name as JSON
    return jsonify({
        'scores': user_total_scores,
        'avatars': player_avatars,
        'ranks': player_ranks,
        'match_name': match_name
    })

def update_total_scores(match_id):
    global match_name, user_total_scores, player_avatars, player_ranks
    
    try:
        match_response = api.match(match_id)
        match_name = match_response.match.name

        user_id_to_name = defaultdict(str)
        
        # Collect user data including avatars and ranks
        for user in match_response.users:
            user_id_to_name[user.id] = user.username
            # Fetch and store the user's avatar URL and rank
            try:
                user_data = api.user(user.id)
                if hasattr(user_data, 'avatar_url') and user_data.avatar_url:
                    player_avatars[user.username] = user_data.avatar_url
                
                # Get the user's current rank from rank history
                if hasattr(user_data, 'rank_history') and user_data.rank_history and user_data.rank_history.data:
                    # Get the most recent rank (last element in the data array)
                    player_ranks[user.username] = user_data.rank_history.data[-1]
                    print(f"Player {user.username} rank: {player_ranks[user.username]}")
            except Exception as e:
                print(f"Could not fetch data for {user.username}: {e}")

        # Reset scores before recalculating
        user_total_scores = defaultdict(int)

        # Process each game (map)
        for event in match_response.events:
            match_game = event.game
            if match_game is not None:
                # Sum up total scores for each player
                for score in match_game.scores:
                    player_name = user_id_to_name[score.user_id]
                    user_total_scores[player_name] += score.score
                
        # Sort scores in descending order (higher is better)
        user_total_scores = dict(sorted(user_total_scores.items(), key=lambda item: item[1], reverse=True))
        print("Total scores (higher is better):", user_total_scores)
    except Exception as e:
        print(f"Error updating scores: {e}")
        traceback.print_exc()

def scheduler_thread(match_id):
    schedule.every(10).seconds.do(update_total_scores, match_id)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='OSU! Multi Total Score Leaderboard')
    parser.add_argument('match_id', type=str, help='Match ID for the OSU multi lobby')
    args = parser.parse_args()
    
    match_id = args.match_id
    
    # Initial update of scores
    update_total_scores(match_id)
    
    # Start the scheduler in a separate thread
    scheduler = Thread(target=scheduler_thread, args=(match_id,))
    scheduler.daemon = True
    scheduler.start()
    
    # Start the Flask app
    print("\n=== OSU! Multi Total Score Leaderboard ===")
    print(f"Connected to: {match_name}")
    print("Total score system: Higher points = better rank")
    print("Players' bars are colored based on their global OSU rank")
    print("\nOpen your browser to http://localhost:5000 to view the leaderboard")
    print("Add this URL as a browser source in OBS: http://localhost:5000")
    print("\nPress Ctrl+C to exit")
    
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    main()