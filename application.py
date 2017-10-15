from __future__ import print_function
import os
import csv
import sqlite3
import datetime
from flask import Flask, redirect, render_template, request, url_for, send_file, session
import sys
from fpdf import FPDF
from PIL import Image
import reportlab
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics  
from reportlab.pdfbase.ttfonts import TTFont   
from pyPdf import PdfFileWriter, PdfFileReader
from werkzeug import secure_filename
from threading import Thread
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
import smtplib
import helpers
import html
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import numpy as np


#App configurations--set folders and allowed extensions for file uploads
app = Flask(__name__)

# Helper functions used in all pages for dynamically generating URLs for Overview and Public pages
def overview_url():
    url = '/overview'
    if request.args.get('datestart') != none and request.args.get('dateend') != none and request.args.get('durationstart') != none and request.args.get('durationend') != none:
        url = url + "?datestart=" + request.args.get('datestart') + "&dateend=" + request.args.get('dateend') + "&durationstart=" + request.args.get('durationstart') + "&durationend=" + request.args.get('durationend')
    return url 

def public_url():
    url = '/public'
    if request.args.get('datestart') != none and request.args.get('dateend') != none and request.args.get('durationstart') != none and request.args.get('durationend') != none:
        url = url + "?datestart=" + request.args.get('datestart') + "&dateend=" + request.args.get('dateend') + "&durationstart=" + request.args.get('durationstart') + "&durationend=" + request.args.get('durationend')
    return url
    
############ LOGIN PAGE ###########

def getCorrectLogin():
    con = sqlite3.connect("logs115.db")
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS login(username varchar primary key, pwd varchar)")
    cur.execute("SELECT COUNT(*) FROM login")
    result = cur.fetchall()
    numaccounts = result[0][0]
    if numaccounts == 0:
        print("here", file=sys.stderr)
        cur.executemany("INSERT INTO login (username, pwd) VALUES (?, ?);", [('cdc', 'cdc')])
    cur.execute("SELECT username FROM login LIMIT 1")
    usernames = cur.fetchall()
    username = usernames[0][0]
    cur.execute("SELECT pwd FROM login LIMIT 1")
    pwds = cur.fetchall()
    pwd = pwds[0][0]
    con.commit()
    con.close()
    return username, pwd

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method=="POST":
        # Extract correct username and password--if none have been set, default is "cdc" and "cdc"
        username, pwd = getCorrectLogin()
        if request.form.get('username') == None or request.form.get('pwd') == None:
            return render_template('index.html')
        if request.form.get('username') != username or request.form.get('pwd') != pwd:
            return render_template('wronglogin.html')
        else:
            session['logged_in'] = True
            return redirect('/overview')
    else:
        return render_template('index.html')

@app.route("/changelogin", methods=["GET", "POST"])
def changelogin():
    if request.method=="POST":
        username, pwd = getCorrectLogin()
        if request.form.get('oldusername') == None or request.form.get('oldpwd') == None or request.form.get('newusername') == None or request.form.get('newpwd') == None:
            return render_template('changelogin.html')
        elif request.form.get('oldusername') != username or request.form.get('oldpwd') != pwd:
            return render_template('wronglogin.html')
        else:
            con = sqlite3.connect("logs115.db")
            cur = con.cursor()
            cur.execute("DELETE FROM login")
            cur.executemany("INSERT INTO login (username, pwd) VALUES (?, ?);", [(request.form.get('newusername'), request.form.get('newpwd'))])
            con.commit()
            con.close()
            return redirect('/')
    else:
        return render_template('changelogin.html')


########## DASHBOARD PAGES: OVERVIEW, PUBLIC, AND HC REPORTS ##########
# Get the specified column of a table (used to get specific series for graphs)
def column(matrix, i):
    return [row[i] for row in matrix]

# Parse the duration in string/minutes format (the format used in the URL parameters) into seconds format for SQL; aso produces add-on for duration in title
def parseDuration(duration_start, duration_end):
    if (duration_start == '0' and duration_end == '5'):
        duration_string = " AND duration <= 300"
        title_addon = " (0-5 minutes)"
    elif (duration_start == '5' and duration_end == '10'):
        duration_string = " AND duration > 300 AND duration <= 600"
        title_addon = " (5-10 minutes)"
    elif (duration_start == '10' and duration_end == "end"):
        duration_string = " AND duration > 600"
        title_addon = " (10+ minutes)"
    else:
        duration_string = ""
        title_addon = ""       
    return (duration_string, title_addon)

