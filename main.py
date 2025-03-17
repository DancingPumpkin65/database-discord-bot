from typing import Final
import os
import time
import platform
import datetime
from dotenv import load_dotenv
from discord import Intents, Client, Message, Embed, version_info as discord_version
from discord.ext import tasks, commands
from responses import get_response
import discord
from discord.file import File
from welcome_card import create_welcome_card, create_welcome_embed
from config import GuildConfig

# Load the environment variables
load_dotenv()

TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
BOT_VERSION: Final[str] = "1.0.0"
BOT_CREATOR: Final[str] = "MAHITO"
ANNOUNCEMENT_CHANNEL_ID: Final[int] = int(os.getenv('ANNOUNCEMENT_CHANNEL_ID', '0'))  # Set your default channel ID in .env
PREFIX: Final[str] = os.getenv('COMMAND_PREFIX', '!')  # Configurable command prefix

# Set up the bot
Intents: Intents = Intents.default()
Intents.message_content = True
Intents.members = True  # Enable member intents for welcome messages
client: Client = Client(intents=Intents)

# Track start time for uptime command
start_time = time.time()

# Available commands list for error handling
COMMANDS = ['!ping', '!help', '!info', '!poll', '!stats', '!remind', '!welcome']
COMMAND_SUGGESTIONS = {
    'ping': '!ping',
    'help': '!help',
    'info': '!info',
    'hlp': '!help',
    'nfo': '!info',
    'pong': '!ping',
    'pol': '!poll',
    'pools': '!poll',
    'stat': '!stats',
    'statistics': '!stats',
    'remind': '!remind',
    'reminder': '!remind',
    'wel': '!welcome',
}

# Role-based command permissions
ADMIN_COMMANDS = ['!welcome', '!announce']
MOD_COMMANDS = ['!mute', '!clear']

# Function to check if user has required permissions
def has_permission(message: Message, command: str) -> bool:
    """Check if a user has permission to use a command"""
    if command in ADMIN_COMMANDS:
        return message.author.guild_permissions.administrator
    elif command in MOD_COMMANDS:
        return message.author.guild_permissions.manage_messages
    return True  # Default allow for regular commands

# Polls storage (message_id -> poll_data)
active_polls = {}

# Reminders storage (user_id -> list of reminders)
reminders = {}

# Stats tracking
message_counts = {}
command_counts = {}

# Initialize the guild config
guild_config = GuildConfig()

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

# Function to get command suggestion
def get_command_suggestion(cmd: str) -> str:
    """Get a command suggestion based on user input"""
    # Remove leading '!' if present
    cleaned_cmd = cmd.lstrip('!')
    
    # Direct match in our suggestions dictionary
    if cleaned_cmd in COMMAND_SUGGESTIONS:
        return COMMAND_SUGGESTIONS[cleaned_cmd]
    
    # Check for similar commands (simple implementation)
    for valid_cmd in COMMANDS:
        if valid_cmd.lstrip('!') in cleaned_cmd or cleaned_cmd in valid_cmd.lstrip('!'):
            return valid_cmd
    
    return None

