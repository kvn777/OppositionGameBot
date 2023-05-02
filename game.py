#import python libs
import os
import gettext
import random
import telegram
from dotenv import load_dotenv
#my imports
from db import Database
load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
# create database object
db = Database(os.getenv("db_file"))
API_KEY = os.getenv("API_KEY")

languages = os.getenv('LANGUAGES').split(',')

translation_ = gettext.translation('messages', localedir=current_dir+'/lang', languages=languages, fallback=False)
translation={}
translation['ru'] = gettext.translation(domain='messages', localedir=current_dir+'/lang', languages=['ru'])
translation['en'] = gettext.translation(domain='messages', localedir=current_dir+'/lang', languages=['en'])
#translation['es'] = gettext.translation(domain='messages', localedir=current_dir+'/lang', languages=['es'])
_ = translation_.gettext

# Create a bot object
bot = telegram.Bot(token=API_KEY)

class Game:

    min_players = 5
    max_players = 15
    rolearray7=['GovernmentAgent','OppositionMember','OppositionMember','GovernmentAgent','OppositionMember','OppositionMember']
    rolearray10=['GovernmentAgent','OppositionMember','OppositionMember','GovernmentAgent','OppositionMember','OppositionLeader','Prosecutor','OppositionMember','OppositionMember']
    rolearray=['Provocateur','OppositionMember','OppositionMember','GovernmentAgent','OppositionMember','OppositionLeader','Prosecutor','OppositionMember','Bodyguard','SecretAgent','OppositionMember','OppositionMember','GovernmentAgent','OppositionMember','OppositionMember']
    _('GovernmentAgent')
    _('OppositionMember')
    _('OppositionLeader')
    _('Prosecutor')
    _('Bodyguard')
    _('SecretAgent')

    def get_lang(self,lang):
        self._=translation[lang].gettext
        return translation[lang].gettext

    def __init__(self, db):
        self.db = db
       

    def join_game_button(lang,InlineKeyboardMarkup,InlineKeyboardButton):
        _=translation[lang].gettext
        msg = _('join_game_button_message')
        keyboard =[
                [
                    InlineKeyboardButton(_("join_game_button_text"), callback_data="game:join"),
                ]
            ]
        markup = InlineKeyboardMarkup(keyboard)
        return  msg, markup

    def start_game_button(lang,InlineKeyboardMarkup,InlineKeyboardButton):
        _=translation[lang].gettext
        msg = _('start_game_button_message')
        keyboard =[
                [
                    InlineKeyboardButton(_("start_game_button_text"), callback_data="game:start"),
                ]
            ]
        markup = InlineKeyboardMarkup(keyboard)
        return  msg, markup
    
    def vote_meeting_team_button(lang,InlineKeyboardMarkup,InlineKeyboardButton):
        _=translation[lang].gettext
        msg = _('vote_meeting_team')
        keyboard =[
                [
                    InlineKeyboardButton(_("Confirm"), callback_data="currentmission:1"),
                    InlineKeyboardButton(_("Against"), callback_data="currentmission:0"),
                ]
            ]
        markup = InlineKeyboardMarkup(keyboard)
        return  msg,markup

    def vote_meeting_button(lang,InlineKeyboardMarkup,InlineKeyboardButton):
        _=translation[lang].gettext
        msg = _('vote_meeting_message')
        keyboard =[
                [
                    InlineKeyboardButton(_("Confirm"), callback_data="successmission:1"),
                    InlineKeyboardButton(_("Against"), callback_data="successmission:0"),
                ]
            ]
        markup = InlineKeyboardMarkup(keyboard)
        return  msg,markup

    def vote_prosecutor_button(chat_id,InlineKeyboardMarkup,InlineKeyboardButton):
        #get members count from db
        chat_id = abs(chat_id)
        players = db.get('game_'+str(chat_id))

        buttons0 = []
        buttons1 = []
        for i, user in enumerate(players):
            if i % 2 == 0:
                buttons0.append(InlineKeyboardButton(user['name'], callback_data="arrest:"+ str(user['id'])))
            else:
                buttons1.append(InlineKeyboardButton(user['name'], callback_data="arrest:"+ str(user['id'])))
        markup = InlineKeyboardMarkup([buttons0,buttons1])
        return  markup


    def get_players(chat_id):
        #get members count from db
        chat_id = abs(chat_id)
        try:
            values = db.get('game_'+str(chat_id))
        except:
            values = []
        return  values
    
    def is_game_started(chat_id):
        chat_id = abs(chat_id)
        values = db.get('mc_'+str(chat_id))
        if values:
            return  True
        else:
            return  False

    async def start_game_routines(self,chat_id,bot,lang):
        _=translation[lang].gettext
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
        #generate mc queue
        for i, user in enumerate(players): db.set('mc_'+str(chat_id),values={'user_id':user['id']})
        for i, user in enumerate(players): db.set('mc_'+str(chat_id),values={'user_id':user['id']})
        for i, user in enumerate(players): db.set('mc_'+str(chat_id),values={'user_id':user['id']})
        for i, user in enumerate(players): db.set('mc_'+str(chat_id),values={'user_id':user['id']})
        for i, user in enumerate(players): db.set('mc_'+str(chat_id),values={'user_id':user['id']})
        for i, user in enumerate(players):
            message=_('your_role: ')+_(role_array[i])+'\n\n';
            db.update('game_'+str(chat_id),values={'role':role_array[i]},where='id='+str(user['id']))
            if players_count>9 and i==0:
                #provocateur
                message+=_('your_identity_and_OppositionLeader_known_Bodyguard_but')+'\n'
            if i==6:
                #prosecutor
                message+=_('your_mission_find_OppositionLeader_and_arrest')+'\n'
            if i==9:
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
            #return False
        db.update('game_'+str(chat_id),values={'round':None,'vote':None})
        db.update('options',values={'round':1,'failcnt':0,'gov':0,'opp':0},where='id='+str(chat_id))
        return True

    def players_buttons(chat_id,round,InlineKeyboardMarkup,InlineKeyboardButton,where='1=1'):
        #get members count from db
        chat_id = abs(chat_id)
        players = db.get('game_'+str(chat_id),where=where)

        buttons0 = []
        buttons1 = []
        for i, user in enumerate(players):
            if i % 2 == 0:
                buttons0.append(InlineKeyboardButton(user['name'], callback_data="getmission:"+str(round)+":"+ str(user['id'])))
            else:
                buttons1.append(InlineKeyboardButton(user['name'], callback_data="getmission:"+str(round)+":"+ str(user['id'])))
        markup = InlineKeyboardMarkup([buttons0,buttons1])
        return  markup

    def check_mission_commander(chat_id,user_id,round):
        #get mission commander
        mc = db.get('mc_'+str(abs(chat_id)),where='id='+str(round)+' and user_id='+str(user_id))
        if len(mc)>0:
            return True
        else:
            return False

    def check_pm_user(user_id):
        #get mission commander
        mc = db.get('users',where='id='+str(user_id))
        if len(mc)>0:
            return True
        else:
            return False

    def check_voters(chat_id,user_id,round):
        #get mission commander
        mc = db.get('game_'+str(abs(chat_id)),where='id='+str(user_id)+' and round='+str(round))
        if mc:
            return True
        else:
            return False

    def check_voter(chat_id,user_id):
        chat_id = abs(chat_id)
        voter = db.get('game_'+str(chat_id),where='id='+str(user_id))
        index = Game.rolearray.index(voter[0]['role'])
        indexes = [1, 2, 4, 5, 7, 8, 10, 11, 13, 14]
        if index in indexes:
            return True
        else:
            return False

    def get_round_count_players(chat_id,round):
        #get round value from db
        round=int(round)
        chat_id = abs(chat_id)
        players = db.get('game_'+str(chat_id))
        count = len(players)
        if count < 6:
            actions = {1:2, 2:3, 3:2, 4:3, 5:3}
        elif count == 6:
            actions = {1:3, 2:3, 3:4, 4:3, 5:4}
        elif count ==7:
            actions = {1:3, 2:3, 3:3, 4:4, 5:4}
        else:
            actions = {1:3, 2:4, 3:4, 4:5, 5:5}
        return actions[round]

    def get_now_count_players(chat_id,round):
        #get round value from db
        chat_id = abs(chat_id)
        players = db.get('game_'+str(chat_id),where='round='+str(round))
        return len(players)

    async def round_one(chat_id,bot,lang,InlineKeyboardMarkup,InlineKeyboardButton):
        _=translation[lang].gettext
        #get round one mission commander
        mc = db.get('mc_'+str(abs(chat_id)),where='id=1')
        user=db.get('users',where='id='+str(mc[0]['user_id']))
        await bot.send_message(chat_id=chat_id,text=_('mission_commander: ')+user[0]['name'])
        message=_('chose_players_next_meeting')
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

    async def ended(chat_id,lang,message):
        _=translation[lang].gettext
        chat_id = abs(chat_id)
        players = db.get('game_'+str(chat_id))
        
        indexes = [1, 2, 4, 5, 7, 8, 10, 11, 13, 14]
        leak = []
        for i, player in enumerate(players):
            index = Game.rolearray.index(player['role'])
            if index not in indexes:
                leak.append(player['name'])
        await bot.send_message(chat_id='-'+str(chat_id),text=message+'\n\n'+_('list_of_players: ')+', '.join(leak))
        db.droptable('game_'+str(chat_id))
        db.droptable('mc_'+str(chat_id))

    async def nextround(chat_id,lang,InlineKeyboardMarkup,InlineKeyboardButton,next=True):
        _=translation[lang].gettext
        round = db.get('game_'+str(abs(chat_id)),where='round is not null')[0]['round']
        round = round+1
        round_real = db.get('options',where='id='+str(abs(chat_id)))[0]['round']
        if next:
            round_real=round_real+1
            db.update('options',values={'round':round_real},where='id='+str(abs(chat_id)))
        #get next mc
        mc = db.get('mc_'+str(abs(chat_id)),where='id='+str(round))
        user=db.get('users',where='id='+str(mc[0]['user_id']))
        await bot.send_message(chat_id=chat_id,text=_('round: ')+str(round_real)+'\n'+_('mission_commander: ')+user[0]['name'])
        message=_('chose_players_next_meeting')
        markup = Game.players_buttons(chat_id,round,InlineKeyboardMarkup,InlineKeyboardButton)
        await bot.send_message(chat_id=chat_id,text=message, reply_markup=markup)
        db.update('game_'+str(abs(chat_id)),values={'round':None,'vote':None})
