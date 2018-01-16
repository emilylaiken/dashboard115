from __future__ import print_function
import sys
import csv
import sqlite3
import datetime
import helpers
import json

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

def insertCallLog(cur, call, calls_attributes, public_fields_available, hc_fields_available):
    # Get time and date from 'started' field
    dateTime = parseDateTime(call['Started'])
    date = dateTime[0]
    time = dateTime[1]
    # Calculate week ID (for grouping by weeks)
    day_of_week = datetime.datetime.strptime(date, '%Y-%m-%d').weekday()
    if day_of_week in [1, 2, 3]:
        days_since_wed = day_of_week + 5
    else:
        days_since_wed = day_of_week - 2
    week_id = datetime.datetime.strftime(datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(days=days_since_wed), '%y-%m-%d')
    datenum = helpers.dtoi(date)
    # Decide which type of call it is--HC worker or public
    call_type = 'public'
    if (call['level_worker'] == '2'):
        call_type = 'hc_worker'
    general_info = [(call['ID'], date, datenum, datenum[4:6], datenum[0:4], time, week_id, call['Duration(second)'], removeAnonymous(call['Caller ID']), call['Status'], call_type)]
    cur.executemany("INSERT INTO calls (" +  ", ".join(calls_attributes) + ") VALUES (" + ", ".join(["?" for atr in calls_attributes]) + ");", general_info)
    # Record disease report information--disease type and disease # inputs
    if (call_type == "hc_worker"):
        reports = ()
        report_something = "false"
        for var in hc_fields_available:
            if call[var] == "": # Did not enter any of this disease
                reports = reports + (0,)
            else: # Some of disease reported
                reports = reports + (deleteStar(call[var]),)
                report_something = "true"
        completed = "false"
        if ((call['cdc_report_started'] == '1' and call['cdc_report_ended'] == '1') or (call['cdc_report_started'] != '1' and report_something == "true")):
            completed = "true"
        to_db = [(call['ID'], call['Caller ID'], completed, week_id) + reports]
        hc_attributes = ['call_id', 'caller_id', 'completed', 'week_id'] + hc_fields_available
        cur.executemany("INSERT INTO hc_reports (" + ", ".join(hc_attributes) + ") VALUES (" + ", ".join(["?" for atr in hc_attributes]) + ");", to_db)
        #cur.execute("UPDATE hc_reports SET " +  ", ".join([field + " = 0" for field in hc_fields_available]) + " WHERE caller_id = " + call['Caller ID'] + " AND week_id = " + week_id + ";")
        # Record public interaction with menus
    else:
        disease_menus = ['hotline_menu', 'disease_menu'] + [disease + "_menu" for disease in public_fields_available]
        interaction = ()
        for menu in disease_menus:
            if call[menu] == "":
                interaction = interaction + (None,)
            else:
                interaction = interaction + (call[menu],)
        to_db = [(call['ID'],) + interaction]
        cur.executemany("INSERT INTO public_interactions (" + ", ".join(['call_id'] + disease_menus) + ") VALUES (" + ", ".join(["?" for atr in ['call_id'] + disease_menus]) + ");", to_db)


