# version 1.7.0 DEV 
# THE ESCAPE - (Change to a DEFFENSIVE approach instead of an OFFENSIVE one)

# Simply recalculating a new Path in every move to keep distance from enemies and bullets doesn't help.
# The obstacles create squares. Maybe we should implement some logic to capture those squares and try to find path through the ones where there are no enemies.
# We should use offensive tactics only when it's necessary.

# This version includes features that take a path that keeps distance from threats

import requests
import heapq

class PonyPanicClient:
    def __init__(self, base_url, story_playthrough_token):
        self.base_url = base_url
        self.headers = {
            'story-playthrough-token': story_playthrough_token,
            'Content-Type': 'application/json'
        }
        self.obstacles = {}
        self.data = {}

        # Get the map size from the most recent map_state
        self.map_width = self.get_map_state()['map']['width']
        self.map_height = self.get_map_state()['map']['height']

    def get_map_resources(self):
        response = requests.get(f'{self.base_url}/play/mapResource', headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_map_state(self):
        response = requests.get(f'{self.base_url}/play/mapState', headers=self.headers)
        response.raise_for_status()
        print("CALL MapState")
        return response.json()

    def approve_hero_turn(self, action):
        data = {'action': action}
        response = requests.post(f'{self.base_url}/play/approveHeroTurn', headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def next_level(self):
        data = {}
        response = requests.post(f'{self.base_url}/story/nextLevel', headers=self.headers, json=data)
        if response.status_code != 200:
            print("Response content:", response.content)
        response.raise_for_status()
        return response.json()

    def reset_level(self):
        
        response = requests.post(f'{self.base_url}/story/resetLevel', headers=self.headers, json=self.data)
        response.raise_for_status()
        return response.json()

    def get_playthrough_state(self):
        response = requests.get(f'{self.base_url}/story/playthroughState', headers=self.headers)
        response.raise_for_status()
        return response.json()

    # A* Pathfinding Algorithm
    def a_star(self, start, goal, map_state):
        def heuristic(a, b):
            # Manhattan distance with additional negative cost for proximity to threats
            base_cost = abs(a['x'] - b['x']) + abs(a['y'] - b['y'])
            threat_cost = -self.get_proximity_cost(a, map_state)  # Negative cost to encourage distance from threats
            return base_cost + threat_cost
        
        open_list = []
        heapq.heappush(open_list, (0, tuple(start.values())))
        came_from = {}
        g_score = {tuple(start.values()): 0}
        f_score = {tuple(start.values()): heuristic(start, goal)}
        
        while open_list:
            _, current_tuple = heapq.heappop(open_list)

            if current_tuple == tuple(goal.values()):
                return self.reconstruct_path(came_from, current_tuple)
            
            current = {'x': current_tuple[0], 'y': current_tuple[1]}
            neighbors = self.get_neighbors(current)
            for neighbor in neighbors:
                tentative_g_score = g_score[current_tuple] + 1
                neighbor_tuple = tuple(neighbor.values())
                
                if tentative_g_score < g_score.get(neighbor_tuple, float('inf')):
                    came_from[neighbor_tuple] = current_tuple
                    g_score[neighbor_tuple] = tentative_g_score
                    f_score[neighbor_tuple] = tentative_g_score + heuristic(neighbor, goal)
                    heapq.heappush(open_list, (f_score[neighbor_tuple], neighbor_tuple))
        
        return None  # Return None if no path is found
    
    def get_neighbors(self, position):
        """Get all walkable neighboring positions."""
        directions = [
            {'x': 1, 'y': 0},  # Right
            {'x': -1, 'y': 0}, # Left
            {'x': 0, 'y': 1},  # Up
            {'x': 0, 'y': -1}  # Down
        ]
        neighbors = []
        
        for direction in directions:
            neighbor = {'x': position['x'] + direction['x'], 'y': position['y'] + direction['y']}

            # Skip if coordinates are out of bounds
            if (neighbor['x'] < 0 or neighbor['x'] >= self.map_width or neighbor['y'] < 0 or neighbor['y'] >= self.map_height):
                continue # Skip this neighbor as it's out of map bounds

            # Check if the neighbor is walkable (not an obstacle)
            if self.is_field_empty(neighbor, self.obstacles):
                neighbors.append(neighbor)
        
        return neighbors
    
    def is_field_empty(self, position, obstacles):
        """Check if the field is empty."""
        x_str = str(position['x'])
        if x_str in obstacles and position['y'] in obstacles[x_str]:
            return False
        return True

    def reconstruct_path(self, came_from, current_tuple):
        """Reconstruct the path from start to goal."""
        path = []
        while current_tuple in came_from:
            path.append({'x': current_tuple[0], 'y': current_tuple[1]})
            current_tuple = came_from[current_tuple]
        path.reverse()
        return path
    
    def get_move_direction(self, hero_pos, target_pos, map_state):
        path = self.a_star(hero_pos, target_pos, map_state)
        if path:
            print("Found path:", path)
            if len(path) >= 1:
                next_step = path[0]
                if next_step['x'] > hero_pos['x']:
                    print("NEXT STEP POS", next_step['x'], next_step['y'], hero_pos['x'], hero_pos['y'])
                    return "MOVE_RIGHT"
                elif next_step['x'] < hero_pos['x']:
                    print("NEXT STEP POS", next_step['x'], next_step['y'], hero_pos['x'], hero_pos['y'])
                    return "MOVE_LEFT"
                elif next_step['y'] > hero_pos['y']:
                    print("NEXT STEP POS", next_step['x'], next_step['y'], hero_pos['x'], hero_pos['y'])
                    return "MOVE_UP"
                elif next_step['y'] < hero_pos['y']:
                    print("NEXT STEP POS", next_step['x'], next_step['y'], hero_pos['x'], hero_pos['y'])
                    return "MOVE_DOWN"
        else:
            print("No valid path found from", hero_pos, "to", target_pos)
        return "NOTHING"
    
    def get_enemy_positions(self, map_state):
        """Return a list of enemy positions."""
        return [enemy['position'] for enemy in map_state['map']['enemies']]
    
    def get_enemy_health(self, map_state):
        """Return a list of enemy health."""
        return [enemy['health'] for enemy in map_state['map']['enemies']]

    def get_bullet_positions(self, map_state):
        """Return a list of bullet positions."""
        return [bullet['position'] for bullet in map_state['map']['bullets']]

    def get_kick_direction(self, hero_pos, enemy_pos):
        """Determine the direction to kick the enemy."""
        if enemy_pos['x'] > hero_pos['x']:
            return "KICK_RIGHT"
        elif enemy_pos['x'] < hero_pos['x']:
            return "KICK_LEFT"
        elif enemy_pos['y'] > hero_pos['y']:
            return "KICK_UP"
        elif enemy_pos['y'] < hero_pos['y']:
            return "KICK_DOWN"
        return None

    def is_bullet_threatening(self, hero_pos, bullet_pos):
        """Determine if a bullet is about to hit the hero in the next move."""
        if bullet_pos['x'] == hero_pos['x']:
            if abs(bullet_pos['y'] - hero_pos['y']) == 1:
                return True
        elif bullet_pos['y'] == hero_pos['y']:
            if abs(bullet_pos['x'] - hero_pos['x']) == 1:
                return True
        return False

    def play_game(self):

        # Continue playing until the story is finished
        while True:
            # Get the current map state
            map_state = self.get_map_state()

            # Check if the game is already over
            if map_state['map']['status'] == 'LOST':
                print("""
   ____    _    __  __ _____    _____     _______ ____  
  / ___|  / \  |  \/  | ____|  / _ \ \   / / ____|  _ \ 
 | |  _  / _ \ | |\/| |  _|   | | | \ \ / /|  _| | |_) |
 | |_| |/ ___ \| |  | | |___  | |_| |\ V / | |___|  _ < 
  \____/_/   \_\_|  |_|_____|  \___/  \_/  |_____|_| \_\\
                                                        """)
                print(f"RESETTING LEVEL {self.get_playthrough_state()['currentLevel']}")
                del self.map_resources
                self.reset_level()
                continue  # Start over with the same old new level

            # Check if WON
            if map_state['map']['status'] == 'WON':
                print("""
 /$$    /$$    /$$ /$$             /$$   /$$ /$$$$$$$ 
| $$   | $$   | $$| $$            | $$  | $$| $$__  $$
| $$   | $$   | $$| $$            | $$  | $$| $$  \ $$
| $$   |  $$ / $$/| $$            | $$  | $$| $$$$$$$/
| $$    \  $$ $$/ | $$            | $$  | $$| $$____/ 
| $$     \  $$$/  | $$            | $$  | $$| $$      
| $$$$$$$$\  $/   | $$$$$$$$      |  $$$$$$/| $$      
|________/ \_/    |________/       \______/ |__/      
                                                      
                                                      
                                                      """)
                print(f"LEVEL {self.get_playthrough_state()['currentLevel']} IS COMPLETED! Moving to the NEXT LEVEL...")
                del self.map_resources
                self.next_level()
                continue

            # Fetch map resources only once at the beginning of the map
            if not hasattr(self, 'map_resources'):
                self.map_resources = self.get_map_resources()
                # Set the obstacles from the map resources
                self.obstacles = self.map_resources['compressedObstacles']['coordinateMap']

            # Analyze the map and decide the next move
            hero = map_state['heroes'][0]['position']
            enemies = self.get_enemy_positions(map_state)
            bullets = self.get_bullet_positions(map_state)
            treasures = map_state['map']['treasures']
            noncollected_treasures = [t for t in treasures if t['collectedByHeroId'] is None]

            # Recalculate the optimal move direction to avoid enemies and bullets
            action = None
            if noncollected_treasures:
                # Move towards the nearest treasure
                target = noncollected_treasures[0]['position']
                action = self.get_move_direction(hero, target, map_state)
            else:
                action = "NOTHING"  # Stand still if there are no treasures left
            
            # Execute the action
            if action:
                print(f"Action: {action}")
                self.approve_hero_turn(action)
            else:
                print("No action to perform. Waiting...")
                break
    
    def calculate_distance(self, pos1, pos2):
        return abs(pos1['x'] - pos2['x']) + abs(pos1['y'] - pos2['y'])
    
    def get_proximity_cost(self, pos, map_state):
        """Calculate a cost inversely proportional to the distance from enemies and bullets."""
        enemies = self.get_enemy_positions(map_state)
        bullets = self.get_bullet_positions(map_state)

        min_distance_enemy = min((self.calculate_distance(pos, enemy) for enemy in enemies), default=float('inf'))
        min_distance_bullet = min((self.calculate_distance(pos, bullet) for bullet in bullets), default=float('inf'))

        # Cost is higher when closer to threats
        return 10 / (min_distance_enemy + 1) + 5 / (min_distance_bullet + 1)  # Adjust weights

if __name__ == "__main__":
    STORY_PLAYTHROUGH_TOKEN = "4352_I2ptMlc4Yj9IZTRza1RvV1lGaX1iSUZ3PXYpLDw0T1ZgT1JQLkI8YUY="
    BASE_URL = "https://ponypanic.io/playGameApi/v1"
    
    client = PonyPanicClient(BASE_URL, STORY_PLAYTHROUGH_TOKEN)
    client.play_game()
