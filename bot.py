#!usr/bin/env python
#coding:utf8

import xml.etree.ElementTree as ET

from settings import YANDEX_API_KEY 
import logging
from datetime import datetime, date, timedelta
import json
import time
import re
import pandas as pd
from collections import OrderedDict
from settings import TOKEN
import requests
import uuid
from speech_to_text import speech_to_text
from speech import convert_to_pcm16b16000r


from telegram.ext import Updater,CommandHandler, MessageHandler, Filters, Job
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, User
logging.basicConfig(format = '%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

from botdb import db_session, Session
import re


def set_repeat(bot, update, args, job_queue, chat_data):
    chat_id = update.message.chat_id
    date_string = ' '.join(args[:2])
    first = datetime.strptime(date_string, '%Y/%m/%d %H:%M')
    print(first)
    interval = int(args[2])*24*60*60
    print(interval)
    print(type(interval))


    job = job_queue.run_repeating(alarm_repeat, interval, first, context=dict(chat_id=chat_id, args=args))
    chat_data['job'] = job

def alarm_repeat(bot, job):
    bot.send_message(job.context['chat_id'], text='Ты просил напомнить тебе: "{}"'.format(job.context['args'][-1]))


    
def set_once(bot, update, args, job_queue, chat_data):
    chat_id = update.message.chat_id
    date = update.message.date
    due_val = args[0]
    if due_val.isdigit():
        due = int(args[0])
    else:
        m = re.match(r'(\d+)(m|мин|s|сек|с|секунд|seconds)', due_val)
        if m:
            if m.group(2) in ['m', 'мин']:
                due = timedelta(minutes=int(m.group(1)))
            elif m.group(2) in ['s', 'сек', 'с', 'секунд', 'seconds']:
                due = timedelta(seconds=int(m.group(1)))
        else:
            if type(due_val) == type(''):
                date_string = ' '.join(args[0:2])
                due = int(time.mktime(datetime.strptime(date_string, '%Y/%m/%d %H:%M').timetuple())) - int(time.mktime(date.timetuple()))
                print(due)
    if due < 0:
        update.message.reply_text('Извини, я пока еще не умею менять прошлое')
        return


    job = job_queue.run_once(alarm_once, due, context=dict(chat_id=chat_id, args=args))
    update.message.reply_text('Ура! Таймер установлен')

#numbers_voice = {'одну': 1, 'две': 2, 'три':3, 'четыре':4, 'пять':5, 'шесть':6, 'семь':7, 'восемь':8,'девять': 9,'десять':10, 'пятнадцать':15, 'двадцать':20, 'тридцать':30, 'полчаса':'30 минут','час': '60 минут'}


def message_handler(bot, update, job_queue, chat_data):
    chat_id = update.message.chat_id
    date = update.message.date
    message = get_voice_message(bot, update)
    print(message) 
    m = re.match(r'([Нн]апомни(?:ть)?)(?: мне)? (.*)', message)
    m_unset = re.match(r'[Уу]дали(?:ть)?(?: вс[её])?', message)
    if m:
        print('first IF')
        tail = m.group(2)
        print('tail = {}'.format(tail))
        m1 = re.match(r'(сегодня|завтра|послезавтра) (.*)', tail)
        #'(' + 'slovo' + '|' + 'slovo2' + ')' = '(slovo|slovo2)' = '(' + '|'.join(['slovo', 'slovo2') + ')'
        m2 = re.match(r'(через|кажды[ей]) ([0-9]+)(?: секунд|минут[а-я]?)? (.*)', tail)
        if m1:
            when = m1.group(1)
            what = m1.group(2)
            if when == 'сегодня':
                due = date
            elif when == 'завтра':
                due = date + timedelta(days=1)
            elif when == 'послезавтра':
                due = date + timedelta(days=2)
            print(due)
            print('DUE')
            print(when)

            when = int(time.mktime(due.timetuple())) - int(time.mktime(date.timetuple()))
            print(when)
            job = job_queue.run_once(alarm_once, when, context=dict(chat_id=chat_id, args=[when, what]))
            chat_data['job'] = job
        elif m2:
            once = m2.group(1) == 'через'
            due = m2.group(2)
            what = m2.group(3)
            print(due, what)
            when = int(due)
            #when = int(due)*60
            if once:
                job = job_queue.run_once(alarm_once, when, context=dict(chat_id=chat_id, args=[when,what]))
                chat_data['job'] = job
            else:
                interval = int(when)
                first = date
                print ("YAHOO 2: ", interval, " ", first)
                job = job_queue.run_repeating(alarm_repeat, interval, first, context=dict(chat_id=chat_id, args=[when, what]))
                chat_data['job'] = job
    elif m_unset:
        unset(bot, update, chat_data)




def alarm_once(bot, job):
    print(job, 'YAHHOO')
    print(job.context['args'])
    #bot.send_message(job.context['chat_id'], text='Аларм')
    bot.send_message(job.context['chat_id'], text='Ты просил напомнить тебе: "{}"'.format(job.context['args'][-1]))

def unset(bot, update, chat_data):
    if 'job' not in chat_data:
        update.message.reply_text('У тебя нет установленных таймеров')
        return
    print("YAHOO 3")
    job = chat_data['job']
    job.schedule_removal()
    del chat_data['job']
    update.message.reply_text('Таймер удален')


def get_voice_message(bot, update):
    file_info = bot.get_file(update.message.voice.file_id)
    #file_response = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN, file_info.file_path))
    file_response = requests.get(file_info.file_path)
    uid = uuid.uuid4().hex
    data = convert_to_pcm16b16000r(in_bytes=file_response.content)
    response = requests.post('http://asr.yandex.net/asr_xml?uuid={}&key=e99621ac-66dc-45e6-981d-d24f92f2deea&topic=queries&lang=ru-RU'.format(uid), 
                        data=data, headers={'Content-Type': 'audio/x-pcm;bit=16;rate=16000'}
                        )
    print(str(response))
    print(len(file_response.content))
    #print(file_response.headers)
    #print(response.content)
    #print(file_response.content)
    
    if response.status_code == 200:
        response_text = response.text
        root = ET.fromstring(response_text)
        #print(root)
        #print(root.tag, root.attrib)
        result = ''
        for child in root:
            result = child.text
            return result #считаю, что самый вероятный результат - первый и его возвращаю
            print(result)


all_chat_info = {}


def set_task(bot, update, args):
    user_text = update.message.text
    task_name = ' '.join(args)
    print(task_name)
    user_id = update.message.from_user.id

    save_to_session(update, task=task_name)
    save_to_sessiondb(update, task = args[0])

    
def save_to_session(update, **kwargs):
    user_id = update.message.from_user.id
    chat_info = {
                'update_id': update.update_id,
                'chat_id' : update.message.chat_id, 
                #'message_id' : update.message.message_id,
                'user_name' : update.message.from_user.first_name,
                'task' : kwargs['task']
                #'date' : datetime.date(update.message.date)
            }

    if user_id not in all_chat_info:
        all_chat_info[user_id] = chat_info
    else:
        all_chat_info[user_id].update(chat_info)  
    return all_chat_info

def save_to_sessiondb(update, **kwargs):
    user_id = update.message.from_user.id
    update_id = update.update_id
    chat_id = update.message.chat_id
    print(chat_id)
    first_name = update.message.from_user.first_name
    user_session = db_session.query.filter(Session.user_id == user_id).first()
    print(user_session) 
    print(session)
    if not user_session: 
        print('NEW')
        user_session = Session(user_id=user_id, update_id=update_id, chat_id=chat_id, first_name=first_name, data=json.dumps(kwargs)) 
        db_session.add(user_session)
        db_session.commit()
    else:
        print('NOT NEW')
        user_session.data = json.dumps(kwargs)
        # db_session.execute(
        #     Session.__table__.update().where(
        #         Session.user_id == user_id
        #     ).values(
        #         user_id=user_id, update_id=update_id, chat_id=chat_id, first_name=first_name, data = json.dumps(kwargs)
        #     )
        # )
        db_session.commit()


def get_task(bot, update):
    user_id = update.message.from_user.id

    print(user_id)
    print(all_chat_info)
    print(all_chat_info.get(user_id, {}).get('task'))

    result = db_session.query(Session.data).filter(Session.user_id == user_id).first()
    task_data_str = result.data
    if task_data_str:
        task_data = json.loads(task_data_str)
        task = task_data.get('task')
        # task = db_session.execute(Session.query(Session.data).filter(Session.user_id == user.id))
        print(task)
    



def start_info(bot, update):
    print("Вызван /start")

    user_id = update.message.from_user.id

    chat_info = {
                'update_id': update.update_id,
                'chat_id' : update.message.chat_id, 
                #'message_id' : update.message.message_id,
                'user_name' : update.message.from_user.first_name,
                #'date' : datetime.date(update.message.date)
            }

    if user_id not in all_chat_info:
        all_chat_info[user_id] = chat_info
    else:
        all_chat_info[user_id].update(chat_info)

    print(chat_info)
    print(all_chat_info)
    text = "Я твой помощник. Ниже список моих команд: "
    update.message.reply_text('Привет, {}! {}'.format(chat_info['user_name'], text))

def echo_func(bot, update):
    print("Вызван echo")
    user_text = update.message.text
    print(user_text)
    update.message.reply_text(user_text)
    

commands = [
    ('start', dict(handler=start_info, descr='Start info')),
    ('echo', dict(handler=echo_func, descr='Echo command')),
    ('set_task', dict(handler=set_task, descr = 'set task', kwargs=dict(pass_args=True))),
    ('get_task', dict(handler=get_task, descr = 'get_task')),
    ('set_once', dict(handler=set_once, descr = 'set_once', kwargs=dict(pass_args=True, pass_job_queue=True, pass_chat_data=True))),
    ('unset', dict(handler=unset, descr='unset', kwargs=dict(pass_chat_data=True))),
    ('set_repeat', dict(handler=set_repeat, descr='set_repeat', kwargs=dict(pass_chat_data=True, pass_args=True, pass_job_queue=True)))
    ]



def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    for command_name, data in commands:
        dp.add_handler(CommandHandler(command_name, data['handler'], **data.get('kwargs', {})))    
    # dp.add_handler(CommandHandler("start", start_info))  # ручка для инструкций
    # dp.add_handler(CommandHandler("echo", echo_func))
    # dp.add_handler(CommandHandler("voice", get_voice_message))
    dp.add_handler(MessageHandler(Filters.voice, message_handler, pass_chat_data=True, pass_job_queue=True))
    dp.add_handler(MessageHandler(Filters.text, echo_func))
    updater.start_polling()
    updater.idle()







if __name__ == '__main__':
    main()
