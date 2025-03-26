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
        bullet_count = random.randint(1, self.chamber_count // 2)
        all_positions = list(range(self.chamber_count))
        random.shuffle(all_positions)
        self.bullets = sorted(all_positions[:bullet_count])  # Sort for better readability
        self.current_position = random.randint(0, self.chamber_count - 1)
        
        # Log for spectators with bullet positions
        self.logs.append(f"游戏初始化: {bullet_count}个子弹被随机装入位置 {[pos+1 for pos in self.bullets]}，初始扳机位置为{self.current_position + 1}")
        
        # Log for players without bullet positions
        self.player_logs.append(f"游戏初始化: {bullet_count}个子弹被随机装入，初始扳机位置为{self.current_position + 1}")
        
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
            spec_msg = f"子弹被添加到位置 {new_bullet+1}"
            player_msg = "一个额外的子弹被添加到枪中"
            
            return spec_msg, player_msg
        
        spec_msg = "所有弹巢都已有子弹"
        player_msg = "所有弹巢都已有子弹"
        return spec_msg, player_msg
    
    def check_chamber(self, position: int, player_name: str) -> bool:
        """Check if the specified chamber has a bullet"""
        if position < 0 or position >= self.chamber_count:
            raise ValueError(f"Position must be between 0 and {self.chamber_count-1}")
        
        has_bullet = position in self.bullets
        
        # Log for spectators
        self.logs.append(f"{player_name} 查看位置 {position+1}: {'有子弹' if has_bullet else '空弹巢'}")
        
        # For players, this info is directly returned to the checking player
        # but not added to player_logs to avoid leaking information
        
        return has_bullet
    
    def move_position(self):
        """Move the current position by 1"""
        self.current_position = (self.current_position + 1) % self.chamber_count
        
        # Same message for both spectators and players
        msg = f"扳机移动到位置 {self.current_position+1}"
        return msg
    
    def activate_contract(self):
        """Activate contract for 3 turns"""
        self.contract_active = True
        self.contract_turns_left = 3
        
        # Same message for both spectators and players
        msg = "契约已激活，持续3回合"
        return msg
    
    def activate_reverse(self):
        """Activate reverse effect for next turn"""
        self.reverse_active = True
        
        # Same message for both spectators and players
        msg = "反转效果已激活，将影响下一回合"
        return msg

    def fire(self) -> bool:
        """Fire the gun at current position and return True if it was a bullet"""
        was_bullet = self.current_position in self.bullets
        
        # Log for spectators with full information
        self.logs.append(f"在位置 {self.current_position+1} 开火，结果: {'命中' if was_bullet else '空弹'}")
        
        # Log for players with same information (result is publicly visible)
        self.player_logs.append(f"在位置 {self.current_position+1} 开火，结果: {'命中' if was_bullet else '空弹'}")
        
        # Move to next chamber after firing
        self.current_position = (self.current_position + 1) % self.chamber_count
        
        # Update contract turns
        if self.contract_active:
            self.contract_turns_left -= 1
            if self.contract_turns_left <= 0:
                self.contract_active = False
                self.logs.append("契约效果已结束")
                self.player_logs.append("契约效果已结束")
        
        return was_bullet
    
    def get_status(self, for_player: bool = True) -> str:
        """Get formatted game logs for display
        
        Args:
            for_player: If True, return limited logs for players
        """
        logs_to_use = self.player_logs if for_player else self.logs
        if not logs_to_use:
            return "游戏刚刚开始"
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
            return "无"
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
        print_header("俄罗斯轮盘游戏开始", "green")
        print(f"弹巢数量: {self.chamber_count}")
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
        available_items = ["子弹", "查看", "反转", "契约", "推动"] * (len(self.players) + 2)
        random.shuffle(available_items)
        
        item_count = (self.chamber_count + 2) // 3  # ceil(x/3)
        
        # Give items to players
        for i, player in enumerate(self.players):
            player_items = available_items[i*item_count:(i+1)*item_count]
            for item in player_items:
                player.add_item(item)
            
            print(f"{player.name} (角色: {player.role}, 风格: {player.style})")
            print(f"道具: {COLORS['cyan']}{player.get_items_string()}{COLORS['reset']}")
        
        # Randomly determine who goes first
        self.current_player_idx = random.randint(0, len(self.players) - 1)
        print_event(f"{self.players[self.current_player_idx].name} 先手")
        
    def get_game_rule(self) -> str:
        """Get the formatted game rule with actual chamber count"""
        rule = f"""游戏规则：
现在有一个左轮手枪，里面共有{self.chamber_count}个弹巢，并且里面随机装了1~{self.chamber_count//2}个子弹。
游戏将随机选择一个玩家开始，每个玩家可以选择对自己开枪或者对另一个玩家开枪
在开枪前，玩家可以选择性进行两次行动：选择是否使用道具（对面的玩家只能看到是否使用了道具，但并不能知道使用了什么，除了契约）->选择是否对另一个玩家说话，对话可以选择协商，如果对面也同意则进入平局->告知目前扳机所对的弹巢的位置，并选择对自己还是对另一个玩家开枪
道具部分的规则：每个玩家会在开局随机分发ceil(x/3)个道具。道具的列表和功能分别是：
1. 子弹：额外向枪内随机位置装填一个子弹
2. 查看：选择一个位置的弹巢进行探测，并被告知是子弹还是空弹巢
3. 反转：下一次对手的行动将被反转
4. 契约：3次行动内如果一个人被击毙则另一个人也被击毙，平局
5. 推动：使扳机所对位置前进一格"""
        return rule
    
    def get_reply_format(self) -> str:
        """Get the required reply format"""
        return """【道具】
若使用道具，请写：道具名称 参数(如有)
若不使用道具，请写：不使用
【道具结束】

【交流】
若要交谈，请写：谈话 你想说的话
若要协商，请写：协商 你的协商内容
若不交流，请写：沉默
【交流结束】

【开火】
请选择：自己 或 对面
【开火结束】"""
    
    def parse_response(self, response: str) -> Dict:
        """Parse the player's response using simplified format markers"""
        result = {}
        
        # Extract item usage
        item_match = re.search(r'【道具】\s*(.*?)\s*【道具结束】', response, re.DOTALL)
        if item_match:
            item_text = item_match.group(1).strip()
            if "不使用" in item_text:
                result["item"] = None
                result["item_param"] = None
            else:
                # Try to extract item name and parameter
                item_parts = item_text.split(maxsplit=1)
                result["item"] = item_parts[0] if item_parts else None
                # Get parameter if it exists
                result["item_param"] = item_parts[1] if len(item_parts) > 1 else None
        
        # Extract communication
        comm_match = re.search(r'【交流】\s*(.*?)\s*【交流结束】', response, re.DOTALL)
        if comm_match:
            comm_text = comm_match.group(1).strip()
            if "沉默" in comm_text:
                result["communication"] = "沉默"
                result["message"] = None
            elif comm_text.startswith("协商"):
                result["communication"] = "协商"
                # Extract the message part
                parts = comm_text.split(maxsplit=1)
                result["message"] = parts[1] if len(parts) > 1 else ""
            else:
                result["communication"] = "谈话"
                parts = comm_text.split(maxsplit=1)
                result["message"] = parts[1] if len(parts) > 1 else ""
        
        # Extract firing decision
        fire_match = re.search(r'【开火】\s*(.*?)\s*【开火结束】', response, re.DOTALL)
        if fire_match:
            fire_text = fire_match.group(1).strip()
            result["target"] = "自己" if "自己" in fire_text else "对面"
        
        return result

    def handle_item_usage(self, player: Player, item: str, param: Optional[str] = None) -> str:
        """Handle a player's item usage"""
        if item is None or item not in player.items:
            return "无效道具或未使用道具"
        
        spec_message = ""
        player_message = ""
        
        if item == "子弹":
            player.remove_item("子弹")
            spec_message, player_message = self.game_state.add_bullet()
        
        elif item == "查看":
            try:
                position = int(param) - 1  # Convert to 0-based index
                if position < 0 or position >= self.game_state.chamber_count:
                    spec_message = player_message = f"无效位置，应为1-{self.game_state.chamber_count}"
                else:
                    has_bullet = self.game_state.check_chamber(position, player.name)
                    player.remove_item("查看")
                    spec_message = f"{player.name} 查看位置 {position+1}"
                    player_message = f"位置 {position+1} 是{'有' if has_bullet else '空'}弹"
            except (ValueError, TypeError):
                spec_message = player_message = "查看道具需要一个有效的位置参数"
        
        elif item == "反转":
            player.remove_item("反转")
            spec_message = player_message = self.game_state.activate_reverse()
            # Record which player activated the reverse effect
            self.game_state.last_active_player = player
        
        elif item == "契约":
            player.remove_item("契约")
            spec_message = player_message = self.game_state.activate_contract()
        
        elif item == "推动":
            player.remove_item("推动")
            spec_message = player_message = self.game_state.move_position()
        
        # Add to spectator logs
        self.game_state.logs.append(f"{player.name} 使用了 {item}：{spec_message}")
        
        # Add to player logs (with potentially less information)
        self.game_state.player_logs.append(f"{player.name} 使用了 {item}")
        
        return player_message
    
    def get_opponent(self, player):
        """Get the player's opponent"""
        player_idx = self.players.index(player)
        return self.players[(player_idx + 1) % len(self.players)]
    
    def process_player_turn(self, player_idx) -> bool:
        """Process a player's turn, return True if game should continue"""
        player = self.players[player_idx]
        opponent = self.get_opponent(player)
        
        print_header(f"{player.name} 回合", "magenta")
        print(f"角色: {player.role} (风格: {player.style})")
        print(f"当前扳机位置: {self.game_state.current_position + 1}/{self.chamber_count}")
        print(f"契约状态: {'激活' if self.game_state.contract_active else '未激活'}")
        
        # For spectators only: visualization of gun state
        if DEBUG:
            print_debug("当前枪械状态 (仅观众可见)")
            print(self.game_state.visualize_gun())
            print_debug("玩家道具: " + player.get_items_string())
        
        # Skip if player is not AI
        if player.llm_client is None:
            return True
        
        # Create a Role object for this player
        role = Role(player.role, player.style)
        
        # Prepare the prompt for AI with improved format
        prompt = f"""你是:{role.name}
你要以{role.style}的风格来进行游戏。
你的对手是{opponent.name}

游戏规则是：
{self.get_game_rule()}

之前的游戏log是:
{self.game_state.get_status(for_player=True)}

当前扳机位置: {self.game_state.current_position + 1}
总弹巢数: {self.chamber_count}
契约状态: {'激活' if self.game_state.contract_active else '未激活'}

你目前已经有的道具有：
{player.get_items_string()}

你必须按照以下格式回复（用【】而不是<>，避免XML格式混淆）：

{self.get_reply_format()}

请你基于你的角色设定，游戏规则，你目前有的道具，进行深刻的思考和推理，尽一切办法，做到使自己赢。如果实在不行也要尽可能平局。

非常重要：交流是这个游戏中的关键元素！请务必在【交流】部分表达你的想法。
你可以采取以下沟通策略：
1. 欺骗战略：故意误导对手关于弹巢位置或你的意图
2. 压制战略：试图通过展示信心让对手认为你掌握了更多信息
3. 劝降战略：劝说对手放弃或提出对你有利的妥协方案
4. 心理战：通过言语影响对手的判断或情绪

你的沟通内容会极大地影响游戏结局，请不要沉默，积极与对手交流！
道具的使用和你的交流相结合，能创造出极大的战术优势。

请确保按照上面的格式回复，使用【】标记区域，而不是其他任何标签。"""

        messages = [{"role": "user", "content": prompt}]
        
        if DEBUG:
            print_debug("发送给AI的Prompt如下:")
            print_divider("-", 40)
            print(prompt)
            print_divider("-", 40)
        
        # Send message to LLM
        print_event(f"{player.name} 思考中...")
        start_time = time.time()
        ai_response = player.llm_client.send_message(messages)
        end_time = time.time()
        print(f"思考用时: {COLORS['yellow']}{end_time - start_time:.2f}秒{COLORS['reset']}")
        
        # Print AI response with clear formatting
        print_header(f"{player.name} 回应", "cyan")
        print(ai_response)
        print_divider("-")
        
        # Parse response
        parsed = self.parse_response(ai_response)
        if DEBUG:
            print_debug(f"解析结果: {parsed}")
        
        # Process the player's actions
        # 1. Item usage
        if parsed.get("item"):
            result = self.handle_item_usage(player, parsed["item"], parsed.get("item_param"))
            print_event(f"{player.name} 使用道具 {parsed['item']}: {result}")
        else:
            print_event(f"{player.name} 选择不使用道具")
        
        # 2. Communication
        if parsed.get("communication") == "协商":
            message = parsed.get('message', '')
            print_event(f"{player.name} 提出协商: {message}")
            # Add to both logs
            self.game_state.add_player_communication(f"{player.name} 提出协商: {message}")
            
            # Create a prompt for the opponent to consider the negotiation
            neg_prompt = self.get_neg_prompt(player, opponent, message)

            neg_messages = [{"role": "user", "content": neg_prompt}]
            
            if DEBUG:
                print_debug("协商考虑中的Prompt内容:")
                print_divider("-", 40)
                print(neg_prompt)
                print_divider("-", 40)
            
            print_event(f"等待 {opponent.name} 考虑协商请求...")
            opponent_response = opponent.llm_client.send_message(neg_messages)
            print_header(f"{opponent.name} 回应", "cyan")
            print(opponent_response)
            print_divider("-")
            self.game_state.add_player_communication(f"{opponent.name} 回应: {opponent_response}")
            
            if "同意" in opponent_response.lower():
                print_header("协商成功，游戏结束为平局!", "green")
                return False
            else:
                print_warning(f"{opponent.name} 拒绝了协商请求，游戏继续")
        
        elif parsed.get("communication") == "谈话":
            message = parsed.get('message', '')
            print_event(f"{player.name} 说: {message}")
            # Add to both logs
            self.game_state.add_player_communication(f"{player.name} 说: {message}")
        
        else:
            print_event(f"{player.name} 选择保持沉默")
            # Add to both logs
            self.game_state.add_player_communication(f"{player.name} 选择保持沉默")
        
        # 3. Fire
        target = parsed.get("target", "对面")  # Default to opponent if missing
        
        # Apply reverse if active
        if self.game_state.reverse_active and self.game_state.last_active_player != player:
            target = "自己" if target == "对面" else "对面"
            print_warning(f"反转效果激活! {player.name} 的目标被反转为 {target}")
            self.game_state.reset_reverse = True
        
        # Reset reverse after applying it
        if hasattr(self.game_state, 'reset_reverse') and self.game_state.reset_reverse:
            self.game_state.reverse_active = False
            self.game_state.reset_reverse = False
        
        print_header(f"{player.name} 选择对{target}开火!", "red")
        
        # Execute fire
        was_hit = self.game_state.fire()
        
        if was_hit:
            print_header(f"结果: 命中! {'💥' * 3}", "red")
            if target == "自己":
                player.alive = False
                print_header(f"{player.name} 击中自己，游戏结束!", "red")
                return False
            else:
                opponent.alive = False
                print_header(f"{opponent.name} 被击中，游戏结束!", "red")
                return False
        else:
            print_event(f"结果: 未命中 (空弹)")
        
        # Show updated gun state after turn if debugging
        if DEBUG:
            print_debug("回合结束后枪械状态:")
            print(self.game_state.visualize_gun())
        
        return True
    
    def check_contract_effect(self) -> bool:
        """Check and apply contract effect if needed, return True if game should continue"""
        if self.game_state.contract_active:
            dead_players = [p for p in self.players if not p.alive]
            if dead_players:
                print("契约效果触发! 所有玩家同归于尽!")
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
            print_header(f"第 {turn_count + 1} 回合", "white")
            
            game_active = self.process_player_turn(player_idx)
            
            # If a player was hit, check contract but game will end
            if not game_active:
                if self.game_state.contract_active:
                    print_header("检查契约效果", "yellow")
                    self.check_contract_effect()
                break
            
            # Switch to next player
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            turn_count += 1
        
        print_header("游戏结束", "green", width=80)
        alive_players = [p for p in self.players if p.alive]
        
        if not alive_players:
            print_header("平局! 所有玩家都死亡了", "yellow")
        elif len(alive_players) == len(self.players):
            print_header("游戏达到最大回合数，以平局结束", "yellow")
        else:
            for player in alive_players:
                print_header(f"{player.name} 获胜!", "green")
        
        # Print stats
        print_divider("*")
        print_header("游戏统计", "blue")
        print(f"总回合数: {turn_count}")
        print(f"弹巢总数: {self.chamber_count}")
        print(f"子弹总数: {len(self.game_state.bullets)}")
        
        # Print full logs with bullet information for spectators
        print_header("游戏详细日志 (包含弹巢信息)", "magenta")
        print(self.game_state.get_status(for_player=False))
        
        # Final visualization of the gun
        print_header("最终枪械状态", "yellow")
        print(self.game_state.visualize_gun())

    def get_neg_prompt(self, player, opponent, message):
        """Generate a negotiation prompt for the opponent"""
        return f"""你是:{opponent.role}
你要以{opponent.style}的风格来进行游戏。
当前游戏中，对手 {player.name} 提出了协商平局的请求。

具体协商内容: "{message}"

当前游戏状态:
{self.game_state.get_status(for_player=True)}

当前扳机位置: {self.game_state.current_position + 1}/{self.chamber_count}
契约状态: {'激活' if self.game_state.contract_active else '未激活'}

你的道具: {opponent.get_items_string()}

请考虑当前游戏状态、你的性格和胜率，你会同意这个协商吗？
请只回复"同意"或"拒绝"以及简短的理由。"""

def main():
    # Game configuration
    game_config = {
        "chamber_count": 6,  # Number of chambers in the gun
        "player_configs": [
            {
                "name": "Bill",
                "role_name": "赌徒",
                "role_style": "激进大胆，喜欢冒险，会极限施压并擅长说谎来干扰对手判断",
                "llm_type": "anthropic"
            },
            {
                "name": "Lee",
                "role_name": "侦探",
                "role_style": "冷静分析，善于推理，会通过逻辑分析来识破对手的谎言和策略",
                "llm_type": "openai"
            }
        ]
    }
    
    # Clear screen for better visualization
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Print game banner
    print_divider("=")
    print(f"{COLORS['bold']}{COLORS['red']}俄罗斯轮盘对决{COLORS['reset']}")
    print_divider("=")
    
    # Initialize and run the game
    game = GameController(chamber_count=game_config["chamber_count"])
    game.setup_game(game_config["player_configs"])
    game.run_game()

if __name__ == "__main__":
    main()
