# version 1.1

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

    def get_map_resources(self):
        response = requests.get(f'{self.base_url}/play/mapResource', headers=self.headers)
        response.raise_for_status()
        print(response.json())
        return response.json()

    def get_map_state(self):
        response = requests.get(f'{self.base_url}/play/mapState', headers=self.headers)
        response.raise_for_status()
        print(response.json())
        return response.json()

    def approve_hero_turn(self, action):
        data = {'action': action}
        response = requests.post(f'{self.base_url}/play/approveHeroTurn', headers=self.headers, json=data)
        print(response.json())
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
        print(response.json())
        response.raise_for_status()
        return response.json()

    def get_playthrough_state(self):
        response = requests.get(f'{self.base_url}/story/playthroughState', headers=self.headers)
        response.raise_for_status()
        print(response.json())
        return response.json()

    # A* Pathfinding Algorithm
    def a_star(self, start, goal):
        def heuristic(a, b):
            return abs(a['x'] - b['x']) + abs(a['y'] - b['y'])  # Manhattan distance
        
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
    
    def get_move_direction(self, hero_pos, target_pos):
        path = self.a_star(hero_pos, target_pos)
        if path:
            print("Found path:", path)
            if len(path) >= 1:
                print("PATH: ", path)
                next_step = path[0]
                if next_step['x'] > hero_pos['x']:
                    print("NEXT STEP POS", next_step['x'], next_step['y'], hero_pos['x'], hero_pos['y'])
                    return "MOVE_RIGHT"
                elif next_step['x'] < hero_pos['x']:
                    print("NEXT STEP POS", next_step['x'], hero_pos['x'])
                    return "MOVE_LEFT"
                elif next_step['y'] > hero_pos['y']:
                    print("NEXT STEP POS", next_step['y'], hero_pos['y'])
                    return "MOVE_UP"
                elif next_step['y'] < hero_pos['y']:
                    print("NEXT STEP POS", next_step['y'], hero_pos['y'])
                    return "MOVE_DOWN"
        return "NOTHING"

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
                print("Resetting level...")
                self.reset_level()
                continue  # Start over with the same old new level

            # Check if WON
            if map_state['map']['status'] == 'WON':
                print("Map COMPLETED! Moving to the NEXT LEVEL...")
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
            treasures = map_state['map']['treasures']
            noncollected_treasures = [t for t in treasures if t['collectedByHeroId'] is None]

            if noncollected_treasures:
                target = min(noncollected_treasures, key=lambda t: self.calculate_distance(hero, t['position']))
                action = self.get_move_direction(hero, target['position'])
                print("Action:", action)
                try:
                    self.approve_hero_turn(action)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 409:
                        error_data = e.response.json()
                        if error_data.get('subName') == 'GAME_ON_MAP_IS_ALREADY_OVER':
                            print("Game already over. Resetting level...")
                            self.reset_level()
                        else:
                            raise

            else:
                print("There are NO treasures, staying put.")
                self.approve_hero_turn("NOTHING")
    
    def calculate_distance(self, pos1, pos2):
        return abs(pos1['x'] - pos2['x']) + abs(pos1['y'] - pos2['y'])

if __name__ == "__main__":
    STORY_PLAYTHROUGH_TOKEN = "4352_I2ptMlc4Yj9IZTRza1RvV1lGaX1iSUZ3PXYpLDw0T1ZgT1JQLkI8YUY="
    BASE_URL = "https://ponypanic.io/playGameApi/v1"
    
    client = PonyPanicClient(BASE_URL, STORY_PLAYTHROUGH_TOKEN)
    client.play_game()
