# OppositionGameBot
Telegram bot to play OppositionGame, online. Bot link https://t.me/OppositionGameBot

You need to create .env file with following variables:
```bash
API_KEY=<API_KEY>
db_file=db.sqlite3
LANGUAGES="ru,en,es"
```

I use SQLite3 for database, because it is lightweight and fast.
This project created for education purposes, I'm new in python.

Dependensies
```bash
pip install python-telegram-bot --upgradeCancel changes
pip install python-dotenv
```

To start the bot
```bash
python3 main.py
```