# Generates the SQL query on a given table for the given date and duration specifics, with the where clause inserted in the condition string
def generateSQL(table, starting_date_string, ending_date_string, duration_string, condition_string):
    if table == "all":
        from_string = "calls"
    elif table == "public":
        from_string = "calls JOIN public_interactions ON calls.call_id = public_interactions.call_id"
    elif table == "hc_reports":
        from_string = "calls JOIN hc_reports ON calls.call_id = hc_reports.call_id"
    filter_string = " date >=" + "'" + starting_date_string + "'" " AND date <= " + "'" + ending_date_string + "'" + duration_string + " "
    chart_sql = "SELECT date, count(calls.call_id) as count FROM " + from_string + " WHERE " + condition_string + " AND " + filter_string + "GROUP BY date ORDER BY date desc"
    total_sql = "SELECT count(calls.call_id) FROM " + from_string + " WHERE " + condition_string + " AND " + filter_string
    avg_sql = "SELECT avg(count) FROM (" + chart_sql + ")"
    return (chart_sql, total_sql, avg_sql)

# Given three SQL statements (one for the chart, one for the total, and one for the average), executes the SQL statements and calls the helper chart function to create the chart
def generateFigures(chart_sql, total_sql, avg_sql, title):
    con = sqlite3.connect("logs115.db")
    cur = con.cursor()
    cur.execute(chart_sql)
    calls_by_date = cur.fetchall()
    dates = []
    numcalls = []
    for log in calls_by_date:
        dates = dates + [log[0]]
        numcalls = numcalls + [log[1]]
    chart = helpers.calls_by_day(dates, numcalls, title)
    # Average
    cur.execute(total_sql)
    totals = cur.fetchall()
    total = totals[0][0]
    # Average by day
    # If the total is zero, we already know the average is zero
    if total == 0:
        avg = 0
    else:
        cur.execute(avg_sql)
        avgs = cur.fetchall()
        avg = int(round(avgs[0][0]))
    con.close()
    return (chart, total, avg)

# Same as the above function, but the chart created by this function is downloadable
def generateFiguresDownload(chart_sql, total_sql, avg_sql, title, filename):
    con = sqlite3.connect("logs115.db")
    cur = con.cursor()
    cur.execute(chart_sql)
    calls_by_date = cur.fetchall()
    dates = []
    numcalls = []
    for log in calls_by_date:
        dates = dates + [log[0]]
        numcalls = numcalls + [log[1]]
    chart = helpers.calls_by_day_offline(dates, numcalls, title, filename)
    # Total
    cur.execute(total_sql)
    totals = cur.fetchall()
    total = totals[0][0]
    # Average by day
    if total == 0:
        avg = 0
    else:
        cur.execute(avg_sql)
        avgs = cur.fetchall()
        avg = int(round(avgs[0][0]))
    con.close()
    return (total, avg)

@app.route('/overview', methods=["GET"])
def overview():  
    # Check for log-in
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    # If all parameters not available, default to page with built-in parameters
    if request.args.get('datestart') == None or request.args.get('dateend') == None or request.args.get('durationstart') == None or request.args.get('durationend') == None:
        now_date = datetime.datetime.now()
        now_string = now_date.strftime("%Y-%m-%d")
        month_ago = now_date - datetime.timedelta(days = 30)
        monthago_string = month_ago.strftime("%Y-%m-%d")
        return redirect('/overview?datestart=' + monthago_string + '&dateend=' + now_string + '&durationstart=0&durationend=end')
    # Parse duration from URL parameters
    duration_string, title_addon = parseDuration(request.args.get('durationstart'), request.args.get('durationend'))
    # Parse dates from URL parameters
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    # Make queries for data in charts and statistics (total and average)
    charts = []
    totals = []
    averages = []
    # Generate calls by day to overall hotline chart
    condition_string = "call_id != ''"
    chart_sql, total_sql, avg_sql = generateSQL("all", starting_date_string, ending_date_string, duration_string, condition_string)
    chart, total, avg = generateFigures(chart_sql, total_sql, avg_sql, "Calls to Entire Hotline by Day" + title_addon)
    charts.append(chart)
    totals.append(total)
    averages.append(avg)
    return render_template("overview.html", figures = zip(charts, totals, averages))

