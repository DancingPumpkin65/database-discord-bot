from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message
from responses import get_response

# Load the environment variables
load_dotenv()

TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# Set up the bot
Intents: Intents = Intents.default()
Intents.message_content = True
client: Client = Client(intents=Intents)

# Message event
async def send_message(message: Message, user_message: str) -> None:
    if not user_message:
        print('User message is empty because intents were not enabled properly.')
        return
    
    if is_private := user_message[0] == '?':
        user_message = user_message[1:]
    
    try:
        response: str = await get_response(user_message)  # Await the coroutine
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)

# Handling the startups for our bot
@client.event
async def on_ready() -> None:
    print(f'{client.user} has connected to Discord!')

# Handling incoming messages
@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return

    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)

    print(f'[{channel}] {username}: {user_message}')
    await send_message(message, user_message)

# Main entry point
def main() -> None:
    client.run(TOKEN)

if __name__ == '__main__': 
    main()