# Message event
async def send_message(message: Message, user_message: str) -> None:
    if not user_message:
        print('User message is empty because intents were not enabled properly.')
        return
    
    # Track stats
    user_id = str(message.author.id)
    if user_id not in message_counts:
        message_counts[user_id] = 0
    message_counts[user_id] += 1
    
    # Handle commands
    if user_message.lower().startswith('!'):
        command = user_message.split()[0].lower()
        
        # Check permissions
        if not has_permission(message, command):
            await message.channel.send("You don't have permission to use this command.")
            return
        
        # Track command usage
        if command not in command_counts:
            command_counts[command] = 0
        command_counts[command] += 1
    
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
    
    elif user_message.lower().startswith('!poll '):
        # Create a simple poll
        poll_text = user_message[6:].strip()
        if not poll_text:
            await message.channel.send("Please provide a poll question.")
            return
            
        poll_embed = Embed(title="📊 Poll", description=poll_text, color=0x3498db)
        poll_embed.set_footer(text=f"Poll created by {message.author.display_name}")
        
        poll_msg = await message.channel.send(embed=poll_embed)
        # Add reactions
        await poll_msg.add_reaction('👍')
        await poll_msg.add_reaction('👎')
        await poll_msg.add_reaction('🤷')
        
        # Store poll
        active_polls[poll_msg.id] = {
            'creator': message.author.id,
            'question': poll_text,
            'timestamp': datetime.datetime.now()
        }
        return
        
    elif user_message.lower().startswith('!stats'):
        # Show user stats
        target = message.author
        target_id = str(target.id)
        
        stats_embed = Embed(title=f"Stats for {target.display_name}", color=0x9b59b6)
        stats_embed.add_field(
            name="Messages Sent", 
            value=str(message_counts.get(target_id, 0)), 
            inline=True
        )
        stats_embed.add_field(
            name="Commands Used", 
            value=str(sum(1 for cmd_id in command_counts if cmd_id == target_id)), 
            inline=True
        )
        stats_embed.set_footer(text="Stats since bot started")
        
        await message.channel.send(embed=stats_embed)
        return
        
    elif user_message.lower().startswith('!remind '):
        # Set a reminder
        parts = user_message[8:].split(maxsplit=1)
        if len(parts) != 2:
            await message.channel.send("Usage: !remind [time in minutes] [reminder text]")
            return
            
        try:
            minutes = int(parts[0])
            reminder_text = parts[1]
            
            if minutes <= 0 or minutes > 1440:  # Max 24 hours (1440 minutes)
                await message.channel.send("Please specify a time between 1 and 1440 minutes (24 hours).")
                return
                
            user_id = message.author.id
            if user_id not in reminders:
                reminders[user_id] = []
                
            reminder_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
            reminders[user_id].append({
                'time': reminder_time,
                'text': reminder_text,
                'channel_id': message.channel.id
            })
            
            await message.channel.send(f"✅ I'll remind you about **{reminder_text}** in **{minutes}** minutes.")
            return
        except ValueError:
            await message.channel.send("Please specify a valid number of minutes.")
            return
            
    elif user_message.lower() == '!welcome':
        if not message.author.guild_permissions.administrator:
            await message.channel.send("You need administrator permissions to set welcome messages.")
            return
            
        embed = Embed(title="Welcome Message Configuration", color=0x2ecc71)
        embed.add_field(
            name="Current Status", 
            value="Welcome messages are enabled.", 
            inline=False
        )
        embed.add_field(
            name="How to Use", 
            value="To toggle welcome messages, use `!welcome toggle`.\n"
                  "To set a custom welcome message, use `!welcome set [message]`.", 
            inline=False
        )
        embed.add_field(
            name="Variables", 
            value="{user} - The username\n{server} - The server name", 
            inline=False
        )
        
        await message.channel.send(embed=embed)
        return
    
    elif user_message.lower().startswith('!welcome'):
        # Process welcome command with arguments
        args = user_message.split()[1:] if len(user_message.split()) > 1 else []
        await handle_welcome_command(message, args)
        return
    
    # Error handling for command-like messages that don't match any command
    elif user_message.startswith('!'):
        command = user_message.split()[0].lower()
        suggestion = get_command_suggestion(command)
        
        error_msg = f"Command `{command}` not found."
        if suggestion:
            error_msg += f" Did you mean `{suggestion}`?"
        error_msg += " Type `!help` to see all available commands."
        
        await message.channel.send(error_msg)
        return
    
    if is_private := user_message[0] == '?':
        user_message = user_message[1:]
    
    try:
        response: str = await get_response(user_message)  # Await the coroutine
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(f"Error while processing message: {str(e)}")
        await message.channel.send("Sorry, I encountered an error while processing your request.")

