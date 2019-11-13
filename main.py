from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import time
import playsound
import speech_recognition as sr
import pyttsx3
## to get current UTC time
import pytz
## to open other application
import subprocess

##global section
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

CAL_STRS = ["do i have any plans","am i busy","what plans do i have","what am i doing","is my schedule occupied on","am i free","can i book","can i plan"]
NOTE_STRS = ["make a note","note down","keep a note"]
#START_UP = ["startup buddy","hey buddy","hey bot"]
START_UP = "hey buddy"

DAYS = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
DAYS_EXTRAS = ["st","rd","th","nd"]
MONTHS = ["january","february","march","april","may","june","july","august","september","october","november","december"]


def talk(msg):
    engine = pyttsx3.init()
    engine.say(msg)
    engine.runAndWait()

def audio_from_user():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        au = r.listen(source)
        said = ""

        try:
            said = r.recognize_google(au)
            print(said)
        except Exception as e:
            print("Exception: "+str(e))
    return said.lower()



def auth_user():
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

def get_events(day,service):
    # Call the Calendar API
    date = datetime.datetime.combine(day,datetime.datetime.min.time())
    end_date = datetime.datetime.combine(day,datetime.datetime.max.time())

    current_utc = pytz.UTC

    ### current into current utc format
    date = date.astimezone(current_utc)
    end_date = end_date.astimezone(current_utc)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    #print('Getting the upcoming '+str(n) + 'events')
    events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(),timeMax=end_date.isoformat(),singleEvents=True,orderBy='startTime').execute()
    events = events_result.get('items', [])

    ## print 10 upcoming events
    if not events:
        talk('No upcoming events found.')
    for event in events:
        talk("You have "+str(len(events))+" event on this day")
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])
        time_start_hr = start.split("T")[1].split("+")[0]
        time_end_hr = start.split("T")[1].split("+")[1]

        if int(time_start_hr.split(":")[0]) < 12:
            time_start_hr = time_start_hr + "am"
        else:
            time_start_hr = str(int(time_start_hr.split(":")[0])-12) + time_start_hr.split(":")[1]
            time_start_hr = time_start_hr + "pm"

        talk(event['summary'] + ' starts at ' + time_start_hr)

def note(text):
    current_date = datetime.datetime.now()
    new_file_name = str(current_date).replace(":","_") + "-note.txt"
    with open(new_file_name,"w") as f:
        f.write(text)
    subprocess.Popen(['notepad.exe',new_file_name])

def get_date(text):
    text = text.lower()
    today = datetime.date.today()

    if text.count("today") > 0:
        return today

    day = -1
    day_of_week = -1
    month = -1
    year = today.year

    for d in text.split():
        if d in MONTHS:
            month = MONTHS.index(d) + 1
#            print(month)
        elif d in DAYS:
            day_of_week = DAYS.index(d)
            print(day_of_week)
        elif d.isdigit():
            day = int(d)
#            print(day)
        else:
            for ext in DAYS_EXTRAS:
                found = d.find(ext)
                if found > 0:
                    #print("found")
                    try:
                        day = int(d[:found])
#                        print(day)
                    except:
                        pass

    ### if month in the provided text is already passed hence user is talking about the month occurence in next year
    if month < today.month and month!=-1:
        year = year + 1

    if day < today.day and month == -1 and day!= -1:
        month = month + 1

    ### if only week day is mentioned, complicate part
    if month==-1 and day == -1 and day_of_week!=-1:
        current_day_of_week = today.weekday()
        diff = day_of_week - current_day_of_week

        if diff < 0: ###talking about next week 7 - diff
            diff = diff + 7

        else:
            day = today.day + diff
        if text.count("next") >= 1:
            diff = diff + 7
        return today + datetime.timedelta(diff)

    ## default
    if day == -1 or month == -1:
        return None

    return datetime.date(month=month,day=day,year=year)


service = auth_user()
print('START NOW')
flag = 0
while True:
    print("i am available")

    text = "hey buddy"

    if text.count(START_UP) > 0:
        talk("ready")
        text = audio_from_user()

        for statement in CAL_STRS:
            if statement in text:
                date = get_date(text)
                if date:
                    get_events(date, service)
                else:
                    talk('I was not able to catch up')
        # text = "make a note"
        for statement in NOTE_STRS:
            if statement in text:
                talk("Speak what you wanna me to take a note of ?")
                # note_text = audio_from_user().lower()
                note_text = audio_from_user()
                note(note_text)
                talk("hey i have noted that, continue with the interaction")
