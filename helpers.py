from __future__ import print_function
import sys
import sqlite3
import datetime
from flask import Flask, redirect, render_template, request, url_for, send_file, session

# Get the URL with current parameters for any links to the overview page
def overview_url():
    url = '/overview'
    if request.args.get('datestart') != none and request.args.get('dateend') != none and request.args.get('durationstart') != none and request.args.get('durationend') != none:
        url = url + "?datestart=" + request.args.get('datestart') + "&dateend=" + request.args.get('dateend') + "&durationstart=" + request.args.get('durationstart') + "&durationend=" + request.args.get('durationend')
    return url 

# Get the URL with current parameters for any links to the public page
def public_url():
    url = '/public'
    if request.args.get('datestart') != none and request.args.get('dateend') != none and request.args.get('durationstart') != none and request.args.get('durationend') != none:
        url = url + "?datestart=" + request.args.get('datestart') + "&dateend=" + request.args.get('dateend') + "&durationstart=" + request.args.get('durationstart') + "&durationend=" + request.args.get('durationend')
    return url

# If there is no login yet, sets login to "cdc" and "cdc", otherwise finds out what the current login is 
def getCorrectLogin():
    con = sqlite3.connect("logs115.db")
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS login(username varchar primary key, pwd varchar)")
    cur.execute("SELECT COUNT(*) FROM login")
    result = cur.fetchall()
    numaccounts = result[0][0]
    # No current login, so set login to "cdc" and "cdc"
    if numaccounts == 0:
        cur.executemany("INSERT INTO login (username, pwd) VALUES (?, ?);", [('cdc', 'cdc')])
    # There is a current login, so find out what it is
    cur.execute("SELECT username FROM login LIMIT 1")
    usernames = cur.fetchall()
    username = usernames[0][0]
    cur.execute("SELECT pwd FROM login LIMIT 1")
    pwds = cur.fetchall()
    pwd = pwds[0][0]
    con.commit()
    con.close()
    return username, pwd

# Check if there are any date/duration arguments missing (datestart, dateend, durationstart, or durationend)
def argsMissing():
    return request.args.get('datestart') == None or request.args.get('dateend') == None or request.args.get('durationstart') == None or request.args.get('durationend') == None

# Check if there are any date arguments missing (datestart, dateend)
def timeArgsMissing():
    return request.args.get('datestart') == None or request.args.get('dateend') == None 

# Used when there are date/duration arguments missing. Returns the base URL with default time and duration arguments.
def redirectWithArgs(base):
    now_date = datetime.datetime.now()
    now_string = now_date.strftime("%Y-%m-%d")
    month_ago = now_date - datetime.timedelta(days = 30)
    monthago_string = month_ago.strftime("%Y-%m-%d")
    return base + '?datestart=' + monthago_string + '&dateend=' + now_string + '&durationstart=0&durationend=end'