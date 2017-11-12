from __future__ import print_function
import sys
import sqlite3
import datetime
from flask import Flask, redirect, render_template, request, url_for, send_file, session

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