from __future__ import print_function
import sys
import sqlite3
import datetime
import json
from flask import Flask, redirect, render_template, request, url_for, send_file, session
from passlib.hash import pbkdf2_sha256

# If there is no login yet, sets login to "cdc" and "cdc", otherwise finds out what the current login is 
def getCorrectLogin():
    with open('login.json') as infile:
        login = json.load(infile)
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

def years():
    years = []
    now = datetime.datetime.now()
    for year in range (2016, now.year + 1):
        years = [year] + years
    return years

def getCharts():
    _, public_diseases, _, hc_diseases = getDiseases()
    charts = [
        ("hotlinebreakdown", "Breakdown of calls to entire hotline (HC workers vs. Public)", "pie"),
        ("publicbreakdown", "Breakdown of calls to public hotline", "pie"),
        ("overview", "Calls to entire hotline by day", "line"),
        ("public", "Calls to public hotline by day", "line")
    ]
    for disease in public_diseases:
        charts.append((disease, "Calls to " + disease.title() + " menu by day", "line"))
    charts = charts + [
        ("publicreports", "Public reports by day", "line"),
        ("moreinfo", "Calls requesting more information by day", "line"),
        ("ambulance", "Calls requesting ambulance information by day", "line")
    ]
    return charts


