# LLM Russian Roulette Game

A text-based implementation of Russian Roulette where large language models (LLMs) play against each other in strategic duels.

## Description

This project implements a virtual Russian Roulette game where AI language models compete against each other. The game simulates a revolver with multiple chambers, randomly loaded with bullets. Players take turns deciding whether to shoot themselves or their opponent, with the option to use special items and engage in psychological gameplay through dialogue.

The program demonstrates how different AI personas approach risk management, strategic decision-making, and interpersonal negotiation in a high-stakes environment.

## Features

- Configurable game setup with customizable number of chambers and bullets
- Support for multiple LLM providers (OpenAI, Anthropic Claude, DeepSeek)
- Special items that influence gameplay:
  - **Bullet**: Adds an extra bullet to a random empty chamber
  - **Check**: Inspect a chamber to see if it contains a bullet
  - **Reverse**: Reverses the opponent's next action
  - **Contract**: For 3 turns, if one player is shot, both players lose (draw)
  - **Push**: Advance the trigger position by one chamber
- Rich communication system allowing for negotiation and psychological tactics
- Detailed logging and visualization of game state
- Available in both English and Chinese versions



## Requirements

### Python
- Python 3.8 or higher

### Dependencies
Install the dependencies using:

```
pip install -r requirements.txt
```

### API Keys
You'll need API keys for at least one of the following services:
- OpenAI API (for GPT models)
- Anthropic API (for Claude models)
- DeepSeek API (optional)

### Environment Setup
Make sure your environment variables are properly set up for the API keys specified in your `config.json` file.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/llm_game_Russian_Roulette.git
   cd llm_game_Russian_Roulette
   ```

2. Install dependencies:
   ```
   pip install openai anthropic colorama
   ```

3. Configure API keys:
   - Edit `config.json` to specify the environment variable names for your API keys
   - Set the corresponding environment variables:
     ```
     export GPT_API_KEY="your-openai-api-key"
     export CLAUDE_API_KEY="your-anthropic-api-key"
     export DS_API="your-deepseek-api-key"  # Optional
     ```

## Usage

Run the English version of the game:

```
python game_en.py
```

Or run the Chinese version:

```
python game.py
```

## Game Configuration

You can customize the game by modifying the `game_config` dictionary in either `game_en.py` or `game.py`:

```python
game_config = {
    "chamber_count": 8,  # Number of chambers in the gun
    "player_configs": [
        {
            "name": "Bill",
            "role_name": "Gambler",
            "role_style": "Aggressive and bold, likes taking risks...",
            "llm_type": "anthropic"
        },
        {
            "name": "Lee",
            "role_name": "Detective",
            "role_style": "Calm and analytical, good at reasoning...",
            "llm_type": "openai"
        }
    ]
}
```

## Game Rules

1. A revolver has X chambers, with 1 to X/2 bullets randomly loaded.
2. Players take turns choosing to shoot themselves or their opponent.
3. Before shooting, players can:
   - Use an item from their inventory
   - Communicate with the other player (including negotiation for a draw)
   - Make their shooting decision (self or opponent)
4. The game ends when a player is shot or when players agree to a draw.
5. If Contract is active and a player is shot, both players lose.

## Extending the Game

You can add new LLM providers by extending the `LLMClient` class in `llm_client.py` and updating the `create_llm_client` function.

## Acknowledgments

This project demonstrates the capabilities of modern large language models in complex decision-making scenarios with imperfect information.