# Check reminders every minute
@tasks.loop(minutes=1)
async def check_reminders():
    now = datetime.datetime.now()
    to_remove = []
    
    for user_id, user_reminders in reminders.items():
        for reminder in user_reminders[:]:  # Create a copy to safely modify during iteration
            if now >= reminder['time']:
                try:
                    channel = client.get_channel(reminder['channel_id'])
                    if channel:
                        user = await client.fetch_user(user_id)
                        await channel.send(f"⏰ Reminder for {user.mention}: {reminder['text']}")
                    user_reminders.remove(reminder)
                except Exception as e:
                    print(f"Error sending reminder: {str(e)}")
                    user_reminders.remove(reminder)
        
        # If user has no more reminders, mark for removal
        if not user_reminders:
            to_remove.append(user_id)
    
    # Clean up empty reminder lists
    for user_id in to_remove:
        del reminders[user_id]

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
    
    # Start the tasks
    if not daily_announcement.is_running():
        daily_announcement.start()
        print("Daily announcement task started.")
        
    if not check_reminders.is_running():
        check_reminders.start()
        print("Reminder check task started.")

# Welcome new members
@client.event
async def on_member_join(member):
    try:
        # Get the welcome configuration for this guild
        guild_id = str(member.guild.id)
        welcome_enabled = guild_config.get(guild_id, "welcome_enabled")
        
        if not welcome_enabled:
            return
        
        # Get the welcome channel (custom or system)
        custom_channel_id = guild_config.get(guild_id, "welcome_channel")
        if custom_channel_id:
            welcome_channel = client.get_channel(int(custom_channel_id))
        else:
            welcome_channel = member.guild.system_channel
        
        if not welcome_channel:
            return
        
        # Get custom welcome message if set
        welcome_message = guild_config.get(guild_id, "welcome_message")
        welcome_message = welcome_message.replace("{user}", member.display_name).replace("{server}", member.guild.name)
        
        # Get guild accent color (or use default)
        accent_color = (46, 204, 113)  # Default green
        
        # Create and send the welcome card
        card_image = await create_welcome_card(
            username=member.display_name,
            avatar_url=member.display_avatar.url,
            server_name=member.guild.name,
            member_count=len(member.guild.members),
            custom_message=welcome_message,
            accent_color=accent_color
        )
        
        if card_image:
            # Create welcome embed to accompany the image
            embed = create_welcome_embed(
                username=member.mention,
                server_name=member.guild.name,
                member_count=len(member.guild.members),
                user_id=member.id
            )
            
            # Send the welcome card with embed
            await welcome_channel.send(
                file=File(fp=card_image, filename="welcome.png"),
                embed=embed
            )
        else:
            # Fallback to basic embed if image creation fails
            embed = Embed(
                title=f"Welcome to {member.guild.name}!",
                description=f"Hello {member.mention}! {welcome_message}",
                color=0x2ecc71
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Member Count", value=f"{len(member.guild.members)} members")
            embed.set_footer(text=f"User ID: {member.id}")
            
            await welcome_channel.send(embed=embed)
    except Exception as e:
        print(f"Error in welcome message: {str(e)}")

# Update the !welcome command to configure welcome settings
async def handle_welcome_command(message, args):
    """Handle welcome command and its subcommands"""
    if not message.guild:
        await message.channel.send("This command can only be used in a server.")
        return
        
    if not message.author.guild_permissions.administrator:
        await message.channel.send("You need administrator permissions to use this command.")
        return
    
    guild_id = str(message.guild.id)
    
    # No arguments - show current settings
    if not args:
        welcome_enabled = guild_config.get(guild_id, "welcome_enabled")
        welcome_message = guild_config.get(guild_id, "welcome_message")
        custom_channel_id = guild_config.get(guild_id, "welcome_channel")
        
        status = "enabled" if welcome_enabled else "disabled"
        channel_text = f"<#{custom_channel_id}>" if custom_channel_id else "Default system channel"
        
        embed = Embed(title="Welcome Message Configuration", color=0x2ecc71)
        embed.add_field(name="Status", value=status.capitalize(), inline=True)
        embed.add_field(name="Channel", value=channel_text, inline=True)
        embed.add_field(name="Current Message", value=welcome_message, inline=False)
        
        embed.add_field(
            name="Commands", 
            value=(
                "`!welcome toggle` - Enable/disable welcome messages\n"
                "`!welcome message <text>` - Set custom welcome message\n"
                "`!welcome channel <#channel>` - Set welcome channel\n"
                "`!welcome test` - Test current welcome message\n"
                "`!welcome reset` - Reset to defaults"
            ),
            inline=False
        )
        
        embed.add_field(
            name="Variables", 
            value=(
                "{user} - The username\n"
                "{server} - The server name"
            ),
            inline=False
        )
        
        await message.channel.send(embed=embed)
        return
    
    # Handle subcommands
    subcommand = args[0].lower()
    
    if subcommand == "toggle":
        current = guild_config.get(guild_id, "welcome_enabled")
        guild_config.set(guild_id, "welcome_enabled", not current)
        new_status = "enabled" if not current else "disabled"
        await message.channel.send(f"✅ Welcome messages are now {new_status}.")
        
    elif subcommand == "message" and len(args) > 1:
        new_message = " ".join(args[1:])
        guild_config.set(guild_id, "welcome_message", new_message)
        await message.channel.send(f"✅ Welcome message updated!")
        
    elif subcommand == "channel":
        if not message.channel_mentions:
            await message.channel.send("Please mention a channel: `!welcome channel #channel`")
            return
            
        channel = message.channel_mentions[0]
        guild_config.set(guild_id, "welcome_channel", str(channel.id))
        await message.channel.send(f"✅ Welcome channel set to {channel.mention}")
        
    elif subcommand == "test":
        # Simulate welcome message for the command user
        welcome_message = guild_config.get(guild_id, "welcome_message")
        welcome_message = welcome_message.replace("{user}", message.author.display_name).replace("{server}", message.guild.name)
        
        card_image = await create_welcome_card(
            username=message.author.display_name,
            avatar_url=message.author.display_avatar.url,
            server_name=message.guild.name,
            member_count=len(message.guild.members),
            custom_message=welcome_message
        )
        
        if card_image:
            embed = create_welcome_embed(
                username=message.author.mention,
                server_name=message.guild.name,
                member_count=len(message.guild.members),
                user_id=message.author.id
            )
            
            await message.channel.send(
                content="**Welcome Card Preview:**",
                file=File(fp=card_image, filename="welcome_preview.png"),
                embed=embed
            )
        else:
            await message.channel.send("Failed to generate welcome card preview.")
            
    elif subcommand == "reset":
        guild_config.reset(guild_id, "welcome_enabled")
        guild_config.reset(guild_id, "welcome_message")
        guild_config.reset(guild_id, "welcome_channel")
        await message.channel.send("✅ Welcome settings have been reset to defaults.")
        
    else:
        await message.channel.send("Unknown subcommand. Type `!welcome` to see available options.")

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
        error_embed = Embed(
            title="Error", 
            description="An error occurred while processing your message.", 
            color=0xe74c3c
        )
        error_embed.add_field(name="What happened?", value="The bot encountered an unexpected issue.")
        error_embed.add_field(name="What to do?", value="Please try again later or contact the bot administrator.")
        error_embed.set_footer(text="Use !help to see available commands")
        
        try:
            await message.channel.send(embed=error_embed)
        except:
            # If even sending the error embed fails, try a simple message
            await message.channel.send("Sorry, an error occurred while processing your message.")

# Track reaction changes for polls
@client.event
async def on_raw_reaction_add(payload):
    if payload.message_id in active_polls:
        # Someone voted on a poll
        channel = client.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        
        # Update poll data if needed
        # This is just a placeholder - you could track votes here

# Additional error handling for Discord client
@client.event
async def on_error(event, *args, **kwargs):
    error = args[0] if args else "Unknown error"
    print(f"Discord error in {event}: {str(error)}")
    
    # Try to send error details to a log channel if available
    try:
        if event == 'on_message' and ANNOUNCEMENT_CHANNEL_ID != 0:
            log_channel = client.get_channel(ANNOUNCEMENT_CHANNEL_ID)
            if log_channel:
                embed = Embed(title="Bot Error", description=f"An error occurred in event: {event}", color=0xe74c3c)
                embed.add_field(name="Error", value=str(error)[:1024])  # Truncate if too long
                embed.add_field(name="Time", value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                await log_channel.send(embed=embed)
    except Exception as e:
        print(f"Error in error handler: {str(e)}")

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
        elif "privileged intent" in str(e).lower():
            print("ERROR: You need to enable privileged intents in the Discord Developer Portal")
            print("Visit: https://discord.com/developers/applications")

if __name__ == '__main__': 
    main()