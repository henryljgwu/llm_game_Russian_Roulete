import random
import re
import time
import os
from typing import List, Dict, Optional
from llm_client import create_llm_client

# Debug settings
DEBUG = True  # Set to True for debugging output
# ANSI color codes for better visibility
COLORS = {
    "reset": "\033[0m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "bold": "\033[1m",
    "underline": "\033[4m"
}

# Check if we're in Windows CMD (which needs colorama for ANSI codes)
if os.name == 'nt':
    try:
        import colorama
        colorama.init()
    except ImportError:
        # If colorama is not available, disable colors
        for key in COLORS:
            COLORS[key] = ""

def print_header(text, color="yellow", width=80):
    """Print a centered header with a colored background"""
    print(f"\n{COLORS[color]}{COLORS['bold']}{text.center(width)}{COLORS['reset']}\n")
    
def print_debug(text):
    """Print debug information if DEBUG is enabled"""
    if DEBUG:
        print(f"{COLORS['blue']}[DEBUG] {text}{COLORS['reset']}")

def print_event(text):
    """Print game event information"""
    print(f"{COLORS['green']}➤ {text}{COLORS['reset']}")

def print_warning(text):
    """Print warning information"""
    print(f"{COLORS['red']}⚠ {text}{COLORS['reset']}")

def print_divider(char="=", width=80):
    """Print a divider line"""
    print(char * width)

class Role:
    def __init__(self, name: str, style: str):
        self.name = name
        self.style = style

class GameState:
    def __init__(self, chamber_count: int):
        self.chamber_count = chamber_count
        self.bullets = []
        self.current_position = 0
        self.logs = []  # Full logs with all information (for spectators)
        self.player_logs = []  # Limited logs for players (no bullet positions)
        self.contract_active = False
        self.contract_turns_left = 0
        self.reverse_active = False
        self.last_active_player = None
    
    def initialize_gun(self):
        # Randomly place 1 to floor(x/2) bullets
        bullet_count = random.randint(1, self.chamber_count // 3)
        all_positions = list(range(self.chamber_count))
        random.shuffle(all_positions)
        self.bullets = sorted(all_positions[:bullet_count])  # Sort for better readability
        self.current_position = random.randint(0, self.chamber_count - 1)
        
        # Log for spectators with bullet positions
        self.logs.append(f"Game initialized: {bullet_count} bullets randomly loaded at positions {[pos+1 for pos in self.bullets]}, initial trigger position is {self.current_position + 1}")
        
        # Log for players without bullet positions
        self.player_logs.append(f"Game initialized: {bullet_count} bullets randomly loaded, initial trigger position is {self.current_position + 1}")
        
        # Debug output for bullet positions
        if DEBUG:
            print_debug(f"Bullets placed at positions: {[pos+1 for pos in self.bullets]}")
    
    def add_bullet(self):
        # Find empty chambers
        empty_chambers = [i for i in range(self.chamber_count) if i not in self.bullets]
        if empty_chambers:
            new_bullet = random.choice(empty_chambers)
            self.bullets.append(new_bullet)
            self.bullets.sort()  # Keep sorted for easier debugging
            
            # Different logs for spectators vs players
            spec_msg = f"Bullet added to position {new_bullet+1}"
            player_msg = "An extra bullet has been added to the gun"
            
            return spec_msg, player_msg
        
        spec_msg = "All chambers already have bullets"
        player_msg = "All chambers already have bullets"
        return spec_msg, player_msg
    
    def check_chamber(self, position: int, player_name: str) -> bool:
        """Check if the specified chamber has a bullet"""
        if position < 0 or position >= self.chamber_count:
            raise ValueError(f"Position must be between 0 and {self.chamber_count-1}")
        
        has_bullet = position in self.bullets
        
        # Log for spectators
        self.logs.append(f"{player_name} checks position {position+1}: {'has bullet' if has_bullet else 'empty chamber'}")
        
        # For players, this info is directly returned to the checking player
        # but not added to player_logs to avoid leaking information
        
        return has_bullet
    
    def move_position(self):
        """Move the current position by 1"""
        self.current_position = (self.current_position + 1) % self.chamber_count
        
        # Same message for both spectators and players
        msg = f"Trigger moved to position {self.current_position+1}"
        return msg
    
    def activate_contract(self):
        """Activate contract for 3 turns"""
        self.contract_active = True
        self.contract_turns_left = 3
        
        # Same message for both spectators and players
        msg = "Contract activated, lasts for 3 turns"
        return msg
    
    def activate_reverse(self):
        """Activate reverse effect for next turn"""
        self.reverse_active = True
        
        # Same message for both spectators and players
        msg = "Reverse effect activated, will affect next turn"
        return msg

    def fire(self) -> bool:
        """Fire the gun at current position and return True if it was a bullet"""
        was_bullet = self.current_position in self.bullets
        
        # Log for spectators with full information
        self.logs.append(f"Fired at position {self.current_position+1}, result: {'hit' if was_bullet else 'empty'}")
        
        # Log for players with same information (result is publicly visible)
        self.player_logs.append(f"Fired at position {self.current_position+1}, result: {'hit' if was_bullet else 'empty'}")
        
        # Move to next chamber after firing
        self.current_position = (self.current_position + 1) % self.chamber_count
        
        # Update contract turns
        if self.contract_active:
            self.contract_turns_left -= 1
            if self.contract_turns_left <= 0:
                self.contract_active = False
                self.logs.append("Contract effect has ended")
                self.player_logs.append("Contract effect has ended")
        
        return was_bullet
    
    def get_status(self, for_player: bool = True) -> str:
        """Get formatted game logs for display
        
        Args:
            for_player: If True, return limited logs for players
        """
        logs_to_use = self.player_logs if for_player else self.logs
        if not logs_to_use:
            return "Game just started"
        return "\n".join(logs_to_use)
    
    def visualize_gun(self) -> str:
        """Visualize the current state of the gun for spectators"""
        chambers = []
        chambers.append(f"{COLORS['yellow']}Gun state: ({self.current_position + 1}/{self.chamber_count}){COLORS['reset']}")
        for i in range(self.chamber_count):
            if i == self.current_position:
                marker = f"{COLORS['red']}👉 {COLORS['reset']}"  # Pointer for current position
            else:
                marker = "   "
                
            if i in self.bullets:
                chamber = f"{COLORS['red']}● {COLORS['reset']}"  # Bullet
            else:
                chamber = f"{COLORS['cyan']}○ {COLORS['reset']}"  # Empty
                
            chambers.append(f"{marker}{chamber} Chamber {i+1}")
            
        return "\n".join(chambers)
    
    def add_player_communication(self, message: str):
        """Add player communication to both logs"""
        self.logs.append(message)
        self.player_logs.append(message)

class Player:
    def __init__(self, name: str, role_name: str, role_style: str, llm_type: str = None):
        self.name = name
        self.llm_type = llm_type
        self.llm_client = None if llm_type is None else create_llm_client(llm_type)
        self.items = []
        self.alive = True
        self.role = role_name
        self.style = role_style
    
    def add_item(self, item: str):
        self.items.append(item)
    
    def remove_item(self, item: str) -> bool:
        """Remove an item from inventory, return success"""
        if item in self.items:
            self.items.remove(item)
            return True
        return False
    
    def get_items_string(self) -> str:
        """Get comma-separated string of items"""
        if not self.items:
            return "None"
        return ", ".join(self.items)
    
    def set_role(self, role: str, style: str):
        self.role = role
        self.style = style

class GameController:
    def __init__(self, chamber_count: int = 6):
        self.chamber_count = chamber_count
        self.game_state = GameState(chamber_count)
        self.players = []
        self.current_player_idx = 0
        
    def add_player(self, name: str, role_name: str, role_style: str, llm_type: str = None):
        """Add a player with specified role, style, and LLM type"""
        player = Player(name, role_name, role_style, llm_type)
        self.players.append(player)
        return player
    
    def setup_game(self, player_configs: List[Dict]):
        """Initialize the game with specified player configurations"""
        print_header("Russian Roulette Game Started", "green")
        print(f"Number of chambers: {self.chamber_count}")
        print_divider("-")
        
        # Add players with specified configurations
        for config in player_configs:
            player_name = config["name"]
            role_name = config["role_name"]
            role_style = config["role_style"]
            llm_type = config["llm_type"]
            
            self.add_player(player_name, role_name, role_style, llm_type)
        
        # Initialize gun with random bullets
        self.game_state.initialize_gun()
        
        # Distribute items
        available_items = ["Bullet", "Check", "Reverse", "Contract", "Push"] * (len(self.players) + 2)
        random.shuffle(available_items)
        
        item_count = (self.chamber_count + 2) // 3  # ceil(x/3)
        
        # Give items to players
        for i, player in enumerate(self.players):
            player_items = available_items[i*item_count:(i+1)*item_count]
            for item in player_items:
                player.add_item(item)
            
            print(f"{player.name} (Role: {player.role}, Style: {player.style})")
            print(f"Items: {COLORS['cyan']}{player.get_items_string()}{COLORS['reset']}")
        
        # Randomly determine who goes first
        self.current_player_idx = random.randint(0, len(self.players) - 1)
        print_event(f"{self.players[self.current_player_idx].name} goes first")
        
    def get_game_rule(self) -> str:
        """Get the formatted game rule with actual chamber count"""
        rule = f"""Game Rules:
There is a revolver with {self.chamber_count} chambers, and 1~{self.chamber_count//2} bullets randomly loaded.
The game will randomly select a player to start. Each player can choose to shoot themselves or the other player.
Before shooting, players can optionally perform two actions: choose whether to use an item (the opponent can only see if an item was used, but not which one, except for Contract) -> choose whether to speak to the other player, dialog can be used for negotiation, if the opponent agrees then the game ends in a draw -> acknowledge the current trigger position, and choose to shoot yourself or the other player.
Item rules: Each player will randomly receive ceil(x/3) items at the start. The items and their functions are:
1. Bullet: Adds an extra bullet to a random empty chamber
2. Check: Choose a chamber position to inspect, and be told if it contains a bullet or is empty
3. Reverse: The opponent's next action will be reversed
4. Contract: For the next 3 turns, if one player is shot, the other is also shot, resulting in a draw
5. Push: Advance the trigger position by one chamber"""
        return rule
    
    def get_reply_format(self) -> str:
        """Get the required reply format"""
        return """【item】
If using an item, write: Item name Parameter(if any)
If not using an item, write: None
【item end】

【communication】
If you want to talk, write: Talk Your message
If you want to negotiate, write: Negotiate Your negotiation message
If no communication, write: Silent
【communication end】

【fire】
Choose: Self or Opponent
【fire end】"""
    
    def parse_response(self, response: str) -> Dict:
        """Parse the player's response using simplified format markers"""
        result = {}
        
        # Extract item usage
        item_match = re.search(r'【item】\s*(.*?)\s*【item end】', response, re.DOTALL)
        if item_match:
            item_text = item_match.group(1).strip()
            if "None" in item_text:
                result["item"] = None
                result["item_param"] = None
            else:
                # Try to extract item name and parameter
                item_parts = item_text.split(maxsplit=1)
                result["item"] = item_parts[0] if item_parts else None
                # Get parameter if it exists
                result["item_param"] = item_parts[1] if len(item_parts) > 1 else None
        
        # Extract communication
        comm_match = re.search(r'【communication】\s*(.*?)\s*【communication end】', response, re.DOTALL)
        if comm_match:
            comm_text = comm_match.group(1).strip()
            if "Silent" in comm_text:
                result["communication"] = "Silent"
                result["message"] = None
            elif comm_text.startswith("Negotiate"):
                result["communication"] = "Negotiate"
                # Extract the message part
                parts = comm_text.split(maxsplit=1)
                result["message"] = parts[1] if len(parts) > 1 else ""
            else:
                result["communication"] = "Talk"
                parts = comm_text.split(maxsplit=1)
                result["message"] = parts[1] if len(parts) > 1 else ""
        
        # Extract firing decision
        fire_match = re.search(r'【fire】\s*(.*?)\s*【fire end】', response, re.DOTALL)
        if fire_match:
            fire_text = fire_match.group(1).strip()
            result["target"] = "Self" if "Self" in fire_text else "Opponent"
        
        return result

    def handle_item_usage(self, player: Player, item: str, param: Optional[str] = None) -> str:
        """Handle a player's item usage"""
        if item is None or item not in player.items:
            return "Invalid item or no item used"
        
        spec_message = ""
        player_message = ""
        
        if item == "Bullet":
            player.remove_item("Bullet")
            spec_message, player_message = self.game_state.add_bullet()
        
        elif item == "Check":
            try:
                position = int(param) - 1  # Convert to 0-based index
                if position < 0 or position >= self.game_state.chamber_count:
                    spec_message = player_message = f"Invalid position, should be 1-{self.game_state.chamber_count}"
                else:
                    has_bullet = self.game_state.check_chamber(position, player.name)
                    player.remove_item("Check")
                    spec_message = f"{player.name} checks position {position+1}"
                    player_message = f"Position {position+1} {'has a bullet' if has_bullet else 'is empty'}"
            except (ValueError, TypeError):
                spec_message = player_message = "Check item requires a valid position parameter"
        
        elif item == "Reverse":
            player.remove_item("Reverse")
            spec_message = player_message = self.game_state.activate_reverse()
            # Record which player activated the reverse effect
            self.game_state.last_active_player = player
        
        elif item == "Contract":
            player.remove_item("Contract")
            spec_message = player_message = self.game_state.activate_contract()
        
        elif item == "Push":
            player.remove_item("Push")
            spec_message = player_message = self.game_state.move_position()
        
        # Add to spectator logs
        self.game_state.logs.append(f"{player.name} used {item}: {spec_message}")
        
        # Add to player logs (with potentially less information)
        self.game_state.player_logs.append(f"{player.name} used {item}")
        
        return player_message
    
    def get_opponent(self, player):
        """Get the player's opponent"""
        player_idx = self.players.index(player)
        return self.players[(player_idx + 1) % len(self.players)]
    
    def process_player_turn(self, player_idx) -> bool:
        """Process a player's turn, return True if game should continue"""
        player = self.players[player_idx]
        opponent = self.get_opponent(player)
        
        print_header(f"{player.name}'s Turn", "magenta")
        print(f"Role: {player.role} (Style: {player.style})")
        print(f"Current trigger position: {self.game_state.current_position + 1}/{self.chamber_count}")
        print(f"Contract status: {'Active' if self.game_state.contract_active else 'Inactive'}")
        
        # For spectators only: visualization of gun state
        if DEBUG:
            print_debug("Current gun state (spectators only)")
            print(self.game_state.visualize_gun())
            print_debug("Player items: " + player.get_items_string())
        
        # Skip if player is not AI
        if player.llm_client is None:
            return True
        
        # Create a Role object for this player
        role = Role(player.role, player.style)
        
        # Prepare the prompt for AI with improved format
        prompt = f"""You are: {role.name}
You should play the game in the style of {role.style}.
Your opponent is {opponent.name}

Game rules:
{self.get_game_rule()}

Previous game logs:
{self.game_state.get_status(for_player=True)}

Current trigger position: {self.game_state.current_position + 1}
Total chambers: {self.chamber_count}
Contract status: {'Active' if self.game_state.contract_active else 'Inactive'}

Your current items:
{player.get_items_string()}

You must reply in the following format (use 【】 instead of <>, to avoid XML format confusion):

{self.get_reply_format()}

Please think deeply and reason based on your role, the game rules, and your available items, doing everything possible to win. If winning isn't possible, aim for a draw.

Very important: Communication is a key element in this game! Please express your thoughts in the 【communication】 section.
You can use these communication strategies:
1. Deception strategy: Deliberately mislead your opponent about chamber positions or your intentions
2. Pressure strategy: Try to make your opponent believe you have more information by showing confidence
3. Surrender strategy: Persuade your opponent to give up or propose a compromise that benefits you
4. Psychological warfare: Use words to influence your opponent's judgment or emotions

Your communication will greatly influence the game outcome, don't stay silent, actively engage with your opponent!
Combining item use with effective communication can create significant tactical advantages.

Make sure to reply in the exact format above, using 【】 markers for sections, not any other tags."""

        messages = [{"role": "user", "content": prompt}]
        
        if DEBUG:
            print_debug("Prompt sent to AI:")
            print_divider("-", 40)
            print(prompt)
            print_divider("-", 40)
        
        # Send message to LLM
        print_event(f"{player.name} thinking...")
        start_time = time.time()
        ai_response = player.llm_client.send_message(messages)
        end_time = time.time()
        print(f"Thinking time: {COLORS['yellow']}{end_time - start_time:.2f} seconds{COLORS['reset']}")
        
        # Print AI response with clear formatting
        print_header(f"{player.name}'s Response", "cyan")
        print(ai_response)
        print_divider("-")
        
        # Parse response
        parsed = self.parse_response(ai_response)
        if DEBUG:
            print_debug(f"Parsed result: {parsed}")
        
        # Process the player's actions
        # 1. Item usage
        if parsed.get("item"):
            result = self.handle_item_usage(player, parsed["item"], parsed.get("item_param"))
            print_event(f"{player.name} uses item {parsed['item']}: {result}")
        else:
            print_event(f"{player.name} chooses not to use an item")
        
        # 2. Communication
        if parsed.get("communication") == "Negotiate":
            message = parsed.get('message', '')
            print_event(f"{player.name} proposes negotiation: {message}")
            # Add to both logs
            self.game_state.add_player_communication(f"{player.name} proposes negotiation: {message}")
            
            # Create a prompt for the opponent to consider the negotiation
            neg_prompt = self.get_neg_prompt(player, opponent, message)

            neg_messages = [{"role": "user", "content": neg_prompt}]
            
            if DEBUG:
                print_debug("Negotiation consideration prompt:")
                print_divider("-", 40)
                print(neg_prompt)
                print_divider("-", 40)
            
            print_event(f"Waiting for {opponent.name} to consider the negotiation request...")
            opponent_response = opponent.llm_client.send_message(neg_messages)
            print_header(f"{opponent.name}'s Response", "cyan")
            print(opponent_response)
            print_divider("-")
            self.game_state.add_player_communication(f"{opponent.name} responds: {opponent_response}")
            
            if "agree" in opponent_response.lower():
                print_header("Negotiation successful, game ends in a draw!", "green")
                return False
            else:
                print_warning(f"{opponent.name} rejected the negotiation request, game continues")
        
        elif parsed.get("communication") == "Talk":
            message = parsed.get('message', '')
            print_event(f"{player.name} says: {message}")
            # Add to both logs
            self.game_state.add_player_communication(f"{player.name} says: {message}")
        
        else:
            print_event(f"{player.name} chooses to remain silent")
            # Add to both logs
            self.game_state.add_player_communication(f"{player.name} chooses to remain silent")
        
        # 3. Fire
        target = parsed.get("target", "Opponent")  # Default to opponent if missing
        
        # Apply reverse if active
        if self.game_state.reverse_active and self.game_state.last_active_player != player:
            target = "Self" if target == "Opponent" else "Opponent"
            print_warning(f"Reverse effect activated! {player.name}'s target was reversed to {target}")
            self.game_state.reset_reverse = True
        
        # Reset reverse after applying it
        if hasattr(self.game_state, 'reset_reverse') and self.game_state.reset_reverse:
            self.game_state.reverse_active = False
            self.game_state.reset_reverse = False
        
        print_header(f"{player.name} chooses to shoot {target}!", "red")
        
        # Execute fire
        was_hit = self.game_state.fire()
        
        if was_hit:
            print_header(f"Result: Hit! {'💥' * 3}", "red")
            if target == "Self":
                player.alive = False
                print_header(f"{player.name} shot themselves, game over!", "red")
                return False
            else:
                opponent.alive = False
                print_header(f"{opponent.name} was shot, game over!", "red")
                return False
        else:
            print_event(f"Result: Miss (empty chamber)")
        
        # Show updated gun state after turn if debugging
        if DEBUG:
            print_debug("Gun state after turn:")
            print(self.game_state.visualize_gun())
        
        return True
    
    def check_contract_effect(self) -> bool:
        """Check and apply contract effect if needed, return True if game should continue"""
        if self.game_state.contract_active:
            dead_players = [p for p in self.players if not p.alive]
            if dead_players:
                print("Contract effect triggered! All players die together!")
                for player in self.players:
                    player.alive = False
                return False
        return True
    
    def run_game(self):
        """Run the game loop"""
        game_active = True
        max_turns = 30  # Safety measure to prevent infinite loops
        turn_count = 0
        
        while game_active and turn_count < max_turns:
            player_idx = self.current_player_idx
            
            # Show turn counter
            print_divider("=")
            print_header(f"Turn {turn_count + 1}", "white")
            
            game_active = self.process_player_turn(player_idx)
            
            # If a player was hit, check contract but game will end
            if not game_active:
                if self.game_state.contract_active:
                    print_header("Checking contract effect", "yellow")
                    self.check_contract_effect()
                break
            
            # Switch to next player
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            turn_count += 1
        
        print_header("Game Over", "green", width=80)
        alive_players = [p for p in self.players if p.alive]
        
        if not alive_players:
            print_header("Draw! All players are dead", "yellow")
        elif len(alive_players) == len(self.players):
            print_header("Game reached maximum turns, ending in a draw", "yellow")
        else:
            for player in alive_players:
                print_header(f"{player.name} wins!", "green")
        
        # Print stats
        print_divider("*")
        print_header("Game Statistics", "blue")
        print(f"Total turns: {turn_count}")
        print(f"Total chambers: {self.chamber_count}")
        print(f"Total bullets: {len(self.game_state.bullets)}")
        
        # Print full logs with bullet information for spectators
        print_header("Detailed Game Log (with chamber information)", "magenta")
        print(self.game_state.get_status(for_player=False))
        
        # Final visualization of the gun
        print_header("Final Gun State", "yellow")
        print(self.game_state.visualize_gun())

    def get_neg_prompt(self, player, opponent, message):
        """Generate a negotiation prompt for the opponent"""
        return f"""You are: {opponent.role}
You should play in the style of {opponent.style}.
In the current game, opponent {player.name} has proposed a draw negotiation.

Negotiation content: "{message}"

Current game status:
{self.game_state.get_status(for_player=True)}

Current trigger position: {self.game_state.current_position + 1}/{self.chamber_count}
Contract status: {'Active' if self.game_state.contract_active else 'Inactive'}

Your items: {opponent.get_items_string()}

Consider the current game state, your character, and your chances of winning. Do you agree to this negotiation?
Please respond with only "Agree" or "Decline" and a brief reason."""

def main():
    # Game configuration
    game_config = {
        "chamber_count": 8,  # Number of chambers in the gun
        "player_configs": [
            {
                "name": "Bill",
                "role_name": "Gambler",
                "role_style": "Aggressive and bold, likes taking risks, applies extreme pressure and is skilled at lying to disrupt opponent's judgment",
                "llm_type": "anthropic"
            },
            {
                "name": "Lee",
                "role_name": "Detective",
                "role_style": "Calm and analytical, good at reasoning, uses logical analysis to see through opponent's lies and strategies",
                "llm_type": "openai"
            }
        ]
    }
    
    # Clear screen for better visualization
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Print game banner
    print_divider("=")
    print(f"{COLORS['bold']}{COLORS['red']}RUSSIAN ROULETTE DUEL{COLORS['reset']}")
    print_divider("=")
    
    # Initialize and run the game
    game = GameController(chamber_count=game_config["chamber_count"])
    game.setup_game(game_config["player_configs"])
    game.run_game()

if __name__ == "__main__":
    main()
