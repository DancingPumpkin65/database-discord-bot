# Discord Bot

## Project Structure

```text
    discord-bot
    ├── .env                   # Environment variables
    ├── main.py                # The main bot service that handles Discord events
    ├── responses.py           # The module that provides responses to user inputs
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
```

## Running the API

1. Start the bot:
```sh
    python main.py
```

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.