# Given the CSV file name, loads the call logs into memory (if they are not duplicates of previously loaded logs)
def loadData(data_file_name):
    # Check that all required variables are present
    con = sqlite3.connect("logs115.db")
    cur = con.cursor()
    calls_attributes = ['call_id', 'date', 'datenum', 'month', 'year', 'time', 'week_id', 'duration', 'caller_id', 'status', 'type']
    calls_attributes_types = {'call_id':'integer primary key', 'date':'varchar', 'datenum': 'integer', 'month': 'varchar', 'year':'varchar', 'time':'time', 'week_id':'varchar', 'duration':'integer', 'caller_id':'integer', 
                        'status':'varchar', 'type':'varchar'}
    req_attributes = ['ID', 'Started', 'Caller interaction', 'Duration(second)', 'Caller ID', 'Status', 'hotline_menu', 'disease_menu', 'level_worker', 'cdc_report_started', 'cdc_report_ended']
    # REFRESH
    #cur.execute("DROP TABLE calls;")
    #cur.execute("DROP TABLE hc_reports;")
    #cur.execute("DROP TABLE public_interactions;")
    #helpers.setDiseases([], [], [], [])
    with open(data_file_name, 'rU') as fin: 
        dr = csv.DictReader(fin) 
        for req_attribute in req_attributes:
            if req_attribute not in dr.fieldnames:
                return "Missing attribute: " + req_attribute, "", ""
        # Record which diseases are available, add to records if there are new ones
        hc_fields_available = []
        public_fields_available = []
        other_public_fields = ['welcome', 'hotline', 'disease', 'nchad']
        for field in dr.fieldnames:
            # Search for HC worker diseases--begin with 'va' and end with 'case' or 'death'
            if (field[-4:] == 'case' or field[-5:] == 'death') and field[:2] == 'va':
                hc_fields_available.append(field)
            # Search for public diseases--end with 'menu'
            elif field[-4:] == 'menu' and not field.split("_")[0] in other_public_fields and not field.split("_")[0] in public_fields_available:
                public_fields_available.append(field.split("_")[0])
        # Add new records to settings JSON
        all_public, chosen_public, all_hc, chosen_hc = helpers.getDiseases()
        new_public_diseases = [disease for disease in public_fields_available if disease not in all_public]
        new_hc_diseases = [disease for disease in hc_fields_available if disease not in all_hc]
        # Define attributes for each table
        hc_attributes = ['call_id', 'caller_id', 'completed', 'week_id'] + hc_fields_available
        hc_attributes_types = {}
        for atr in hc_attributes:
            if atr == 'call_id':
                hc_attributes_types[atr] = 'integer primary key'
            elif atr == 'completed' or atr == 'caller_id' or atr == 'week_id':
                hc_attributes_types[atr] = 'varchar'
            else:
                hc_attributes_types[atr] = 'integer'
        public_attributes = {'call_id':'integer primary key', 'hotline_menu':'integer', 'disease_menu':'integer'}
        for disease in public_fields_available:
            public_attributes[disease + '_menu'] = 'integer'
        # Create tables if needed, alter if new disease has been added
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calls';")
        tables = cur.fetchall()
        cur.execute("CREATE TABLE IF NOT EXISTS calls (" + ", ".join([atr + " " + calls_attributes_types[atr] for atr in calls_attributes]) + ");")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_date ON calls (datenum);")
        cur.execute("CREATE TABLE IF NOT EXISTS hc_reports (" + ", ".join([key + " " + value for key, value in hc_attributes_types.iteritems()]) + ");")
        cur.execute("CREATE TABLE IF NOT EXISTS public_interactions (" + ", ".join([key + " " + value for key, value in public_attributes.iteritems()]) + ");")        # Insert columns if there are any new diseases
        for disease in new_public_diseases:
            if tables != []:
                cur.execute("ALTER TABLE public_interactions ADD " + disease + "_menu integer;")
            all_public, chosen_public, all_hc, chosen_hc = helpers.setDiseases(all_public + [disease], chosen_public + [disease], all_hc, chosen_hc)
        for disease in new_hc_diseases:
            if tables != []:
                cur.execute("ALTER TABLE hc_reports ADD " + disease + " integer;")
            all_public, chosen_public, all_hc, chosen_hc = helpers.setDiseases(all_public, chosen_public, all_hc + [disease], chosen_hc + [disease])
        numInserted = 0
        numDuplicates = 0
        # Read in calls
        prev_date = ""
        week_id = ""
        for call in dr:
            # Record general info--call ID, date, time, caller ID, status, level of worker, and cdc report confirmations
            if call['ID'] == "": # If we are passed the end of the call records, stop
                break
            cur.execute("SELECT * FROM calls WHERE call_id = " + "'" + call['ID'] + "'");
            duplicate_calls = cur.fetchall()
            if len(duplicate_calls) == 0:
                insertCallLog(cur, call, calls_attributes, public_fields_available, hc_fields_available)
                numInserted = numInserted + 1
            else:
                numDuplicates = numDuplicates + 1
    con.commit()
    con.close()
    # Messages to print on HTML template: number of calls inserted/duplicates, new public diseases detected, new HC diseases detected
    num_loaded_msg = "Number of call logs successfully loaded: " + str(numInserted) + ". Number of duplicates (not loaded): " + str(numDuplicates)+ "."
    new_public_msg = ""
    if len(new_public_diseases) == 0:
        new_public_msg = "New public diseases detected: None."
    else:
        new_public_msg = "New public diseases detected: " + str.title(", ".join(new_public_diseases)) + "."
    new_hc_msg = ""
    if len(new_hc_diseases) == 0:
        new_hc_msg = "New HC diseases detected: None."
    else:
        hc_disease_titles = [str.title(disease.split('_')[1] + " " + disease.split('_')[2]) for disease in new_hc_diseases]
        new_hc_msg = "New public diseases detected: " + str.title(", ".join(hc_disease_titles)) + "."
    return num_loaded_msg, new_public_msg, new_hc_msg

