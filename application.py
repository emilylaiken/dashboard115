from __future__ import print_function
import os
import csv
import sqlite3
import time
import datetime
from flask import Flask, redirect, render_template, request, url_for
import sys


import helpers

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Takes the combined date-time cell in the CSV and parses it into two separate objects
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

# For the caller-ID cell, sets anonymous callers to NULL
def removeAnonymous(caller_id):
    if caller_id[0] == 'A':
        return None
    else:
        return caller_id

def deleteStar(disease_report):
    for i in range(len(disease_report)):
        if disease_report[i] == "*":
            return disease_report[0:i]
    return disease_report

def column(matrix, i):
    return [row[i] for row in matrix]

def loadData(data_file_name):
    con = sqlite3.connect("logs115.db")
    cur = con.cursor()
    
    cur.execute("CREATE TABLE IF NOT EXISTS calls (call_id integer primary key, date varchar, time time, week_id varchar, duration integer, caller_id integer, status varchar, type varchar);")
    cur.execute("CREATE TABLE IF NOT EXISTS hc_reports (call_id integer primary key, level_worker integer, completed varchar, disease_type integer, diarrhea_cases integer, diarrhea_deaths integer, fever_cases integer, fever_deaths integer, flaccid_cases integer, flaccid_deaths integer, respiratory_cases integer, respiratory_deaths integer, dengue_cases integer, dengue_deaths integer, meningitis_cases integer, meningitis_deaths integer, jaundice_cases integer, jaundice_deaths integer, diphteria_cases integer, diphteria_deaths integer, rabies_cases integer, rabies_deaths integer, neonatal_cases integer, neonatal_deaths integer);")
    cur.execute("CREATE TABLE IF NOT EXISTS  public_interactions (call_id integer primarykey, hotline_menu integer, disease_menu integer, h5n1_menu integer, h5n1_overview_menu integer, h5n1_prevention_menu integer, mers_menu integer, mers_overview_menu integer, mers_prevention_menu integer, zika_menu integer, zika_overview_menu integer, zika_prevention_menu integer, public_report_confirmation integer);")
    cur.execute("SELECT Max(date) FROM calls")
    max_date = cur.fetchall()[0][0];
    with open(data_file_name, 'rU') as fin: # In-file is rawcalls.csv
        dr = csv.DictReader(fin) # First line is used as column headers by default
        prev_date = ""
        week_id = ""
        day_counter = 7
        for call in dr:
            # Record general info--call ID, date, time, caller ID, status, level of worker, and cdc report confirmations
            if call['ID'] == "": # If we are passed the end of the call records, stop
                break
            dateTime = parseDateTime(call['Started'])
            date = dateTime[0]
            if (date > max_date):
                time = dateTime[1]
                if not prev_date == date:
                    day_counter = day_counter + 1
                if (day_counter == 8):
                    week_id = "Week of " + date
                    day_counter = 1
                prev_date = date
                call_type = 'public'
                if (call['cdc_report_started'] == '1'):
                    call_type = 'hc_worker'
                general_info = [(call['ID'], date, time, week_id, call['Duration(second)'], removeAnonymous(call['Caller ID']), call['Status'], call_type)]
                cur.executemany("INSERT INTO calls (call_id, date, time, week_id, duration, caller_id, status, type) VALUES (?, ?, ?, ?, ?, ?, ?, ?);", general_info)
                # Record disease report information--disease type and disease # inputs
                if (call_type == "hc_worker"):
                    report_vars = ('var_dairrhea_case', 'var_dairrhea_death', 'var_fever_case', 'var_fever_death', 'var_flaccid_case', 'var_flaccid_death', 'var_respiratory_case', 'var_respiratory_death', 'var_dengue_case', 'var_dengue_death', 'var_meningetis_case', 'var_meningitis_death', 'var_juandice_case', 'var_juandice_death', 'var_diphteria_case', 'var_diphteria_death', 'var_rabies_case', 'var_rabies_death', 'va_neonatal_case', 'var_neonatal_death')
                    reports = (call['disease_type'],)
                    for var in report_vars:
                        if call[var] == "": # Did not enter any of this disease
                            reports = reports + (0,)
                        else: # Some of disease reported
                            reports = reports + (deleteStar(call[var]),)
                    completed = "false"
                    if (call['cdc_report_ended'] == '1'):
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
@app.route("/")
def index():
    time_period = "week"
    time_period = request.args.get('time')
    current_date = datetime.date.today() - datetime.timedelta(weeks = 16)
    if time_period == "week":
        starting_date = current_date - datetime.timedelta(weeks = 1)
    elif time_period == "month":
        starting_date = current_date - datetime.timedelta(weeks = 4)
    elif time_period == "quarter":
        starting_date = current_date - datetime.timedelta(weeks = 12)
    else:
        starting_date = current_date - datetime.timedelta(weeks = 56)
    starting_date_string = starting_date.strftime("%Y-%m-%d")
    #Load additional call logs if there are any and open database
    #loadData("rawwcallsyear.csv")
    #loadData("rawcalls.csv")
    con = sqlite3.connect("logs115.db")
    cur = con.cursor()
    #print pd.read_sql_query("SELECT week_id, count(call_id) FROM calls GROUP BY week_id ORDER BY week_id", con)

    charts = []
    cur.execute("SELECT date, count(calls.call_id) FROM calls WHERE date >=" + "'" + starting_date_string + "'" + "GROUP BY date ORDER BY date desc;")
    calls_by_date = cur.fetchall()
    dates = []
    numcalls = []
    for log in calls_by_date:
        dates = dates + [log[0]]
        numcalls = numcalls + [log[1]]
    charts.append(helpers.calls_by_day(dates, numcalls, "Calls to Entire Hotline by Day"))

    #Close database and render HTML template
    con.close()
    return render_template("index.html", name="", charts = charts)


