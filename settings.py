from __future__ import print_function
import sys
import sqlite3
import datetime
import json
from flask import Flask, redirect, render_template, request, url_for, send_file, session

#hc_diseases = ['diarrhea', 'fever', 'flaccid', 'respiratory', 'dengue', 'meningitis', 'jaundice', 'diphteria', 'rabies', 'neonatal']
#hc_var_names = ['var_dairrhea_case', 'var_dairrhea_death', 'var_fever_case', 'var_fever_death', 'var_flaccid_case', 'var_flaccid_death', 'var_respiratory_case', 'var_respiratory_death', 'var_dengue_case', 'var_dengue_death', 'var_meningetis_case', 'var_meningitis_death', 'var_juandice_case', 'var_juandice_death', 'var_diphteria_case', 'var_diphteria_death', 'var_rabies_case', 'var_rabies_death', 'va_neonatal_case', 'var_neonatal_death']

# If there is no login yet, sets login to "cdc" and "cdc", otherwise finds out what the current login is 


def getCorrectLogin():
    with open('login.json') as infile:
        login = json.load(infile)
        if login['username'] == None or login['pwd'] == None:
            return 'cdc', 'cdc'
        else:
            return login['username'], login['pwd']

def editLogin(username, pwd):
    with open('login.json', 'w') as outfile:
        json.dump({'username':username, 'pwd':pwd}, outfile)

# Check if there are any date/duration arguments missing (datestart, dateend, durationstart, or durationend)
def argsMissing():
    return timeArgsMissing() or request.args.get('durationstart') == None or request.args.get('durationend') == None

# Check if there are any date arguments missing (datestart, dateend)
def timeArgsMissing():
    # Check that date arguments are there
    if request.args.get('datestart') == None or request.args.get('dateend') == None:
        return True
    # Check that date arguments are in proper format
    try:
        temp = datetime.datetime.strptime(request.args.get('datestart'), '%Y-%m-%d')
        temp = datetime.datetime.strptime(request.args.get('dateend'), '%Y-%m-%d')
    except:
        return True
    return False

# Used when there are date/duration arguments missing. Returns the base URL with default time and duration arguments.
def redirectWithArgs(base):
    now_date = datetime.datetime.now()
    beginning = datetime.datetime(year=now_date.year-1, month=1, day=1)
    end = datetime.datetime(year=now_date.year-1, month=12, day=31)
    beginning_string = beginning.strftime("%Y-%m-%d")
    end_string = end.strftime("%Y-%m-%d")
    return base + '?datestart=' + beginning_string + '&dateend=' + end_string + '&durationstart=0&durationend=end'

# Used to set which diseases are currently available: which public and HC diseases are options, as well as which ones are currently selected to be viewed
def setDiseases(all_public, chosen_public, all_hc, chosen_hc):
    vars = ['all_public', 'chosen_public', 'all_hc', 'chosen_hc']
    with open('settings.json', 'w') as outfile:
        json.dump({'all_public':all_public, 'chosen_public':chosen_public, 'all_hc':all_hc, 'chosen_hc':chosen_hc}, outfile)
    return getDiseases()

# Get which diseases are options and which are selected (HC and public)
def getDiseases():
    with open('settings.json') as infile:
        settings  = json.load(infile)
        return [str(disease) for disease in settings['all_public']], [str(disease) for disease in settings['chosen_public']], [str(disease) for disease in settings['all_hc']], [str(disease) for disease in settings['chosen_hc']]

# Capitalize a string -- used as Jinja environment filter
def capitalize(s):
    return str.title(s)

def dtoi(date):
    return ''.join(date.split('-'))


