#import python libs
import os
from dotenv import load_dotenv
import logging
import gettext
from typing import Optional, Tuple
#import Telegram API
import telegram
from telegram.ext import Application,CommandHandler, MessageHandler, CallbackQueryHandler, InlineQueryHandler, ContextTypes, filters,ChatMemberHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ChatMemberUpdated, ChatMember, Chat
#my imports
from db import Database
from game import Game

load_dotenv()

# create database object
db = Database(os.getenv("db_file"))
# create table if not exists
db.create_tables()

# get API_KEY from .env file
API_KEY = os.getenv("API_KEY")
languages = os.getenv('LANGUAGES').split(',')

translation = gettext.translation('messages', localedir='./lang', languages=languages, fallback=True)
_ = translation.gettext


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a bot object
bot = telegram.Bot(token=API_KEY)

# Create a handler for the /start command
async def on_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Get the chat ID and language preference
    chat_id = update.message.chat_id
    user_lang = update.message.from_user.language_code

    print(update)

    if update.message.chat.type == Chat.PRIVATE:
        #if user_lang is in languages, send a welcome message:
        if user_lang in languages:
            #save user_lang to database
            values = {'id': update.message.from_user.id, 'lang': user_lang, 'name': update.message.from_user.full_name}
            db.set('users', values)
            await update.message.reply_text(Game.bot_intro_user())
        else:
            # Send a welcome message and language selection keyboard
            welcome_msg = "Hello! Your language is {}. Please choose another language, which is closer to you and in which the bot can communicate.".format(user_lang)
            keyboard =[
                    [
                        InlineKeyboardButton("English 🇬🇧", callback_data="lang:en"),
                        InlineKeyboardButton("Русский 🇷🇺", callback_data="lang:ru"),
                        InlineKeyboardButton("Español 🇪🇸", callback_data="lang:es"),
                    ]
                ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text=welcome_msg, reply_markup=reply_markup)
    else:
        #check if user admin
        #delete games in this chat (clean chat games table)
        #save ID who start the game
        #create game table
        #values = {'id': update.message.from_user.id}
        #db.set('games', values)
        msg, markup = Game.join_game_button(InlineKeyboardMarkup,InlineKeyboardButton)
        await update.message.reply_text(text=msg, reply_markup=markup)
        msg, markup = Game.start_game_button(InlineKeyboardMarkup,InlineKeyboardButton)
        await update.message.reply_text(text=msg, reply_markup=markup)


async def temp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Get the chat ID and language preference
    user_id = update.message.from_user.id
   
    #get user_lang from database
    user_lang = db.get_by_id('users', user_id)
    await update.message.reply_text('Language is: ' + user_lang['lang'])

async def Callback_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #Parses the CallbackQuery and updates the message text or sends an alert message
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    command = query.data.split(':')[0]

    if command == 'lang':
        lang = query.data.split(':')[1]
        await select_lang(query,lang)
    elif command == 'game':
        subcommand = query.data.split(':')[1]
        if subcommand == 'join':
           # register user on game in unic game table
           await bot.answer_callback_query(query.id,text=_("request_to_join_game_success"),show_alert=True)
        if subcommand == 'start':
           # check if user is game owner (who send /start command)
           # get Game.start_game_routines() and reply to the user
           #Game.start_game_routines(members)
           await bot.answer_callback_query(query.id,text=_("request_to_start_game_success"),show_alert=True)
        else:
            return None   
    else:
        await bot.answer_callback_query(query.id,text="Wrong option",show_alert=True)
    
async def select_lang(query,lang):
    #save user_lang to database
    values = {'id': query.from_user.id, 'lang': lang, 'name': query.from_user.full_name}
    db.set('users', values)
    await query.edit_message_text(text=_('selected_language')+f": {lang}")


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("get message query")
    #some checks of user input

    #not found message to reply to the user
    await update.message.reply_text(_('Reply_not_found'))

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Get the chat ID and language preference
    chat_id = update.inline_query.from_user.id
    logger.info("get inline query")
    
    await update.message.reply_text(_('inline_q {chat_id}'))

def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member

async def new_in_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return
    was_member, is_member = result

    # Let's check who is responsible for the change
    cause_name = update.effective_user.full_name

    # Handle chat types differently:
    chat = update.effective_chat
    if chat.type == Chat.PRIVATE:
        if not was_member and is_member:
            # This may not be really needed in practice because most clients will automatically
            # send a /start command after the user unblocks the bot, and start_private_chat()
            # will add the user to "user_ids".
            # We're including this here for the sake of the example.
            logger.info("%s unblocked the bot", cause_name)
        elif was_member and not is_member:
            logger.info("%s blocked the bot", cause_name)
            db.del_by_id('users', chat.id)
    elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if not was_member and is_member:
            logger.info("%s added the bot to the group %s", cause_name, chat.title)
            values = {'id': chat.id, 'cause_name': cause_name, 'title': chat.title}
            db.set('chats', values)
            #send welcome messagge to all members of the group
            await context.bot.send_message(chat_id=chat.id,text=Game.bot_intro_chat())
            msg, markup = Game.start_game_button(InlineKeyboardMarkup,InlineKeyboardButton)
            await context.bot.send_message(chat_id=chat.id,text=msg, reply_markup=markup)
        elif was_member and not is_member:
            logger.info("%s removed the bot from the group %s", cause_name, chat.title)
            db.del_by_id('chats', chat.id)
    else:
        if not was_member and is_member:
            logger.info("%s added the bot to the channel %s", cause_name, chat.title)
            await bot.leave_chat(chat.id)
        elif was_member and not is_member:
            logger.info("%s removed the bot from the channel %s", cause_name, chat.title)
            #context.bot_data.setdefault("channel_ids", set()).discard(chat.id)

def main():
    # Create the Application and pass it bot's token.
    application = Application.builder().token(API_KEY).build()

    # Command handlers
    application.add_handler(CommandHandler("start", on_start))
    #delete in production
    application.add_handler(CommandHandler("lang", temp))

    # Callback handlers
    application.add_handler(InlineQueryHandler(inline_query))
    application.add_handler(CallbackQueryHandler(Callback_button))

    # on add/remove bot to/from chat
    application.add_handler(ChatMemberHandler(new_in_chat, ChatMemberHandler.MY_CHAT_MEMBER))

    # on non command i.e message - send the message on Telegram
    application.add_handler(MessageHandler((filters.TEXT & ~filters.COMMAND) | filters.Entity('mention'), on_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == '__main__':
    main()