@app.route("/public", methods=["GET", "POST"])
def public():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    # If all parameters not available, default to page with built-in parameters
    if request.args.get('datestart') == None or request.args.get('dateend') == None or request.args.get('durationstart') == None or request.args.get('durationend') == None:
        now_date = datetime.datetime.now()
        now_string = now_date.strftime("%Y-%m-%d")
        month_ago = now_date - datetime.timedelta(days = 30)
        monthago_string = month_ago.strftime("%Y-%m-%d")
        return redirect('/public?datestart=' + monthago_string + '&dateend=' + now_string + '&durationstart=0&durationend=end')
    # Parse duration from URL parameters
    duration_string, title_addon = parseDuration(request.args.get('durationstart'), request.args.get('durationend'))
    # Parse dates from URL parameters
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    #Open database
    con = sqlite3.connect("logs115.db")
    cur = con.cursor()
    charts = []
    totals = []
    averages = []
    #Calls to public hotline chart
    condition_string = " type='public' "
    chart_sql, total_sql, avg_sql = generateSQL("all", starting_date_string, ending_date_string, duration_string, condition_string)
    chart, total, avg = generateFigures(chart_sql, total_sql, avg_sql, "Calls to Public Hotline by Day" + title_addon)
    charts.append(chart)
    totals.append(total)
    averages.append(avg)
    #Disease charts (tracking visits to overview and prevention information)
    public_diseases = ["h5n1", "mers", "zika"]
    for disease in public_diseases:
        menu_string = disease + "_menu"
        overview_string = disease + "_overview_menu"
        prevention_string = disease + "_prevention_menu"
        condition_string_overview = "(" + menu_string + "=1 OR " + overview_string + "=1 OR " + prevention_string + "=2)"
        condition_string_prevention = "(" + menu_string + "=2 OR " + overview_string + "=2 OR " + prevention_string + "=1)"
        chart_sql_overview, total_sql_overview, avg_sql_overview = generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string_overview)
        chart_sql_prevention, total_sql_prevention, avg_sql_prevention = generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string_prevention)
        cur.execute(chart_sql_overview)
        overview_visits = cur.fetchall()
        cur.execute(chart_sql_prevention)
        prevention_visits = cur.fetchall()
        dates = column(overview_visits, 0)
        overview = column(overview_visits, 1)
        prevention = column(prevention_visits, 1)
        disease_chart = helpers.overview_and_prevention_by_day(dates, overview, prevention, str.title(disease) + title_addon)
        charts.append(disease_chart)
        #Total visits to menu
        total_sql = "SELECT count(calls.call_id) FROM calls JOIN public_interactions ON calls.call_id = public_interactions.call_id WHERE date >=" + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " AND(" + menu_string + "=1 OR " + menu_string + "=2)"
        cur.execute(total_sql)
        total = cur.fetchall()
        totals.append(total[0][0])
        #Average visits to menu
        days_sql = "SELECT count(DISTINCT date) FROM calls"
        cur.execute(days_sql)
        num_days = cur.fetchall()
        averages.append(total[0][0]/num_days[0][0]);
    #Public reports by day chart
    condition_string = "public_report_confirmation='0'"
    chart_sql, total_sql, avg_sql = generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string)
    chart, total, avg = generateFigures(chart_sql, total_sql, avg_sql, "Public Disease Reports by Day" + title_addon)
    charts.append(chart)
    totals.append(total)
    averages.append(avg)
    #Calls requesting more info chart
    condition_string = "hotline_menu='3'"
    chart_sql, total_sql, avg_sql = generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string)
    chart, total, avg = generateFigures(chart_sql, total_sql, avg_sql, "Calls Requesting Additional Information by Day" + title_addon)
    charts.append(chart)
    totals.append(total)
    averages.append(avg)
    #Calls requesting ambulance info chart
    condition_string = "hotline_menu='4'"
    chart_sql, total_sql, avg_sql = generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string)
    chart, total, avg = generateFigures(chart_sql, total_sql, avg_sql, "Calls Requesting Ambulance Information by Day" + title_addon)
    charts.append(chart)
    totals.append(total)
    averages.append(avg)
    #Close database and render HTML template
    con.close()
    return render_template("public.html", figures=zip(charts, totals, averages))

