# Happy Hour TLV Bot 🍻

A Telegram bot that helps users find the best happy hour deals in Tel Aviv. Available in both English and Hebrew!

## Features

- 🔍 Find happy hours by location
- ⏰ See currently active happy hours
- 🌟 View popular spots
- 🗺️ Google Maps integration
- 🌐 Bilingual support (English/Hebrew)
- 💰 Price range indicators
- 🎯 Venue vibes and descriptions

## Development Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd HappyHour
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your Telegram bot token:
```
TELEGRAM_TOKEN=your_bot_token_here
```

5. Run the bot:
```bash
python src/bot.py
```

## Deployment

This bot can be deployed to Railway.app:

1. Create a Railway account at https://railway.app
2. Install Railway CLI:
```bash
npm i -g @railway/cli
```

3. Login to Railway:
```bash
railway login
```

4. Create a new project:
```bash
railway init
```

5. Add your environment variables:
```bash
railway variables set TELEGRAM_TOKEN=your_bot_token_here
```

6. Deploy:
```bash
railway up
```

## Contributing

Feel free to submit issues and enhancement requests! 