import os
import json
from typing import Any, List, Dict, Optional, Union
from abc import ABC, abstractmethod
from openai import OpenAI
import anthropic

# 固定配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

class LLMClient(ABC):
    """Abstract base class for LLM API clients"""
    
    @abstractmethod
    def send_message(self, messages: List[Dict[str, str]]) -> str:
        """Send a message to LLM and return response text
        
        Args:
            messages: List of message objects with 'role' and 'content'
            
        Returns:
            str: Response text
        """
        pass

class OpenAIBaseLLMClient(LLMClient):
    """Base client for OpenAI-compatible APIs"""
    
    def __init__(self, client: OpenAI) -> None:
        self.client = client

class DeepSeekLLMClient(OpenAIBaseLLMClient):
    """Client for DeepSeek API"""
    
    def __init__(self, api_key: str, base_url: str) -> None:
        super().__init__(OpenAI(api_key=api_key, base_url=base_url))
    
    def send_message(self, messages: List[Dict[str, str]]) -> str:
        try:
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=messages,
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"API error: {str(e)}")

class OpenAILLMClient(OpenAIBaseLLMClient):
    """Client for OpenAI API"""
    
    def __init__(self, api_key: str) -> None:
        super().__init__(OpenAI(api_key=api_key))
    
    def send_message(self, messages: List[Dict[str, str]]) -> str:
        try:
            response = self.client.chat.completions.create(
                model="o1-mini",
                messages=messages
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"API error: {str(e)}")

class AnthropicLLMClient(LLMClient):
    """Client for Anthropic API"""
    
    def __init__(self, api_key: str) -> None:
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def send_message(self, messages: List[Dict[str, str]]) -> str:
        try:
            # Extract system message if present
            system_message = ""
            conversation = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    conversation.append(msg)
            
            response = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                system=system_message,
                messages=[{"role": m["role"], "content": m["content"]} for m in conversation],
                max_tokens=2500,
                temperature=1,
                thinking={
                    "type": "enabled",
                    "budget_tokens": 1200
                }
            )
            
            return response.content[1].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

def create_llm_client(provider: str) -> LLMClient:
    """Create an appropriate LLM client based on the provider name
    
    Args:
        provider: The provider name ('deepseek', 'openai', or 'anthropic')
        
    Returns:
        LLMClient: An instance of the appropriate LLM client
    """
    # Load configuration from file
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    if provider == "deepseek":
        api_key_env = config.get("deepseek", {}).get("api_key")
        base_url = config.get("deepseek", {}).get("base_url", "https://api.deepseek.com")
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"API key environment variable {api_key_env} not set")
        return DeepSeekLLMClient(api_key, base_url)
    
    elif provider == "openai":
        api_key_env = config.get("openai", {}).get("api_key")
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"API key environment variable {api_key_env} not set")
        return OpenAILLMClient(api_key)
    
    elif provider == "anthropic":
        api_key_env = config.get("anthropic", {}).get("api_key")
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"API key environment variable {api_key_env} not set")
        return AnthropicLLMClient(api_key)
    
    else:
        raise ValueError(f"Unknown provider: {provider}. Available: deepseek, openai, anthropic")

# 测试样例
def test_llm_clients():
    """Test all available LLM clients"""
    
    test_messages = [
        {"role": "user", "content": "What is the capital of France?"}
    ]
    
    # 测试 OpenAI
    if False:
        try:
            print("\n--- Testing OpenAI Client ---")
            openai_client = create_llm_client("openai")
            response = openai_client.send_message(test_messages)
            print(f"OpenAI Response: {response}")
        except Exception as e:
            print(f"OpenAI test failed: {e}")
    
    # 测试 Anthropic
    if True:
        try:
            print("\n--- Testing Anthropic Client ---")
            anthropic_client = create_llm_client("anthropic")
            response = anthropic_client.send_message(test_messages)
            print(f"Anthropic Response: {response}")
        except Exception as e:
            print(f"Anthropic test failed: {e}")
    
    # 测试 DeepSeek
    if False:
        try:
            print("\n--- Testing DeepSeek Client ---")
            deepseek_client = create_llm_client("deepseek")
            response = deepseek_client.send_message(test_messages)
            print(f"DeepSeek Response: {response}")
        except Exception as e:
            print(f"DeepSeek test failed: {e}")

if __name__ == "__main__":
    test_llm_clients()