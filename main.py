#import python libs
import os
from dotenv import load_dotenv
import logging
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
_ = Game.get_lang(Game,'ru')

_ ('bot_intro_chat_message')
_ ('bot_intro_user_message')
_ ('rules_about_bot_message')
_ ('rules_about_bot_message')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a bot object
bot = telegram.Bot(token=API_KEY)

async def on_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_lang = update.message.from_user.language_code
    _ = Game.get_lang(Game,user_lang)
    await update.message.reply_text(_ ('rules_about_game_message'))

# Create a handler for the /start command
async def on_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Get the chat ID and language preference
    chat_id = update.message.chat_id
    user_lang = update.message.from_user.language_code
    _ = Game.get_lang(Game,user_lang)

    if update.message.chat.type == Chat.PRIVATE:
        #if user_lang is in languages, send a welcome message:
        if user_lang in languages:
            #save user_lang to database
            values = {'id': update.message.from_user.id, 'lang': user_lang, 'name': update.message.from_user.full_name}
            db.set('users', values)
            await update.message.reply_text(_ ('bot_intro_user_message'))
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
        #check if user telegram chat admin
        chat_id = update.message.chat_id
        chat_admin = await context.bot.get_chat_administrators(chat_id)
        chat_admins = [admin.user.id for admin in chat_admin]
    
        if update.message.from_user.id in chat_admins:
            #delete games in this chat (clean chat games table)
            try:
                db.droptable('game_'+str(abs(chat_id)))
                db.droptable('mc_'+str(abs(chat_id)))
                db.del_by_id('options', str(abs(chat_id)))
            except:
                print('error deleting game_'+str(chat_id))
                pass
            
            
            msg, markup = Game.join_game_button(user_lang,InlineKeyboardMarkup,InlineKeyboardButton)
            await update.message.reply_text(text=msg, reply_markup=markup)
            
            msg, markup = Game.start_game_button(user_lang,InlineKeyboardMarkup,InlineKeyboardButton)
            await update.message.reply_text(text=msg, reply_markup=markup)
            db.set('options',values={'id':abs(chat_id),'lang':user_lang,'round':1,'failcnt':0,'gov':0,'opp':0})
        else:
            #send message that you are not admin
            await update.message.reply_text(_('you_r_not_admin_message'))


