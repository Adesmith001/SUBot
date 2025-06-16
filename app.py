import os
from flask import Flask, request
from bot import main
import json

with open('config.json') as f:
    config = json.load(f)

BOT_TOKEN = config['BOT_TOKEN']
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
PORT = int(os.environ.get('PORT', 5000))

app = Flask(__name__)
bot_app = main()

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = request.get_json(force=True)
    bot_app.update_queue.put(update)
    return 'ok'

@app.route('/')
def index():
    return 'Bot is running!'

if __name__ == '__main__':
    bot_app.bot.set_webhook(url=f'{WEBHOOK_URL}/{BOT_TOKEN}')
    app.run(host='0.0.0.0', port=PORT) 