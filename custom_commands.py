import json
import os
from typing import Dict, List, Optional, Any
import random

class CustomCommandManager:
    """Manages custom commands for the bot"""
    
    def __init__(self, data_file: str = "custom_commands.json"):
        """Initialize the custom command manager"""
        self.data_file = data_file
        self.commands: Dict[str, Dict[str, Any]] = {}
        self.load_commands()
    
    def load_commands(self) -> None:
        """Load commands from the data file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.commands = json.load(f)
            except Exception as e:
                print(f"Error loading custom commands: {str(e)}")
                self.commands = {}
    
    def save_commands(self) -> None:
        """Save commands to the data file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.commands, f, indent=4)
        except Exception as e:
            print(f"Error saving custom commands: {str(e)}")
    
    def add_command(self, guild_id: str, name: str, response: str, creator_id: str) -> bool:
        """Add a new custom command"""
        if guild_id not in self.commands:
            self.commands[guild_id] = {}
            
        name = name.lower()
        if name in self.commands[guild_id]:
            return False  # Command already exists
            
        self.commands[guild_id][name] = {
            "response": response,
            "creator_id": creator_id,
            "uses": 0,
            "created_at": str(datetime.datetime.now())
        }
        
        self.save_commands()
        return True
    
    def edit_command(self, guild_id: str, name: str, new_response: str) -> bool:
        """Edit an existing custom command"""
        if guild_id not in self.commands or name not in self.commands[guild_id]:
            return False
            
        self.commands[guild_id][name]["response"] = new_response
        self.save_commands()
        return True
    
    def delete_command(self, guild_id: str, name: str) -> bool:
        """Delete a custom command"""
        if guild_id not in self.commands or name not in self.commands[guild_id]:
            return False
            
        del self.commands[guild_id][name]
        self.save_commands()
        return True
    
    def get_command(self, guild_id: str, name: str) -> Optional[str]:
        """Get a command's response"""
        if guild_id not in self.commands or name not in self.commands[guild_id]:
            return None
            
        cmd = self.commands[guild_id][name]
        cmd["uses"] += 1
        self.save_commands()
        
        # Process dynamic content
        response = cmd["response"]
        
        # Handle random choices
        if "{random:" in response:
            import re
            for match in re.finditer(r"{random:([^}]+)}", response):
                options = match.group(1).split("|")
                choice = random.choice(options)
                response = response.replace(match.group(0), choice)
        
        return response
    
    def list_commands(self, guild_id: str) -> List[str]:
        """List all custom commands for a guild"""
        if guild_id not in self.commands:
            return []
            
        return list(self.commands[guild_id].keys())
        
    def get_command_details(self, guild_id: str, name: str) -> Optional[Dict[str, Any]]:
        """Get details about a specific command"""
        if guild_id not in self.commands or name not in self.commands[guild_id]:
            return None
            
        return self.commands[guild_id][name]