async def Callback_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #Parses the CallbackQuery and updates the message text or sends an alert message
    query = update.callback_query
    user_id=query.from_user.id
    chat_id = query.message.chat.id
    name = query.from_user.full_name
    
    values = {'name': query.from_user.full_name}
    db.update('users', values, where='id='+str(user_id))

    options = db.get_by_id('options',abs(chat_id))
    user_lang=options['lang']
    _ = Game.get_lang(Game,user_lang)

    # CallbackQueries need to be answered, even if no notification to the user is needed
    command = query.data.split(':')[0]

    if command == 'lang':
        lang = query.data.split(':')[1]
        await select_lang(query,lang)
    elif command == 'game':
        subcommand = query.data.split(':')[1]
        if subcommand == 'join':
           #create game table and add user to it if game is not started
           db.create_game_tables(game_id=str(abs(chat_id)))
           if not Game.is_game_started(chat_id):
                #check max players count
                if len(Game.get_players(chat_id)) >= Game.max_players:
                    await bot.answer_callback_query(query.id,text=_('max_players_warn'),show_alert=True)
                else:
                    #add user to game
                    add_user=Game.add_gamer(chat_id,user_id,name)
                    #if user not in table users - send message to user, that he need to PM bot
                    check_user=Game.check_pm_user(user_id)
                    if not check_user:
                        await bot.answer_callback_query(query.id,text=_('you_r_not_start_bot_pls_pm_bot'),show_alert=True)
           else:
                add_user=False
           if add_user:
               await query.message.reply_text(_('join_game:')+' '+name)
               if len(Game.get_players(chat_id)) >= Game.max_players:
                   await query.message.reply_text(_('max_players_done_let_game_start'))
           else:
               await bot.answer_callback_query(query.id,text=_("you_already_in_game_or_game_started"),show_alert=True)
               
        if subcommand == 'start':
           # check if user is admin
           chat_admin = await context.bot.get_chat_administrators(chat_id)
           chat_admins = [admin.user.id for admin in chat_admin]
           if user_id in chat_admins:
               #check minimal amount of players
               if len(Game.get_players(chat_id)) >= Game.min_players:
                    #do Game start routine
                    await bot.answer_callback_query(query.id,text=_('you_r_start_game'),show_alert=True) 
                    #await query.edit_message_text(text=_('game_is_started'))
                    routine=await Game.start_game_routines(Game,chat_id,bot,user_lang)
                    if routine:
                        await Game.round_one(chat_id,bot,user_lang,InlineKeyboardMarkup,InlineKeyboardButton)
                    else:
                        await query.message.reply_text(_('error_start_game_pls_try_again'))
               else:
                    await bot.answer_callback_query(query.id,text=_('min_players_warn'),show_alert=True)               
           else:
               #send message that you are not admin
               await bot.answer_callback_query(query.id,text=_('you_r_not_admin_message'),show_alert=True)           
        else:
            return None   
    elif command == 'getmission':
        userid = query.data.split(':')[2]
        round = query.data.split(':')[1]
        print('callback ROUND '+str(round))
        #check callback mission commander
        if  Game.check_mission_commander(chat_id,user_id,round):
            db.update('game_'+str(abs(chat_id)),values={'round':round},where='id='+str(userid))
            user = db.get('users','id='+str(userid))
            await query.message.reply_text(_('go_to_mission: ')+user[0]['name'])
            round_real = options['round']
            round_count_players = Game.get_round_count_players(chat_id,round_real)
            now_count_players = Game.get_now_count_players(chat_id,round)
            if round_count_players != now_count_players:
                #replace message with go to mission button
                players=db.get('game_'+str(abs(chat_id)),where='round='+str(round))
                ids = [row['id'] for row in players]
                
                message=_('mission_commander: ')+user[0]['name']+'\n'+_('chose_players_next_meeting')+'\n\n'+_('u_need_choose_N_players:')+' '+str(round_count_players)
                markup = Game.players_buttons(chat_id,round,InlineKeyboardMarkup,InlineKeyboardButton,where='id NOT IN ('+', '.join(str(id) for id in ids)+')')
                await query.edit_message_text(text=message, reply_markup=markup)
            else:
                message=_('mission_commander: ')+user[0]['name']+'\n'+_('all_players_selected')
                await query.edit_message_text(text=message)
                #vote to go to meeting message with buttons
                msg, markup = Game.vote_meeting_team_button(user_lang,InlineKeyboardMarkup,InlineKeyboardButton)
                await query.message.reply_text(text=msg, reply_markup=markup)               
        else:
            await bot.answer_callback_query(query.id,text=_('you_r_not_mission_commander'),show_alert=True)
    elif command == 'currentmission':
        vote = query.data.split(':')[1]
        db.update('game_'+str(abs(chat_id)),values={'vote':int(vote)},where='id='+str(user_id))
        voted_players=db.get('game_'+str(abs(chat_id)),where='vote NOT NULL')
        players=db.get('game_'+str(abs(chat_id)))
        failcnt=options['failcnt']
        if len(voted_players)==len(players):
            Confirm=[]
            Against=[]
            for player in voted_players:
                if player['vote']>0:
                    Confirm.append(player['name'])
                else:
                    Against.append(player['name'])
            if len(Confirm)>len(Against):
                #send list of voters
                await query.edit_message_text(text=_('all_voted_mission_team_confirmed')+'\n\n'+_('voters_confirmed')+' '+', '.join(Confirm)+'\n\n'+_('voters_against')+' '+', '.join(Against))
                msg, markup = Game.vote_meeting_button(user_lang,InlineKeyboardMarkup,InlineKeyboardButton)
                await query.message.reply_text(text=msg, reply_markup=markup)
                db.update('game_'+str(abs(chat_id)),values={'vote':None})
                #update failcnt none
                db.update('options',values={'failcnt':0},where='id='+str(abs(chat_id)))
            else:
                if failcnt>4:
                    await query.edit_message_text(text=_('pls_admin_enter_start_command'))
                    await Game.ended(chat_id,user_lang,_('game_ended_agents_win'))
                else:
                    #send message that mission team fail
                    await query.edit_message_text(text=_('mission_team_fail')+'\n'+str(failcnt+1)+' '+_('times_in_row')+'\n\n'+_('voters_confirmed')+' '+', '.join(Confirm)+'\n\n'+_('voters_against')+' '+', '.join(Against))
                    db.update('options',values={'failcnt':failcnt + 1},where='id='+str(abs(chat_id)))
                    await Game.nextround(chat_id,user_lang,InlineKeyboardMarkup,InlineKeyboardButton,False)
        else:
            await bot.answer_callback_query(query.id,text=_('you_r_voted')+'\n'+_('voted: ')+str(len(voted_players)),show_alert=True)
    elif command == 'successmission':
        vote = query.data.split(':')[1]
        round=db.get('game_'+str(abs(chat_id)),where='round>0')[0]['round']
        if Game.check_voters(chat_id,user_id,round):
            if Game.check_voter(chat_id,user_id):
                #opposition member always confirmed
                db.update('game_'+str(abs(chat_id)),values={'vote':1},where='id='+str(user_id))
            else:
                #agents vote
                db.update('game_'+str(abs(chat_id)),values={'vote':int(vote)},where='id='+str(user_id))
            
            #get user by id
            user = db.get_by_id('users',user_id)
            await query.message.reply_text(str(user['name'])+' '+_('voted'))

            voted_players=db.get('game_'+str(abs(chat_id)),where='vote NOT NULL')
            players=db.get('game_'+str(abs(chat_id)),where='round NOT NULL')
            allplayers=Game.get_players(chat_id)
            if len(voted_players)==len(players):
                Confirm=[]
                Against=[]
                for player in voted_players:
                    if player['vote']>0:
                        Confirm.append(player['name'])
                    else:
                        Against.append(player['name'])
               
                failcount=0
                round=options['round']
                if options['gov']>0:
                    gov=options['gov']
                else:
                    gov=0
                if options['opp']>0:
                    opp=options['opp']
                else:
                    opp=0
                if round == 4 and len(allplayers)>6:
                    failcount=1
                if len(Against)>failcount:
                    #Agents win round
                    gov=gov+1
                    db.update('options',values={'gov':gov},where='id='+str(abs(chat_id)))
                    await query.edit_message_text(text=_('all_voted')+'\n'+_('mission_failed'))
                else:
                    #Agents lose round
                    opp=opp+1
                    db.update('options',values={'opp':opp},where='id='+str(abs(chat_id)))
                    await query.edit_message_text(text=_('all_voted')+'\n'+_('mission_succeeded'))
                #send stat
                await query.message.reply_text(_('poll_stat')+'\n'+_('Against')+': '+str(len(Against))+'\n'+_('Confirm')+': '+str(len(Confirm))) 
                await query.message.reply_text(_('current_situation')+'\n'+_('round')+': '+str(round)+'\n'+_('gov')+': '+str(gov)+'\n'+_('opp')+': '+str(opp))
                db.update('game_'+str(abs(chat_id)),values={'vote':'NULL'})

                if opp==3:
                    if len(allplayers)>6:
                        #prosecutor chance to arrest Leader
                        msg=_('prosecutor_can_arrest_leader_opposition')
                        markup = Game.vote_prosecutor_button(chat_id,InlineKeyboardMarkup,InlineKeyboardButton)
                        await query.message.reply_text(text=msg, reply_markup=markup)
                    else:
                        await query.edit_message_text(text=_('pls_admin_enter_start_command'))
                        await Game.ended(chat_id,user_lang,_('game_ended_opposition_win'))
                elif gov==3:
                    await query.edit_message_text(text=_('pls_admin_enter_start_command'))
                    await Game.ended(chat_id,user_lang,_('game_ended_agents_win'))
                else:
                    await Game.nextround(chat_id,user_lang,InlineKeyboardMarkup,InlineKeyboardButton)
        else:
            #send message that you are not voters
            await bot.answer_callback_query(query.id,text=_('you_r_not_voters'),show_alert=True)
    elif command == 'arrest':
        arrest_id = query.data.split(':')[1]
        #get user by id from game table and get his role
        user = db.get('game_'+str(abs(chat_id)),where='id='+str(user_id))
        if user[0]['role']!='Prosecutor':
            #send notify than you not prosecutor
            await bot.answer_callback_query(query.id,text=_('you_not_prosecutor'),show_alert=True)
        else:
            arrest=db.get('game_'+str(abs(chat_id)),where='id='+str(arrest_id))
            query.edit_message_text(text=_('prosecutor_arrest')+'\n'+str(arrest[0]['name']))
            if arrest[0]['role']=='LeaderOpposition':
                #arrest leader opposition
                await query.edit_message_text(text=_('pls_admin_enter_start_command'))
                await Game.ended(chat_id,user_lang,_('game_ended_agents_win'))
            else:
                await query.edit_message_text(text=_('pls_admin_enter_start_command'))
                await Game.ended(chat_id,user_lang,_('game_ended_opposition_win'))
    else:
        await bot.answer_callback_query(query.id,text="Wrong callback",show_alert=True)
    
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
    
    #await update.message.reply_text(_('inline_q {chat_id}'))

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

    user_lang = update.effective_user.language_code
    _ = Game.get_lang(Game,user_lang)

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
            values = {'id': abs(chat.id), 'cause_name': cause_name, 'title': chat.title}
            db.set('chats', values)
            #send welcome messagge to all members of the group
            await context.bot.send_message(chat_id=chat.id,text=_ ('bot_intro_chat_message'))
        elif was_member and not is_member:
            logger.info("%s removed the bot from the group %s", cause_name, chat.title)
            db.del_by_id('chats', chat.id)
            db.droptable('game_'+str(abs(chat.id)))
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
    application.add_handler(CommandHandler("help", on_rules))
    application.add_handler(CommandHandler("rules", on_rules))

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