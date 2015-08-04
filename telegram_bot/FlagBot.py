#########################################################################
##
## FlagBot - Bot to move a (physical) flag with a servo
##
#########################################################################

import ConfigParser
import os
import re, string
import time as t
from twx.botapi import TelegramBot, ReplyKeyboardMarkup, InputFile, InputFileInfo

from SerialInterface import SerialInterface

import platform

import pygame
import pygame.camera

__author__ = 'def'

### Basic bot things ####################################
def load_last_id():
    if not os.path.isfile('id'):
        save_last_id(0)
        return 0

    with open('id', 'r') as f:
        return int(f.readline())

def save_last_id(last_id):
    with open('id', 'w') as f:
        f.write(str(last_id))

def save_log(id, update_id, chat_id, text):
    with open('log.txt', 'a') as f:
        f.write(str((id, update_id, chat_id, text))+'\n')

### Init configs #########################################
arduino = None

pygame.camera.init()
pygame.mixer.init()
#pygame.camera.list_camera() #Camera detected or not
cam = pygame.camera.Camera("/dev/video0",(1280,1024))
    
### JukeBot things #######################################
def send_keyboard(bot, user_id):
    keyboard_layout = [['/flag'], ['/rainbow'], ['/foto'] ]
    reply_markup = ReplyKeyboardMarkup.create(keyboard_layout)
    bot.send_message(user_id, 'This is the almighty FlagBot for Euskal Encounter 23!\nWelcome, mortal', reply_markup=reply_markup)

def main():
    print '[+] Starting bot...'

    # Read the config file
    print '[+] Reading config file...'
    config = ConfigParser.ConfigParser()
    config.read([os.path.expanduser('./config')])

    # Read data
    bot_name = config.get('bot', 'name')
    bot_token = config.get('bot', 'token')
    user_id = config.get('user', 'allowed')

    # Last mssg id:
    last_id = int(load_last_id())
    print '[+] Last id: %d' % last_id

    # Configure regex
    regex = re.compile('[%s]' % re.escape(string.punctuation))

    # Create bot
    print '[+] Connecting bot...'
    bot = TelegramBot(bot_token)
    bot.update_bot_info().wait()

    print '\tBot connected! Bot name: %s' % bot.username

    # Connect to hardware
    interface = SerialInterface()
    if platform.system() == 'Windows' : 
        interface.connect('COM5', 19200)
    else:
        interface.connect('/dev/ttyUSB0', 19200)        

    # Send special keyboard:
    send_keyboard(bot, user_id)

    print bot

    while True:
        try:
            updates = bot.get_updates(offset=last_id).wait()
            #print updates[0].message.sender
            #print "-------------------------------"

            for update in updates:
                id = update.message.message_id
                update_id = update.update_id
                user = update.message.sender

                chat_id = update.message.chat.id
                text = update.message.text

                if int(update_id) > last_id:
                    last_id = update_id
                    save_last_id(last_id)
                    save_log(id, update_id, chat_id, text)

                    #text = regex.sub('', text)
                    if text:
                        words = text.split()

                        for i, word in enumerate(words):
                            # Process commands:
                            if word == '/start':
                                print "New user started the app: " + str(user)
                                send_keyboard(bot, chat_id)
                            elif word == '/flag':
                                interface.sendFlagWave(1)
                                if update.message.sender == 'None' :
                                    bot.send_message(chat_id, "Moviendo la bandera " + update.message.sender.first_name + "!")
                                else:
                                    bot.send_message(chat_id, "Moviendo la bandera " + update.message.sender.username + "!")
                                break
                            elif word == '/rainbow':
                                interface.sendRainbow()
                                break
                            elif word == '/foto':
                                #interface.sendFlagWave(1)
                                t.sleep(2) #1 sec for posing
                                cam.start()
                                bot.send_message(chat_id, update.message.sender.first_name + " quiere una foto!")
                                img = cam.get_image()
                                pygame.image.save(img,"./snap_photo.jpg")
                                pygame.mixer.music.load("./camera_shutter.mp3")
                                pygame.mixer.music.play()

                                fp = open('snap_photo.jpg', 'rb')
                                file_info = InputFileInfo('snap_photo.jpg', fp, 'image/jpg')

                                f = InputFile('photo', file_info)

                                bot.send_photo(chat_id, photo=f)

                                cam.stop()
                                try:
                                    print "Foto enviada de " + update.message.sender.first_name + " " + update.message.sender.last_name + ", " + update.message.sender.username  + "!"
                                except Exception, e:
                                    print "User have no name: "
                                    print e
                                break
                            else:
                                bot.send_message(chat_id, "Bad syntax!")
                                break

                            # Restricted API
                            if int(user_id) == user.id:
                                if word == '/move':
                                    try:
                                        interface.sendMove(int(words[i+1]))
                                        break
                                    except Exception, e:
                                        print e


        except (KeyboardInterrupt, SystemExit):
            print '\nkeyboardinterrupt caught (again)'
            print '\n...Program Stopped Manually!'
            raise

if __name__  == '__main__':
    main()