@app.route("/hcreports", methods=["GET", "POST"])
def hcreports():
    # Check for log in
    if not session.get('logged_in'):
        return redirect(url_for('index'))

    if request.args.get('datestart') == None or request.args.get('dateend') == None:
        now_date = datetime.datetime.now()
        now_string = now_date.strftime("%Y-%m-%d")
        month_ago = now_date - datetime.timedelta(days = 30)
        monthago_string = month_ago.strftime("%Y-%m-%d")
        return redirect('/hcreports?datestart=' + monthago_string + '&dateend=' + now_string)

    # Parse dates from URL parameters
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')

    con = sqlite3.connect("logs115.db")
    cur = con.cursor()
    #Generate first chart: attempted & completed HC reports by week
    cur.execute("SELECT week_id, count(calls.call_id) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE completed = 'true' AND date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id ORDER BY week_id asc;")
    completed_reports_by_week = cur.fetchall()
    cur.execute("SELECT week_id, count(calls.call_id) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + "  GROUP BY week_id ORDER BY week_id asc;")
    attempted_reports_by_week = cur.fetchall()
    weeks = column(completed_reports_by_week, 0)
    completed = column(completed_reports_by_week, 1)
    attempted = column(attempted_reports_by_week, 1)
    chart2 = helpers.reports_by_week(weeks, completed, attempted, "HC Reports by Week (Completed vs Attempted)")
    #Generate second chart (line chart of cases of each disease by week)
    cur.execute("SELECT week_id, sum(diarrhea_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    diarrhea_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(fever_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    fever_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(flaccid_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    flaccid_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(respiratory_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    respiratory_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(dengue_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    dengue_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(meningitis_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    meningitis_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(jaundice_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    jaundice_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(diphteria_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    diphteria_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(rabies_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    rabies_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(neonatal_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    neonatal_cases = cur.fetchall()
    dates = column(diarrhea_cases, 0)
    diarrhea = column(diarrhea_cases, 1)
    fever = column(fever_cases, 1)
    flaccid = column(flaccid_cases, 1)
    respiratory = column(respiratory_cases, 1)
    dengue = column(dengue_cases, 1)
    meningitis = column(meningitis_cases, 1)
    jaundice = column(jaundice_cases, 1)
    diphteria = column(diphteria_cases, 1)
    rabies = column(rabies_cases, 1)
    neonatal = column(neonatal_cases, 1)
    chart3 = helpers.case_reports_by_week(dates, diarrhea, fever, flaccid, respiratory, dengue, meningitis, jaundice, diphteria, rabies, neonatal, "Reports of Disease Cases by Week")
    #Generate third chart (line chart of cases of each disease by week)
    cur.execute("SELECT week_id, sum(diarrhea_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    diarrhea_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(fever_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    fever_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(flaccid_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    flaccid_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(respiratory_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    respiratory_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(dengue_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    dengue_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(meningitis_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    meningitis_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(jaundice_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    jaundice_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(diphteria_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    diphteria_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(rabies_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    rabies_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(neonatal_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE date >= " + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " GROUP BY week_id;")
    neonatal_cases = cur.fetchall()
    dates = column(diarrhea_cases, 0)
    diarrhea = column(diarrhea_cases, 1)
    fever = column(fever_cases, 1)
    flaccid = column(flaccid_cases, 1)
    respiratory = column(respiratory_cases, 1)
    dengue = column(dengue_cases, 1)
    meningitis = column(meningitis_cases, 1)
    jaundice = column(jaundice_cases, 1)
    diphteria = column(diphteria_cases, 1)
    rabies = column(rabies_cases, 1)
    neonatal = column(neonatal_cases, 1)
    chart4 = helpers.case_reports_by_week(dates, diarrhea, fever, flaccid, respiratory, dengue, meningitis, jaundice, diphteria, rabies, neonatal, "Reports of Disease Deaths by Week")
    con.close()
    return render_template("hcreports.html", chart2=chart2, chart3=chart3, chart4=chart4)

@app.route("/explore", methods=["GET", "POST"])
def explore():
    # Check for log in
    if not session.get('logged_in'):
        return redirect(url_for('index'))

    # Parse dates from URL parameters
    starting_date_string = '2015-09-03'
    ending_date_string = '2017-08-29'

    con = sqlite3.connect("logs115.db")
    cur = con.cursor()
    #Generate first chart: attempted & completed HC reports by week
    cur.execute('SELECT diarrhea_cases FROM hc_reports WHERE diarrhea_cases > 100')
    raws = cur.fetchall()
    cases = [raw[0] for raw in raws]
    figure1 = {
        "data": [
            {
                "type": "histogram",
                "x": cases,
                "xbins": {
                    "start": 100,
                    "end": 1000,
                    "size": 100
                },
                "marker": {
                    "color": '#ED7D31'
                } 
            }
        ],
        "layout": {
            "title": "Histogram of Diarrhea Cases in Disease Reports (Reports with >100 Cases)",
            "showlegend": False
        }
    }
    plot1 = plotly.offline.plot(figure1, output_type="div", show_link=False, link_text=False)
    cur.execute('SELECT duration FROM calls')
    raws = cur.fetchall()
    data = [raw[0] for raw in raws]
    figure2 = {
        "data": [
            {
                "type": "histogram",
                "x": data,
                "xbins": {
                    "start": 0,
                    "end": 300,
                    "size": 10
                },
                "marker": {
                    "color": '#659A41'
                },  
            }
        ],
        "layout": {
            "title": "Histogram of Call Times (Only Calls Under 300 Seconds)",
            "showlegend": False,
        }
    }
    plot2 = plotly.offline.plot(figure2, output_type="div", show_link=False, link_text=False)
    cur.execute('SELECT status, COUNT(*) as count FROM calls WHERE duration > 10 GROUP BY status')
    raws = cur.fetchall()
    lables = [raw[0] for raw in raws]
    data = [raw[1] for raw in raws]
    figure3 = {
        "data": [
            {
                "labels": lables,
                "hoverinfo": "none",
                #"marker": {
                 #   "colors": [
                  #      "rgb(0,255,00)",
                   #     "rgb(255,0,0)",
                    #]
                #},
                "type": "pie",
                "values": data
            }
        ],
        "layout": {
            "title": "Calls by Status",
            "showlegend": True
            }
    }
    plot3 = plotly.offline.plot(figure3, output_type="div", show_link=False, link_text=False)
    con.close()
    return render_template("explore.html", plot1 = plot1, plot2 = plot2, plot3 = plot3)

########## DOWNLOADABLE REPORTS ##########
# Append PDFs (input files) to a PDF file writer (output)
def append_pdf(input,output):
    [output.addPage(input.getPage(page_num)) for page_num in range(input.numPages)]

# Make PDF out of a list of images
def makePdf(pdfFileName, listPages, dir = ''):
    if (dir):
        dir += "/"

    cover = Image.open(dir + str(listPages[0]))
    width, height = cover.size

    pdf = FPDF(unit = "pt", format = [width, height])

    for page in listPages:
        pdf.add_page()
        pdf.image(dir + str(page), 0, 0)

    pdf.output(dir + pdfFileName + ".pdf", "F")

def genReport(starting_date_string, ending_date_string, qualitative, to_email, target_url):
    # Clean up working directory
    for f in os.listdir(os.getcwd()):
        if f.endswith(".png"):
            os.remove(f)
    # File title includes current timestamp for unique identification
    now = datetime.datetime.now()
    filetitle = "report" + now.strftime("%d-%m-%y-%H-%M-%S") + ".pdf"
    print('writing qualitative', file=sys.stderr)
    #Set up PDF document and styles
    doc = SimpleDocTemplate("hello.pdf", pagesize=letter)
    parts = []
    folder = os.path.dirname(reportlab.__file__) + os.sep + 'fonts'   
    ttfFile = os.path.join(folder, 'Vera.ttf')   
    pdfmetrics.registerFont(TTFont("Vera", ttfFile))
    styles= {
        'paragraph': ParagraphStyle(
            'paragraph',
            fontName='Vera',
            fontSize=10,
            alignment=TA_LEFT
        ),
        'title': ParagraphStyle(
            'title',
            fontName='Vera',
            fontSize=20,
            alignment=TA_CENTER
        ),
        'report_title': ParagraphStyle(
            'report_title',
            fontName='Vera',
            fontSize=30,
            alignment=TA_CENTER
        ),
    }
    #Title Page
    parts.append(Spacer(1, 3*inch))
    parts.append(Paragraph("115 Hotline Report", styles['report_title']))
    parts.append(Spacer(1, 0.7*inch))
    parts.append(Paragraph(starting_date_string + " to " + ending_date_string, styles['report_title']))
    parts.append(PageBreak())
    #Qualitative description page
    parts.append(Paragraph("Qualitative Description", styles['title']))
    parts.append(Spacer(1, inch))
    parts.append(Paragraph(qualitative, styles['paragraph']))
    parts.append(PageBreak())
    parts.append(Paragraph("Summary Statistics", styles['title']))
    parts.append(Spacer(1, inch))
    #Rest of report: statistics and graphs
    # Calls by day entire hotline PNG and statistics
    print('making sql queries and generating pngs', file=sys.stderr)
    con = sqlite3.connect("logs115.db")
    cur = con.cursor()
    condition_string = "call_id != ''"
    duration_string, title_addon = parseDuration('0', 'end')
    chart_sql, total_sql, avg_sql = generateSQL("all", starting_date_string, ending_date_string, duration_string, condition_string)
    total, avg = generateFiguresDownload(chart_sql, total_sql, avg_sql, "Calls to Entire Hotline By Day" + title_addon, "overview.png")
    parts.append(Paragraph("Total calls to entire hotline: " + str(total), styles['paragraph']))
    parts.append(Spacer(1, 0.3*inch))
    parts.append(Paragraph("Average calls to entire hotline (by day): " + str(avg), styles['paragraph']))
    parts.append(Spacer(1, 0.3*inch))
    # Calls by day public hotline PNG and statistics
    condition_string = " type='public' "
    chart_sql, total_sql, avg_sql = generateSQL("all", starting_date_string, ending_date_string, duration_string, condition_string)
    total, avg = generateFiguresDownload(chart_sql, total_sql, avg_sql, "Calls to Public Hotline By Day" + title_addon, "public.png")
    parts.append(Paragraph("Total calls to public hotline: " + str(total), styles['paragraph']))
    parts.append(Spacer(1, 0.3*inch))
    parts.append(Paragraph("Average calls to public hotline (by day): " + str(avg), styles['paragraph']))
    parts.append(Spacer(1, 0.3*inch))
    # Calls to each disease menu by day PNGs and statistics
    public_diseases = ["h5n1", "mers", "zika"]
    for disease in public_diseases:
        menu_string = disease + "_menu"
        overview_string = disease + "_overview_menu"
        prevention_string = disease + "_prevention_menu"
        condition_string_overview = "(" + menu_string + "=1 OR " + overview_string + "=1 OR " + prevention_string + "=2)"
        condition_string_prevention = "(" + menu_string + "=2 OR " + overview_string + "=2 OR " + prevention_string + "=1)"
        chart_sql_overview, total_sql_overview, avg_sql_overview = generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string_overview)
        chart_sql_prevention, total_sql_prevention, avg_sql_prevention = generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string_prevention)
        cur.execute(chart_sql_overview)
        overview_visits = cur.fetchall()
        cur.execute(chart_sql_prevention)
        prevention_visits = cur.fetchall()
        dates = column(overview_visits, 0)
        overview = column(overview_visits, 1)
        prevention = column(prevention_visits, 1)
        disease_chart = helpers.overview_and_prevention_by_day_download(dates, overview, prevention, str.title(disease) + title_addon, disease + ".png")
        total_sql = "SELECT count(calls.call_id) FROM calls JOIN public_interactions ON calls.call_id = public_interactions.call_id WHERE date >=" + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'" + " AND(" + menu_string + "=1 OR " + menu_string + "=2)"
        cur.execute(total_sql)
        total = cur.fetchall()
        parts.append(Paragraph("Total calls to " + disease + " menu (overview or prevention): " + str(total[0][0]), styles['paragraph']))
        parts.append(Spacer(1, 0.3*inch))
        days_sql = "SELECT count(DISTINCT date) FROM calls WHERE date >=" + "'" + starting_date_string + "'" + " AND date <= " + "'" + ending_date_string + "'"
        cur.execute(days_sql)
        num_days = cur.fetchall()
        if num_days[0][0] == 0:
            avg = 0
        else:
            avg = total[0][0]/num_days[0][0]
        parts.append(Paragraph("Average calls to " + disease + " menu (overview or prevention): " + str(avg), styles['paragraph']))
        parts.append(Spacer(1, 0.3*inch))
    # Public reports by day PNG and statistics
    condition_string = "public_report_confirmation='0'"
    chart_sql, total_sql, avg_sql = generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string)
    total, avg = generateFiguresDownload(chart_sql,total_sql, avg_sql, "Public Disease Reports by Day" + title_addon, "publicreports.png")
    parts.append(Paragraph("Total public reports: " + str(total), styles['paragraph']))
    parts.append(Spacer(1, 0.3*inch))
    parts.append(Paragraph("Average public reports (by day): " + str(avg), styles['paragraph']))
    parts.append(Spacer(1, 0.3*inch))
    # More info by day PNG and statistics
    condition_string = "hotline_menu='3'"
    chart_sql, total_sql, avg_sql = generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string)
    total, avg = generateFiguresDownload(chart_sql, total_sql, avg_sql, "Calls Requesting Additional Information by Day" + title_addon, "moreinfo.png")
    parts.append(Paragraph("Total calls requesting more information: " + str(total), styles['paragraph']))
    parts.append(Spacer(1, 0.3*inch))
    parts.append(Paragraph("Average calls requesting more information (by day): " + str(avg), styles['paragraph']))
    parts.append(Spacer(1, 0.3*inch))
    # Ambulance info by day PNG and statistics
    condition_string = "hotline_menu='4'"
    chart_sql, total_sql, avg_sql = generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string)
    total, avg = generateFiguresDownload(chart_sql, total_sql, avg_sql, "Calls Requesting Ambulance Information by Day" + title_addon, "ambulance.png")
    parts.append(Paragraph("Total calls to public hotline: " + str(total), styles['paragraph']))
    parts.append(Spacer(1, 0.3*inch))
    parts.append(Paragraph("Average calls to public hotline (by day): " + str(avg), styles['paragraph']))
    con.close()
    print('creating graphs pdf', file=sys.stderr)
    # Make PDF of all graphs
    makePdf("graphs", ["overview.png", "public.png", "h5n1.png", "mers.png", "zika.png", "publicreports.png", "moreinfo.png", "ambulance.png"])
    doc.build(parts)
    # Combine PDF with text (title page, qualitative, statistics) and PDF with graphs
    print('combining all pdfs', file=sys.stderr)
    output = PdfFileWriter()
    append_pdf(PdfFileReader(open("hello.pdf","rb")),output)
    append_pdf(PdfFileReader(open("graphs.pdf","rb")),output)
    output.write(open(filetitle,"wb"))
    print('sending email', file=sys.stderr)
    fromaddr = "emily.aiken@instedd.org"
    toaddr = to_email
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Your 115 Hotline Report"
    body = "The PDF report you requested is attached to this email."
    msg.attach(MIMEText(body, 'plain'))
    attachment = open(filetitle, "rb")
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filetitle) 
    msg.attach(part)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "dolphin1997")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()



