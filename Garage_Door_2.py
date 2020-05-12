import RPi.GPIO as GPIO
from datetime import datetime
import configparser
import smtplib
import imaplib
import ssl
import email
import time
import re

def send_response(message):
    # Create a secure SSL context
    context = ssl.create_default_context()

    # Read config
    config = configparser.ConfigParser()
    config.read('config.ini')
    SMTP_config = config['SMTP']

    # Try to log in to server and send email
    try:
        server = smtplib.SMTP_SSL(SMTP_config['host'], int(SMTP_config['port']), context = context)
        server.login(SMTP_config['user'], SMTP_config['password'])
        server.sendmail(SMTP_config['user'], SMTP_config['to'], message)
        server.quit()
    except Exception as e:
        raise (e)

# Create secure ssl context
context = ssl.create_default_context()

# Read config
config = configparser.ConfigParser()
config.read('config.ini')
IMAP_config = config['IMAP']

# Last UID for comparison
last_uid = ''

# Try to connect
server = imaplib.IMAP4_SSL(IMAP_config['host'], int(IMAP_config['port']))
server.login(IMAP_config['user'], IMAP_config['password'])

# Read emails
while True:
    try:
        server.select(IMAP_config['inbox'], readonly = True)
        current_date = datetime.date(datetime.now())
        result, all_uid = server.search(None, 'SINCE', current_date.strftime('%d-%b-%Y'))
        print('Result: {}'.format(result))
        print('UIDs for today: {}'.format(all_uid))
        if result == 'OK':
            pass
        else:
            send_message('Search failed.')
            time.sleep(30)
        if all_uid[0].decode('utf-8') == '' or last_uid == all_uid[0].decode('utf-8').split()[-1]:
            print('Waiting for new email.')
            time.sleep(30)
        else:
            if len(all_uid[0]) == 1:
                last_uid = all_uid[0].decode('utf-8')
                print('last uid: {}'.format(last_uid))
            else:
                last_uid = all_uid[0].decode('utf-8').split()[-1]
                print('last uid: {}'.format(last_uid))
            result, msg_data = server.fetch(last_uid, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            if msg['From'] == '5615420627@mms.att.net':
                for part in msg.walk():
                    try:
                        email_body = part.get_payload(decode = True).decode('utf-8')
                    except:
                        pass
                if not email_body:
                    pass
                else:
                    get_command = re.search('<td>((.|\n)*?)</td>', email_body)
                    command = ' '.join(get_command.group(1).split())
                    if command.lower() == 'garage':
                        print('Program successful.')
                        print(command)
                        GPIO.setmode(GPIO.BCM)
                        GPIO.setup(23, GPIO.OUT)
                        GPIO.setup(24, GPIO.OUT)
                        try:
                            GPIO.output(23, 1)
                            time.sleep(0.5)
                            GPIO.output(23, 0)
                            GPIO.output(24, 1)
                            time.sleep(0.5)
                            GPIO.output(24, 0)
                        except:
                            GPIO.cleanup()
                    else:
                        send_message('Invalid command.')
                        time.sleep(30)
            else:
                send_message('Not a valid request.')
                time.sleep(30)
                continue
    except Exception as e:
        print(e)