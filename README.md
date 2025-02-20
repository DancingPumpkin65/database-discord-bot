# Discord Bot

This repository contains a Discord bot that interacts with users by responding to their messages. The bot uses a FastAPI service to manage chat responses stored in a database. The bot can handle both public and private messages and provides predefined responses based on user inputs.

## Project Structure

```text
    discord-bot
    ├── .env                   # Environment variables
    ├── main.py                # The main bot service that handles Discord events
    ├── responses.py           # The module that provides responses to user inputs
    ├── service.py             # The FastAPI service for managing chat responses
    ├── requirements.txt       # Project dependencies
    └── README.md              # Project documentation
```

## Setup

1. Clone the repository:
```sh
    git clone https://github.com/DancingPumpkin65/discord-bot.git
    cd discord-bot
```

2. Create and activate a virtual environment:
```sh
    python -m venv env
    source env/Scripts/activate  # On Windows
    source env/bin/activate      # On Unix or MacOS
```

3. Install the dependencies:
```sh
    pip install -r requirements.txt
```

4. Set up the environment variables:
    Create a `.env` file in the root directory and add your Discord token:
```sh
    DISCORD_TOKEN=YOUR_DISCORD_TOKEN
    DATABASE_URL=YOUR_DATABASE_URL
```

## Running the FastAPI Service

1. Start the FastAPI service:
```sh
uvicorn service:app --host 0.0.0.0 --port 8001
```

## Running the Discord Bot

1. Start the bot:
```sh
python main.py
```

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.