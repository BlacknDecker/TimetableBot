#! python3
import json
from telegram import (ReplyKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler)
import telegram
import datetime as dt


### GET CONNECTION INFOS ###
def getConnectionData():
    with open('bot_info.json', 'r') as f:
        return json.load(f)


connection_data = getConnectionData()
updater = Updater(token=connection_data["token"])
dispatcher = updater.dispatcher
SELECT, CHOOSE = range(2)   # Conversation states


### GET TIMETABLE ###
def getRawTimetable():
    raw_timetable = []
    with open('timetable.json', 'r') as f:
        raw_timetable = json.load(f)
    return raw_timetable


def getLectureInfos(course_acr, lecture):
    lecture_infos = "{}-{}".format(lecture["start"], lecture['end']).ljust(15, '.')
    lecture_infos += "*{}* -> {}\n".format(course_acr, lecture["place"])
    return lecture_infos


def getDayHeader(day_str):
    return "{}".format(day_str).capitalize().center(28, '+') + "\n"


def createTimetable():
    raw_tt = getRawTimetable()
    if len(raw_tt) == 0: return {}  # In case of error
    raw_tt = raw_tt["courses"]
    # Setup timetable
    timetable = {
        "monday": [],
        "tuesday": [],
        "wednesday": [],
        "thursday": [],
        "friday": [],
        "saturday": [],
        "sunday": []
    }
    # Fill timetable
    for course in raw_tt:
        for lecture in course["timetable"]:
            timetable[lecture["day"]].append(
                getLectureInfos(course["acronym"], lecture))  # Add course string to that day
    # Sort lectures by time
    for day_lectures in timetable.values():
        if len(day_lectures) > 0:
            day_lectures.sort(key=lambda date_str: dt.datetime.strptime(date_str.split('.')[0].split('-')[0], "%H:%M"))     # Sort by the start hour
    # Join in a single string
    for day_str in timetable:
        timetable[day_str] = "".join(timetable[day_str])  # Join sorted day lectures
        if len(timetable[day_str]) > 0:
            timetable[day_str] = getDayHeader(day_str) + timetable[day_str]  # Add day header
    return timetable


##### DAYS CONVERSION #########################
days = [
    ('Dom - Sun', 'sunday'),
    ('Lun - Mon', 'monday'),
    ('Mar - Tue', 'tuesday'),
    ('Mer - Wed', 'wednesday'),
    ('Gio - Thu', 'thursday'),
    ('Ven - Fri', 'friday'),
    ('Sab - Sat', 'saturday')
]


def getDayCode(day_msg):
    count = 0
    for day in days:
        if day_msg in day:
            return count
        else:
            count += 1
    return -1   # In case of error


def getLecturesByDay(day_code):
    lects = timetable[days[day_code][1]]
    if len(lects) != 0:
        return lects
    else:
        return '*No Lectures!*'


#####FUNZIONI BOT#############################
def start(bot, update):
    user = update.message.from_user
    update.message.reply_text("Welcome!\n Press '/' to show the available commands!")


# >> Custom Commands
# TC 1 (Timetable Conversation)
def startTimetableConversation(bot, update):
    reply_keyboard = [['Oggi\nToday', 'Domani\nTomorrow'], ['Select...']]
    update.message.reply_text('Select day:', reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return SELECT   # Next state code


# TC 2
def switchMod(bot, update):
    if update.message.text == 'Select...':
        return chooseDay(update)  # ask to select the day
    else:
        return day(bot, update)  # reply to today or tomorrow request


# TC 2.1
def chooseDay(update):
    reply_keyboard = [[days[1][0], days[2][0]], [days[3][0], days[4][0]], [days[5][0]]]    # Days[0] == Sunday
    update.message.reply_text('Select the day:',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CHOOSE


# TC 2.2
def daychoosed(bot, update):
    day_code = getDayCode(update.message.text)
    text = getLecturesByDay(day_code)
    reply_markup = telegram.ReplyKeyboardRemove()
    update.message.reply_text(text, parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=reply_markup)
    return ConversationHandler.END


# TC 3
def day(bot, update):
    if "Oggi" in update.message.text:
        day_code = int(dt.datetime.now().strftime('%w'))
    else:
        day_code = int(dt.datetime.now().strftime('%w'))
        day_code = (day_code + 1) % 7
    text = getLecturesByDay(day_code)
    reply_markup = telegram.ReplyKeyboardRemove()
    update.message.reply_text(text, parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=reply_markup)
    return ConversationHandler.END


# AC (Acronym command)
def showAcronyms(bot, update):
    user = update.message.from_user
    # Collect acronyms
    raw_infos = getRawTimetable()
    courses = raw_infos["courses"]
    acronyms = []
    for course in courses:
        acr = "*{}*".center(6, ' ').format(course["acronym"])
        acr += " - {}\n".format(course["name"])
        acronyms.append(acr)
    acronyms.sort()
    text = "Courses Acronyms:\n{}".format("".join(acronyms))
    reply_markup = telegram.ReplyKeyboardRemove()
    update.message.reply_text(text, parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=reply_markup)

# <<


def error(bot, update, error):
    pass


def cancel(bot, update):
    user = update.message.from_user
    reply_markup = telegram.ReplyKeyboardRemove()
    update.message.reply_text('Command aborted!', reply_markup=reply_markup)
    return ConversationHandler.END


def unknown(bot, update):
    user = update.message.from_user
    update.message.reply_text('Unknown command!\nPress /timetable to start!')


# Definisco gli handler
start_handler = CommandHandler('start', start)

timetable_handler = ConversationHandler(
    entry_points=[CommandHandler('timetable', startTimetableConversation)],

    states={
        SELECT: [MessageHandler(Filters.text, switchMod)],
        CHOOSE: [MessageHandler(Filters.text, daychoosed)]
    },

    fallbacks=[CommandHandler('cancel', cancel)]
)

acronyms_handler = CommandHandler('acronyms', showAcronyms)

unknown_handler = MessageHandler(Filters.command, unknown)

# Aggiungo gli Handler al dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(timetable_handler)
dispatcher.add_handler(acronyms_handler)
dispatcher.add_error_handler(error)
dispatcher.add_handler(unknown_handler)

# Start the BOT
timetable = createTimetable()
updater.start_polling()
print("Timetable Bot Started!")