@app.route("/download")
def download():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    if request.args.get('datestart') == None or request.args.get('dateend') == None:
        now_date = datetime.datetime.now()
        now_string = now_date.strftime("%Y-%m-%d")
        month_ago = now_date - datetime.timedelta(days = 30)
        monthago_string = month_ago.strftime("%Y-%m-%d")
        return redirect('/download?datestart=' + monthago_string + '&dateend=' + now_string)
    # Parse dates from URL parameters
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    return render_template("download.html", redirect_string = "/downloading?datestart=" + starting_date_string + "&dateend=" + ending_date_string)

@app.route("/downloading", methods=["GET", "POST"])
def downloading():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    th = Thread(target=genReport, args=(request.args.get('datestart'), request.args.get('dateend'), request.form['qualitative'], request.form['email'], url_for('downloaded')))
    th.start()
    return render_template("downloading.html")

@app.route("/downloaded", methods=["GET"])
def downloaded():
    filetitle = request.args.get('filename') + ".pdf"
    return send_file(filetitle, attachment_filename=filetitle, as_attachment=True)
    

########## CSV UPLOAD ###########    
# Checks if the uploaded file is a CSV
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# For the caller-ID cell, sets anonymous callers to NULL
def removeAnonymous(caller_id):
    if caller_id[0] == 'A':
        return None
    else:
        return caller_id

