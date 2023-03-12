#import python libs
import os
import gettext
from dotenv import load_dotenv
#my imports
from db import Database
load_dotenv()

# create database object
db = Database(os.getenv("db_file"))

languages = os.getenv('LANGUAGES').split(',')
translation = gettext.translation('messages', localedir='./lang', languages=languages, fallback=True)
_ = translation.gettext

class Game:
    def __init__(self, db):
        self.db = db

    def bot_intro_chat():
        return  _ ('bot_intro_chat_message')
       
    def bot_intro_user():
        return  _ ('bot_intro_user_message')
    
    def rules_about_bot():
        return  _ ('rules_about_bot_message')
    
    def rules_about_game():
        return  _ ('rules_about_game_message')

    def join_game_button(InlineKeyboardMarkup,InlineKeyboardButton):
        msg = _('start_game_button_message')
        keyboard =[
                [
                    InlineKeyboardButton(_("join_game_button_text"), callback_data="game:join"),
                ]
            ]
        markup = InlineKeyboardMarkup(keyboard)
        return  msg,markup

    def start_game_button(InlineKeyboardMarkup,InlineKeyboardButton):
        msg = _('start_game_button_message')
        keyboard =[
                [
                    InlineKeyboardButton(_("start_game_button_text"), callback_data="game:start"),
                ]
            ]
        markup = InlineKeyboardMarkup(keyboard)
        return  msg,markup
    
    def start_game_routines(ChatMember):
        #
        print(ChatMember)
        return  _ ('start_game_routines_message')
    

    