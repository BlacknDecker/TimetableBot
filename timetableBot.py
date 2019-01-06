#! python3
import json
from telegram import (ReplyKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler)
import telegram
import time,datetime


### GET CONNECTION INFOS ###
with open('bot_info.json', 'r') as f:
    connection_data = json.load(f)


#Bot unifi:
# /orario -Oggi o -Domani
# /news   -> prese dal sito unifi (DA SVILUPPARE)

updater= Updater(token=connection_data["token"])  
dispatcher= updater.dispatcher
SELECT,CHOOSE = range(2)


###MATERIE#########################
QAS = '*Quantitative Analysis of Systems*'
CPS = '*Cyber Physical Systems*'
QC  = '*Quality and Certification*'
ANA = '*Advance Numerical Analysis*'
IoT = '*Distributed Programming for IoT*'

#####ORARIO########################
lunedi= '09:30-11:15'.ljust(15,'.')+CPS+'\n'+'11:30-13:00'.ljust(15,'.')+QAS+'\n'+'14:30-17:30'.ljust(15,'.')+IoT
martedi= '09:30-11:15'.ljust(15,'.')+CPS+' - ROOM 221'+'\n'+'11:30-13:00'.ljust(15,'.')+QAS+'\n'+'15:30-18:00'.ljust(15,'.')+QC
mercoledi= '9:00-10:30'.ljust(15,'.')+ANA+'\n'+'14:30-17:30'.ljust(15,'.')+IoT
giovedi= '10:30-13:00'.ljust(15,'.')+QAS+'\n'+'14:30-17:30'.ljust(15,'.')+CPS
venerdi= '10:45-13:15'.ljust(15,'.')+ANA+'\n'+'14:30-17:15'.ljust(15,'.')+QC
sabato= '*No Lectures!*'
domenica= '*No Lectures!*'

#####DAYS#########################
mon = 'Lun - Mon'
tue = 'Mar - Tue'
wed = 'Mer - Wed'
thu = 'Gio - Thu'
fri = 'Ven - Fri'

##################################

padding = 28
symb = '+'

timetable= { 
			 0:'Sun'.center(padding,symb)+'\n'+domenica,	
			 1:mon.center(padding,symb)+'\n'+lunedi,
			 2:tue.center(padding,symb)+'\n'+martedi,
			 3:wed.center(padding,symb)+'\n'+mercoledi,
			 4:thu.center(padding,symb)+'\n'+giovedi,
			 5:fri.center(padding,symb)+'\n'+venerdi,
			 6:'Sat'.center(padding,symb)+'\n'+sabato
			}

def getDayCode(day):	#caso di scelta automatica
	if day=='Oggi\nToday':
		return 0
	else:
		return 1

def setupDayCode(day):	#giorno scelto dall'utente
	if day == mon:
		return 1
	elif day == tue:
		return 2
	elif day == wed:
		return 3
	elif day == thu:
		return 4
	elif day == fri:
		return 5
	else:
		return 6


def getTimetable(oggi, richiesta):
	giorno= (int(oggi)+richiesta) % 7  #modulo 7 per ricominciare dal lunedì
	table=timetable[giorno]
	return table

#####FUNZIONI BOT#############################
def start(bot, update):
	user = update.message.from_user
	update.message.reply_text('Bot started!')


#>> Comando Orario
def orari(bot, update):
	#Creo una tastiera personalizzata:
	reply_keyboard = [['Oggi\nToday','Domani\nTomorrow'],['Select...']]
	update.message.reply_text('Select day:',	reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
	#return il codice dello stato successivo
	return SELECT



def switchMod(bot,update):
	if update.message.text == 'Select...' :
		return chooseDay(update)	#chiedo di selezionare il giorno
	else:
		return day(bot,update)		#se ho scelto oggi o domani posso già rispondere


def chooseDay(update):
	#Creo una tastiera personalizzata:
	reply_keyboard = [[mon,tue],[wed,thu],[fri]]
	update.message.reply_text('Select the day:', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
	#return il codice dello stato successivo
	return CHOOSE

def daychoosed(bot,update):
	request = setupDayCode(update.message.text)
	text= getTimetable(0,request)
	reply_markup= telegram.ReplyKeyboardRemove()
	update.message.reply_text(text, parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=reply_markup)
	return ConversationHandler.END


def day(bot, update):
	now= datetime.datetime.now()
	today= now.strftime('%w')
	request= getDayCode(update.message.text)
	text= getTimetable(today,request)
	reply_markup= telegram.ReplyKeyboardRemove()
	update.message.reply_text(text, parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=reply_markup)
	return ConversationHandler.END
#<<

def error(bot, update, error):


def cancel(bot,update):
	user = update.message.from_user
	reply_markup= telegram.ReplyKeyboardRemove()
	update.message.reply_text('Command aborted!',reply_markup= reply_markup)
	return ConversationHandler.END


def unknown(bot, update):
	user = update.message.from_user
	update.message.reply_text('Unknown command!\nPress /timetable to start!')



#Definisco gli handler
start_handler = CommandHandler('start', start)

timetable_handler = ConversationHandler(
		entry_points=[CommandHandler('timetable',orari)],
		
		states={
			SELECT: [MessageHandler(Filters.text, switchMod)],
			CHOOSE: [MessageHandler(Filters.text, daychoosed)]
				},

		fallbacks=[CommandHandler('cancel',cancel)]
		)

unknown_handler = MessageHandler(Filters.command, unknown)


#Aggiungo gli Handler al dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(timetable_handler)
dispatcher.add_error_handler(error)
dispatcher.add_handler(unknown_handler)

#Start the BOT
updater.start_polling()
