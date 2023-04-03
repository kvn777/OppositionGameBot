#import python libs
import os
import gettext
import random
import telegram
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

    min_players = 2
    max_players = 15
    rolearray7=['GovernmentAgent','OppositionMember','OppositionMember','GovernmentAgent','OppositionMember','OppositionMember']
    rolearray10=['GovernmentAgent','OppositionMember','OppositionMember','GovernmentAgent','OppositionMember','OppositionLeader','Prosecutor','OppositionMember','OppositionMember']
    rolearray=['Provocateur','OppositionMember','OppositionMember','GovernmentAgent','OppositionMember','OppositionLeader','Prosecutor','OppositionMember','Bodyguard','SecretAgent','OppositionMember','OppositionMember','GovernmentAgent','OppositionMember','OppositionMember']

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
    
    def get_players(chat_id):
        #get members count from db
        chat_id = abs(chat_id)
        values = db.get('game_'+str(chat_id))
        return  values
    
    def is_game_started(chat_id):
        chat_id = abs(chat_id)
        values = db.get('game_'+str(chat_id),where='mc not null')
        if values:
            return  True
        else:
            return  False

    async def start_game_routines(self,chat_id,bot):
        #get members count from db
        chat_id = abs(chat_id)
        players = db.get('game_'+str(chat_id))
        players_count = len(players)

        random.shuffle(players)
        players_list = [list(player) for player in players]

        if players_count < 7:
            role_array=self.rolearray7
        elif players_count < 10:
            role_array=self.rolearray10
        else:
            role_array=self.rolearray

        message=''
        error=[]
        for i, user in enumerate(players):
            message=_('your_role: ')+role_array[i]+'\n\n';
            db.update('game_'+str(chat_id),values={'role':role_array[i],'mc':i+1},where='id='+str(user['id']))
            if players_count>9 and i==0:
                #provocateur
                message+=_('your_identity_and_OppositionLeader_known_Bodyguard_but')+'\n'
            if players_count==6:
                #prosecutor
                message+=_('your_mission_find_OppositionLeader_and_arrest')+'\n'
            if players_count==9:
                #secret agent
                message+=_('all_agents_known_OppositionLeader_but')+'\n'
                message+=_('your_mission_disrupt_3_meetings_sabotage_5_election')+'\n'
            leak = []
            if i == 0 or i == 3 or i == 6 or i == 12:
                #send to Agent name other Agents
                if 0 in range(len(players_list)):
                    leak.append(players[0]['name'])
                if 3 in range(len(players_list)):
                    leak.append(players[3]['name'])
                if 6 in range(len(players_list)):
                    leak.append(players[6]['name'])
                if 12 in range(len(players_list)):
                    leak.append(players[12]['name'])
                random.shuffle(leak)
                message+=_('agents_in_game: ')+', '.join(leak)+'\n\n'
                message+=_('your_mission_disrupt_3_meetings_sabotage_5_election')+'\n'
            if players_count > 6 and (i == 1 or i == 2 or i == 4 or i == 7 or i == 8 or i == 10 or i == 11 or i == 13 or i == 14):
                message+=_('you_are_OppositionMember_your_mission_but_OppositionLeader')+'\n'
            if players_count < 7 and (i == 1 or i == 2 or i == 4 or i == 5):
                message+=_('you_are_OppositionMember_your_mission')+'\n'
            leak = []
            if players_count > 6 and i == 5:
                #send to OppositionLeader name all Agents
                if 0 in range(len(players_list)):
                    leak.append(players[0]['name'])
                if 3 in range(len(players_list)):
                    leak.append(players[3]['name'])
                if 6 in range(len(players_list)):
                    leak.append(players[6]['name'])
                if 12 in range(len(players_list)):
                    leak.append(players[12]['name'])
                random.shuffle(leak)
                message+=_('agents_in_game: ')+', '.join(leak)+'\n\n'
                message+=_('your_mission_lead_and_not_be_arrested')+'\n'
            leak = []
            if i == 8:
                #send to bodyguard
                if 0 in range(len(players_list)):
                    leak.append(players[0]['name'])
                if 5 in range(len(players_list)):
                    leak.append(players[5]['name'])
                random.shuffle(leak)
                message+=_('Leader_and_Provocateur: ')+', '.join(leak)+'\n\n'
                message+=_('your_mission_protect_Leader_and_to_be_arrested')+'\n'
            try:
                await bot.send_message(chat_id=user['id'],text=message)
            except telegram.error.BadRequest:
                error.append(user['name'])
        if len(error)>0:
            await bot.send_message(chat_id='-'+str(chat_id),text=_('Cant_send_to: ')+', '.join(error)+'\n\n'+_('pls_start_message_with_bot_PM'))
            return False
        db.update('game_'+str(chat_id),values={'round':1})
        return True

    def players_buttons(chat_id,round,InlineKeyboardMarkup,InlineKeyboardButton):
        #get members count from db
        chat_id = abs(chat_id)
        players = db.get('game_'+str(chat_id))

        buttons0 = []
        buttons1 = []
        for i, user in enumerate(players):
            if i % 2 == 0:
                buttons0.append(InlineKeyboardButton(user['name'], callback_data="getmission:"+str(round)+":"+ str(user['id'])))
            else:
                buttons1.append(InlineKeyboardButton(user['name'], callback_data="getmission:"+str(round)+":"+ str(user['id'])))
        markup = InlineKeyboardMarkup([buttons0,buttons1])
        return  markup

    def check_mission_commander(chat_id,round):
        #get mission commander
        mc = db.get('game_'+str(abs(chat_id)),where='round='+str(round)+' and mc='+str(round))
        if mc:
            return True
        else:
            return False

    async def round_one(chat_id,bot,InlineKeyboardMarkup,InlineKeyboardButton):
        #get round one mission commander
        mc = db.get('game_'+str(abs(chat_id)),where='mc=1')
        message=_('mission_commander: ')+mc[0]['name']+'\n'+_('chose_players_next_meeting')
        markup = Game.players_buttons(chat_id,1,InlineKeyboardMarkup,InlineKeyboardButton)
        await bot.send_message(chat_id=chat_id,text=message, reply_markup=markup)
    
    def add_gamer(chat_id,user_id,name):
        chat_id = abs(chat_id)
        #check if user already join
        values = db.get('game_'+str(chat_id),where='id='+str(user_id))
        if values:
            return  False
        else:
            values = {'id': user_id, 'name': name}
            db.set('game_'+str(chat_id), values)
            return  True

    