from __future__ import print_function
import sys
import csv
import sqlite3
import datetime

# Checks if the uploaded file is a CSV
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in set(['csv'])

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