# Controls what happens on the loading of the dashboard--new data is read in, visualizations are produced
@app.route("/public", methods=["GET"])
def public():
    time_period = "week"
    time_period = request.args.get('time')
    
    duration_start = request.args.get('duration_start')
    duration_end = request.args.get('duration_end')
    duration_start = 0
    duration_end = 5
    #hero = request.args['startDate']
    #hero=request.args.get('startDate')
    #print(hero, file=sys.stderr)
    current_date = datetime.date.today() - datetime.timedelta(weeks = 16)
    if time_period == "week":
        starting_date = current_date - datetime.timedelta(weeks = 1)
    elif time_period == "month":
        starting_date = current_date - datetime.timedelta(weeks = 4)
    elif time_period == "quarter":
        starting_date = current_date - datetime.timedelta(weeks = 12)
    else:
        starting_date = current_date - datetime.timedelta(weeks = 56)
    starting_date_string = starting_date.strftime("%Y-%m-%d")

    if (duration_start == 0 and duration_end == "end"):
        duration_string = ""
    elif (duration_start == 5 and duration_end == "end"):
        #duration_string = " AND duration > 5"
        duration_string = ""
    else:
        #duration_string = " AND duration > " + str(duration_start) + " AND duration < " + str(duration_end)
        duration_string = ""
    #Load additional call logs if there are any and open database
    #loadData("rawwcallsyear.csv")
    #loadData("rawcalls.csv")
    con = sqlite3.connect("logs115.db")
    cur = con.cursor()
    #print pd.read_sql_query("SELECT week_id, count(call_id) FROM calls GROUP BY week_id ORDER BY week_id", con)

    charts = []
    #Generate chart of all calls to public hotline
    statement = "SELECT date, count(call_id) FROM calls WHERE type='public' AND date >=" + "'" + starting_date_string + "'" + duration_string + " GROUP BY date ORDER BY date desc;"
    cur.execute(statement)
    calls_by_date = cur.fetchall()
    dates = []
    numcalls = []
    for log in calls_by_date:
        dates = dates + [log[0]]
        numcalls = numcalls + [log[1]]
    charts.append(helpers.calls_by_day(dates, numcalls, "Calls to Public Hotline by Day"))

    #Generate third chart (line chart of visits to each disease menu by day)
    #cur.execute("SELECT date, count(calls.call_id) FROM calls JOIN public_interactions ON calls.call_id = public_interactions.call_id WHERE h5n1_menu NOT NULL GROUP BY date;")
    #h5n1_visits = cur.fetchall()
    #cur.execute("SELECT date, count(calls.call_id) FROM calls JOIN public_interactions ON calls.call_id = public_interactions.call_id WHERE mers_menu NOT NULL GROUP BY date;")
    #mers_visits = cur.fetchall()
    #cur.execute("SELECT date, count(calls.call_id) FROM calls JOIN public_interactions ON calls.call_id = public_interactions.call_id WHERE zika_menu NOT NULL GROUP BY date;")
    #zika_visits = cur.fetchall()
    #dates = column(h5n1_visits, 0)
    #h5n1 = column(h5n1_visits, 1)
    #mers = column(mers_visits, 1)
    #zika = column(zika_visits, 1)
    #chart3 = helpers.menu_visits_by_day(dates, h5n1, mers, zika)

    #Generate disease charts (tracking visits to overview and prevention information)
    public_diseases = ["h5n1", "mers", "zika"]
    for disease in public_diseases:
        menu_string = disease + "_menu"
        overview_string = disease + "_overview_menu"
        prevention_string = disease + "_prevention_menu"
        cur.execute("SELECT date, count(calls.call_id) FROM calls JOIN public_interactions ON calls.call_id = public_interactions.call_id WHERE date >=" + "'" + starting_date_string + "'" + " AND(" + menu_string + "=1 OR " + overview_string + "=1 OR " + prevention_string + "=2)" + duration_string + " GROUP BY date ORDER BY date desc;")
        overview_visits = cur.fetchall()
        cur.execute("SELECT date, count(calls.call_id) FROM calls JOIN public_interactions ON calls.call_id = public_interactions.call_id WHERE date >=" + "'" + starting_date_string + "'" + " AND(" + menu_string + "=2 OR " + overview_string + "=2 OR " + prevention_string + "=1)" + duration_string + " GROUP BY date ORDER BY date desc;")
        prevention_visits = cur.fetchall()
        dates = column(overview_visits, 0)
        overview = column(overview_visits, 1)
        prevention = column(prevention_visits, 1)
        disease_chart = helpers.overview_and_prevention_by_day(dates, overview, prevention, disease)
        charts.append(disease_chart)

    #Generate fourth chart (success rate of calls)
    #cur.execute("SELECT status, count(call_id) FROM calls WHERE type='public' GROUP BY status;")
    #statuses = cur.fetchall()
    #charts.append(helpers.calls_by_status(column(statuses, 0), column(statuses, 1)))

    #Generate fifth chart (public reports by day)
    cur.execute("SELECT date, count(calls.call_id) FROM calls JOIN public_interactions ON calls.call_id = public_interactions.call_id WHERE date >=" + "'" + starting_date_string + "'" + "AND public_report_confirmation='0'" + duration_string + " GROUP BY date ORDER BY date desc;")
    calls_by_date = cur.fetchall()
    dates = []
    numcalls = []
    for log in calls_by_date:
        dates = dates + [log[0]]
        numcalls = numcalls + [log[1]]
    charts.append(helpers.calls_by_day(dates, numcalls, "Public Reports by Day"))

    #Close database and render HTML template
    con.close()
    return render_template("public.html", name="", charts = charts)


