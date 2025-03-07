from typing import Final
import os
import time
import platform
import datetime
from dotenv import load_dotenv
from discord import Intents, Client, Message, Embed, version_info as discord_version
from discord.ext import tasks
from responses import get_response

# Load the environment variables
load_dotenv()

TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
BOT_VERSION: Final[str] = "1.0.0"
BOT_CREATOR: Final[str] = "MAHITO"
ANNOUNCEMENT_CHANNEL_ID: Final[int] = int(os.getenv('ANNOUNCEMENT_CHANNEL_ID', '0'))  # Set your default channel ID in .env

# Set up the bot
Intents: Intents = Intents.default()
Intents.message_content = True
client: Client = Client(intents=Intents)

# Track start time for uptime command
start_time = time.time()

def get_uptime() -> str:
    """Calculate and format the bot's uptime"""
    uptime_seconds = int(time.time() - start_time)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    
    return " ".join(parts)

# Message event
async def send_message(message: Message, user_message: str) -> None:
    if not user_message:
        print('User message is empty because intents were not enabled properly.')
        return
    
    # Handle commands
    if user_message.lower() == '!ping':
        start_time = time.time()
        msg = await message.channel.send('Pinging...')
        end_time = time.time()
        
        # Calculate ping in ms
        ping = round((end_time - start_time) * 1000)
        await msg.edit(content=f'Pong! Latency: {ping}ms | API Latency: {round(client.latency * 1000)}ms')
        return
    
    elif user_message.lower() == '!help':
        # Create an embed for help command
        embed = Embed(title="Bot Help", description="List of available commands:", color=0x3498db)
        embed.add_field(name="!help", value="Shows this help message", inline=False)
        embed.add_field(name="!info", value="Shows information about the bot", inline=False)
        embed.add_field(name="!ping", value="Shows the bot's latency", inline=False)
        embed.add_field(name="?message", value="Sends a private response (prefix any message with ?)", inline=False)
        embed.set_footer(text=f"Bot created by {BOT_CREATOR}")
        
        await message.channel.send(embed=embed)
        return
    
    elif user_message.lower() == '!info':
        # Create an embed for info command
        embed = Embed(title="Bot Information", color=0x2ecc71)
        embed.add_field(name="Version", value=BOT_VERSION, inline=True)
        embed.add_field(name="Creator", value=BOT_CREATOR, inline=True)
        embed.add_field(name="Discord.py Version", value=f"{discord_version.major}.{discord_version.minor}.{discord_version.micro}", inline=True)
        embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
        embed.add_field(name="Platform", value=platform.system() + " " + platform.release(), inline=True)
        embed.add_field(name="Uptime", value=get_uptime(), inline=True)
        embed.set_footer(text="Use !help to see available commands")
        
        await message.channel.send(embed=embed)
        return
    
    if is_private := user_message[0] == '?':
        user_message = user_message[1:]
    
    try:
        response: str = await get_response(user_message)  # Await the coroutine
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(f"Error while processing message: {str(e)}")
        await message.channel.send("Sorry, I encountered an error while processing your request.")

# Define the daily scheduled task
@tasks.loop(hours=24)
async def daily_announcement():
    if ANNOUNCEMENT_CHANNEL_ID == 0:
        print("WARNING: No announcement channel ID set. Skipping daily announcement.")
        return
    
    try:
        channel = client.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        if channel:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            embed = Embed(
                title="Daily Announcement", 
                description="This is an automated daily announcement.", 
                color=0x9b59b6
            )
            embed.add_field(name="Current Date", value=current_time, inline=False)
            embed.add_field(name="Bot Uptime", value=get_uptime(), inline=False)
            embed.set_footer(text=f"Bot Version: {BOT_VERSION}")
            
            await channel.send(embed=embed)
            print(f"Daily announcement sent at {current_time}")
        else:
            print(f"ERROR: Could not find channel with ID {ANNOUNCEMENT_CHANNEL_ID}")
    except Exception as e:
        print(f"ERROR: Failed to send daily announcement: {str(e)}")

# Handling the startups for our bot
@client.event
async def on_ready() -> None:
    print(f'{client.user} has connected to Discord!')
    
    # Start the daily announcement task
    if not daily_announcement.is_running():
        daily_announcement.start()
        print("Daily announcement task started.")

# Handling incoming messages
@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return

    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)

    print(f'[{channel}] {username}: {user_message}')
    
    try:
        await send_message(message, user_message)
    except Exception as e:
        print(f"Error in on_message handler: {str(e)}")

# Additional error handling for Discord client
@client.event
async def on_error(event, *args, **kwargs):
    print(f"Discord error in {event}: {str(args[0])}")

# Main entry point
def main() -> None:
    try:
        client.run(TOKEN)
    except Exception as e:
        print(f"Failed to start the bot: {str(e)}")
        
        # Check for common errors
        if not TOKEN:
            print("ERROR: DISCORD_TOKEN is not set in your .env file")
        elif "improper token" in str(e).lower():
            print("ERROR: Your Discord token appears to be invalid")

if __name__ == '__main__': 
    main()