# Deletes stars at end of disease reports
def deleteStar(disease_report):
    for i in range(len(disease_report)):
        if disease_report[i] == "*":
            return disease_report[0:i]
    return disease_report

# Parses the start and end date/time object into two seperate objects, one for date and one for time
def parseDateTime(fulldate):
    if fulldate == "":
        return "", ""
    else:
        for i in range(len(fulldate)):
            if fulldate[i] == " ":
                backwards_date = fulldate[0:i]
                day = backwards_date[0:2]
                month = backwards_date[3:5]
                year = backwards_date[6:10]
                forwards_date = year + '-' + month + '-' + day
                return forwards_date, fulldate[i:len(fulldate)]
    return "", ""

# Given the CSV file name, loads the call logs into memory (if they are not duplicates of previously loaded logs)
def loadData(data_file_name):
    con = sqlite3.connect("logs115.db")
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS calls (call_id integer primary key, date varchar, time time, week_id varchar, duration integer, caller_id integer, status varchar, type varchar);")
    cur.execute("CREATE TABLE IF NOT EXISTS hc_reports (call_id integer primary key, level_worker integer, completed varchar, disease_type integer, diarrhea_cases integer, diarrhea_deaths integer, fever_cases integer, fever_deaths integer, flaccid_cases integer, flaccid_deaths integer, respiratory_cases integer, respiratory_deaths integer, dengue_cases integer, dengue_deaths integer, meningitis_cases integer, meningitis_deaths integer, jaundice_cases integer, jaundice_deaths integer, diphteria_cases integer, diphteria_deaths integer, rabies_cases integer, rabies_deaths integer, neonatal_cases integer, neonatal_deaths integer);")
    cur.execute("CREATE TABLE IF NOT EXISTS  public_interactions (call_id integer primarykey, hotline_menu integer, disease_menu integer, h5n1_menu integer, h5n1_overview_menu integer, h5n1_prevention_menu integer, mers_menu integer, mers_overview_menu integer, mers_prevention_menu integer, zika_menu integer, zika_overview_menu integer, zika_prevention_menu integer, public_report_confirmation integer);")
    with open(data_file_name, 'rU') as fin: # In-file is rawcalls.csv
        dr = csv.DictReader(fin) # First line is used as column headers by default
        prev_date = ""
        week_id = ""
        day_counter = 7
        for call in dr:
            #print("reading call " + call['ID'], file=sys.stderr)
            # Record general info--call ID, date, time, caller ID, status, level of worker, and cdc report confirmations
            if call['ID'] == "": # If we are passed the end of the call records, stop
                break
            cur.execute("SELECT * FROM calls WHERE call_id = " + "'" + call['ID'] + "'");
            duplicate_calls = cur.fetchall()
            if len(duplicate_calls) == 0:
                dateTime = parseDateTime(call['Started'])
                date = dateTime[0]
                time = dateTime[1]
                day_of_week = datetime.datetime.strptime(date, '%Y-%m-%d').weekday()
                if not prev_date == date and day_of_week == 2:
                    week_id = "Week of " + date
                prev_date = date
                caller_interaction = call['Caller interaction']
                call_type = 'public'
                if ("Welcome 0 reporting" in caller_interaction or "Welcome keypad reporting" in caller_interaction):
                    call_type = 'hc_worker'
                general_info = [(call['ID'], date, time, week_id, call['Duration(second)'], removeAnonymous(call['Caller ID']), call['Status'], call_type)]
                cur.executemany("INSERT INTO calls (call_id, date, time, week_id, duration, caller_id, status, type) VALUES (?, ?, ?, ?, ?, ?, ?, ?);", general_info)
                # Record disease report information--disease type and disease # inputs
                if (call_type == "hc_worker"):
                    report_vars = ('var_dairrhea_case', 'var_dairrhea_death', 'var_fever_case', 'var_fever_death', 'var_flaccid_case', 'var_flaccid_death', 'var_respiratory_case', 'var_respiratory_death', 'var_dengue_case', 'var_dengue_death', 'var_meningetis_case', 'var_meningitis_death', 'var_juandice_case', 'var_juandice_death', 'var_diphteria_case', 'var_diphteria_death', 'var_rabies_case', 'var_rabies_death', 'va_neonatal_case', 'var_neonatal_death')
                    reports = (call['disease_type'],)
                    report_something = "false"
                    for var in report_vars:
                        if call[var] == "": # Did not enter any of this disease
                            reports = reports + (0,)
                        else: # Some of disease reported
                            reports = reports + (deleteStar(call[var]),)
                            report_something = "true"
                    completed = "false"
                    if ((call['cdc_report_started'] == '1' and call['cdc_report_ended'] == '1') or (call['cdc_report_started'] != '1' and report_something == "true")):
                        completed = "true"
                    to_db = [(call['ID'], completed) + reports]
                    cur.executemany("INSERT INTO hc_reports (call_id, completed, disease_type, diarrhea_cases, diarrhea_deaths, fever_cases, fever_deaths, flaccid_cases, flaccid_deaths, respiratory_cases, respiratory_deaths, dengue_cases, dengue_deaths, meningitis_cases, meningitis_deaths, jaundice_cases, jaundice_deaths, diphteria_cases, diphteria_deaths, rabies_cases, rabies_deaths, neonatal_cases, neonatal_deaths) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", to_db)
                    # Record public interaction with menus
                else:
                    disease_menus = ('hotline_menu', 'disease_menu', 'h5n1_menu', 'h5n1_overview_menu', 'h5n1_prevention_menu', 'mers_menu', 'mers_overview_menu', 'mers_prevention_menu', 'zika_menu', 'zika_overview_menu', 'zika_prevention_menu', 'public_report_confirmation')
                    interaction = ()
                    for menu in disease_menus:
                        if call[menu] == "":
                            interaction = interaction + (None,)
                        else:
                            interaction = interaction + (call[menu],)
                    to_db = [(call['ID'],) + interaction]
                    cur.executemany("INSERT INTO public_interactions (call_id, hotline_menu, disease_menu, h5n1_menu, h5n1_overview_menu, h5n1_prevention_menu, mers_menu, mers_overview_menu, mers_prevention_menu, zika_menu, zika_overview_menu, zika_prevention_menu, public_report_confirmation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", to_db)
    con.commit()
    con.close()

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    if request.args.get('step') == None or request.args.get('step') == '1':
        return render_template("upload1.html")
    elif request.args.get('step') == '2':
        return render_template("upload2.html")
    elif request.args.get('step') == 'template':
        return send_file('call_logs_template.csv', as_attachment = True)
    else:
        return render_template("upload3.html")


@app.route("/dataload", methods=["GET", "POST"])
def dataload():
    if not session.get('logged_in'):
       return redirect(url_for('index'))
    csv = request.files['log']
    # The file must be a CSV
    if csv and allowed_file(csv.filename):
        # Secure the file name so it doesn't have any illegal characters
        filename = secure_filename(csv.filename)
        csv.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # Upload data from the saved file to the dashboard
        loadData("uploads/" + filename)
    else:
        return render_template("uploadfail.html")
    return render_template("uploadcomplete.html")

app.secret_key = 'secret key'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['csv'])
app.config['SESSION_TYPE'] = 'filesystem'
# Run application
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)