@app.route("/hcreports")
def hcreports():
    #Load additional call logs if there are any and open database
    #loadData("rawwcallsyear.csv")
    #loadData("rawcalls.csv")
    con = sqlite3.connect("logs115.db")
    cur = con.cursor()
    #print pd.read_sql_query("SELECT week_id, count(call_id) FROM calls GROUP BY week_id ORDER BY week_id", con)

    #Generate first chart: attempted & completed HC reports by week
    cur.execute("SELECT week_id, count(calls.call_id) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE completed = 'true' GROUP BY week_id ORDER BY week_id asc;")
    completed_reports_by_week = cur.fetchall()
    cur.execute("SELECT week_id, count(calls.call_id) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id ORDER BY week_id asc;")
    attempted_reports_by_week = cur.fetchall()
    weeks = column(completed_reports_by_week, 0)
    completed = column(completed_reports_by_week, 1)
    attempted = column(attempted_reports_by_week, 1)
    chart2 = helpers.reports_by_week(weeks, completed, attempted, "HC Reports by Week (Completed vs Attempted)")

    #Generate second chart (line chart of cases of each disease by week)
    cur.execute("SELECT week_id, sum(diarrhea_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    diarrhea_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(fever_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    fever_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(flaccid_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    flaccid_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(respiratory_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    respiratory_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(dengue_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    dengue_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(meningitis_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    meningitis_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(jaundice_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    jaundice_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(diphteria_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    diphteria_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(rabies_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    rabies_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(neonatal_cases) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
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
    cur.execute("SELECT week_id, sum(diarrhea_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    diarrhea_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(fever_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    fever_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(flaccid_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    flaccid_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(respiratory_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    respiratory_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(dengue_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    dengue_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(meningitis_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    meningitis_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(jaundice_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    jaundice_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(diphteria_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    diphteria_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(rabies_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
    rabies_cases = cur.fetchall()
    cur.execute("SELECT week_id, sum(neonatal_deaths) FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id GROUP BY week_id;")
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
    return render_template("hcreports.html", name="", chart2=chart2, chart3=chart3, chart4=chart4)

    # Visualizations: Public - Calls by day, disease reports by day, visits to each disease menu by day, success rate of calls (last month)
    # Visualizations: HC Workers - Number of completed reports by week, cases of each disease by week, deaths from each disease by week, success rate of calls
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)