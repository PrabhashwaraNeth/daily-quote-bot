import logging
import random
import schedule
import time
import requests
import json
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from threading import Thread
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load user data from a JSON file
def load_user_data():
    try:
        with open('user_data.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save user data to a JSON file
def save_user_data(data):
    with open('user_data.json', 'w') as file:
        json.dump(data, file)

# Define quotes by category
quotes = {
    "motivational": [
        "The best way to predict the future is to create it.",
        "Success is not how high you have climbed, but how you make a positive difference to the world."
    ],
    "inspirational": [
        "Life is 10% what happens to us and 90% how we react to it.",
        "The only limit to our realization of tomorrow is our doubts of today."
    ],
    "life": [
        "Get busy living or get busy dying.",
        "Life is what happens when you're busy making other plans."
    ],
    "love": [
        "You know you're in love when you can't fall asleep because reality is finally better than your dreams.",
        "The greatest thing you'll ever learn is just to love and be loved in return."
    ]
}

# Fetch a random quote from a specified category
def fetch_random_quote(category):
    if category in quotes:
        return random.choice(quotes[category])
    else:
        return "Category not found."

# Function to send daily quotes
def send_daily_quote(context: CallbackContext) -> None:
    user_data = load_user_data()
    chat_id = context.job.context
    if str(chat_id) in user_data:
        preferred_category = user_data[str(chat_id)]["category"]
        quote = fetch_random_quote(preferred_category)
        context.bot.send_message(chat_id=chat_id, text=quote)

# Command to start the daily quotes
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hi Welcome! You will receive a daily quote. Set your preferred time with /settime <HH:MM> and category with /setcategory <category>.')
    
    chat_id = update.message.chat_id
    user_data = load_user_data()

    # Initialize user data if not present
    if str(chat_id) not in user_data:
        user_data[str(chat_id)] = {"time": "09:00", "category": "motivational"}  # Default time and category
        save_user_data(user_data)

    # Schedule daily quotes
    schedule_daily_quote(update, context)

# Function to schedule daily quotes
def schedule_daily_quote(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_data = load_user_data()

    # Get the user's preferred time
    preferred_time = user_data[str(chat_id)]["time"]
    schedule.every().day.at(preferred_time).do(send_daily_quote, context=update.message.chat_id)

    context.job_queue.run_repeating(schedule_jobs, interval=60, first=0, context=chat_id)

# Command to set preferred time for daily quotes
def set_time(update: Update, context: CallbackContext) -> None:
    if context.args:
        new_time = context.args[0]
        try:
            datetime.strptime(new_time, "%H:%M")  # Validate time format
            chat_id = update.message.chat_id
            user_data = load_user_data()
            user_data[str(chat_id)]["time"] = new_time
            save_user_data(user_data)
            update.message.reply_text(f'Your preferred time has been set to {new_time}.')
        except ValueError:
            update.message.reply_text('Please use the format HH:MM (24-hour format).')
    else:
        update.message.reply_text('Please provide a time in HH:MM format.')

# Command to set preferred category for quotes
def set_category(update: Update, context: CallbackContext) -> None:
    if context.args:
        new_category = context.args[0].lower()
        if new_category in quotes:
            chat_id = update.message.chat_id
            user_data = load_user_data()
            user_data[str(chat_id)]["category"] = new_category
            save_user_data(user_data)
            update.message.reply_text(f'Your preferred quote category has been set to {new_category}.')
        else:
            update.message.reply_text('Available categories are: motivational, inspirational, life, love.')
    else:
        update.message.reply_text('Please provide a category (motivational, inspirational, life, love).')

# Command to get a quote on demand
def quote(update: Update, context: CallbackContext) -> None:
    if context.args:
        category = context.args[0].lower()
        quote = fetch_random_quote(category)
        update.message.reply_text(quote)
    else:
        update.message.reply_text('Please specify a category (motivational, inspirational, life, love).')

# Command to provide the YouTube channel link
def youtube(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Check out my YouTube channel: [MindWARRIOR](https://www.youtube.com/@Mind4WORRIOR', parse_mode='Markdown')

# Function to run scheduled jobs
def schedule_jobs(context: CallbackContext):
    schedule.run_pending()

# Error handler
def error(update: Update, context: CallbackContext) -> None:
    logger.warning(f'Update {update} caused error {context.error}')

def main() -> None:
    updater = Updater("YOUR_TOKEN")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("settime", set_time))
    dispatcher.add_handler(CommandHandler("setcategory", set_category))
    dispatcher.add_handler(CommandHandler("quote", quote))
    dispatcher.add_handler(CommandHandler("youtube", youtube))

    # Log all errors
    dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Start a thread for running scheduled jobs
    Thread(target=schedule_jobs, args=(updater.bot,), daemon=True).start()

    # Run the bot until you press Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main()
