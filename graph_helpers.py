from __future__ import print_function
import sqlite3
import datetime
from flask import Flask, redirect, render_template, request, url_for, send_file, session
import chartmaker
import sys
import helpers
import datetime


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

# Generates the SQL query on a given date, duration, and additional constraints. Only for single-series charts.
def generateSQL(table, starting_date_string, ending_date_string, duration_string, condition_string):
    if table == "all":
        from_string = "calls"
    elif table == "public":
        from_string = "calls JOIN public_interactions ON calls.call_id = public_interactions.call_id"
    elif table == "hc_reports":
        from_string = "calls JOIN hc_reports ON calls.call_id = hc_reports.call_id"
    filter_string = " datenum >=" + "'" + helpers.dtoi(starting_date_string) + "'" " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "'" + duration_string + " "
    chart_sql = "SELECT date, count(calls.call_id) as count FROM " + from_string + " WHERE " + condition_string + " AND " + filter_string + "GROUP BY date ORDER BY date desc"
    total_sql = "SELECT count(calls.call_id) FROM " + from_string + " WHERE " + condition_string + " AND " + filter_string
    avg_sql = "SELECT avg(count) FROM (" + chart_sql + ")"
    return (chart_sql, total_sql, avg_sql)

# Given three SQL statements (one for the chart, one for the total, and one for the average), executes the SQL statements and calls the helper chart function to create the figure
def generateFigures(chart_sql, total_sql, avg_sql, title, daterange, cur):
    num_days = (datetime.datetime.strptime(request.args.get('dateend'), '%Y-%m-%d') - datetime.datetime.strptime(request.args.get('datestart'), '%Y-%m-%d')).days + 1
    cur.execute(chart_sql)
    calls_by_date = cur.fetchall()
    dates = []
    numcalls = []
    for log in calls_by_date:
        dates = dates + [log[0]]
        numcalls = numcalls + [log[1]]
    chart = chartmaker.calls_by_day(dates, numcalls, title, daterange)
    # Total
    cur.execute(total_sql)
    totals = cur.fetchall()
    total = totals[0][0]
    # Average
    avg = total/num_days
    return (chart, total, avg)

# Same as the above function, but the chart created by this function is downloadable
def generateFiguresDownload(chart_sql, total_sql, avg_sql, title, filename, numdays, daterange):
    con = sqlite3.connect('logs115.db')
    cur = con.cursor()
    cur.execute(chart_sql)
    calls_by_date = cur.fetchall()
    dates = []
    numcalls = []
    for log in calls_by_date:
        dates = dates + [log[0]]
        numcalls = numcalls + [log[1]]
    chart = chartmaker.calls_by_day_offline(dates, numcalls, title, filename, daterange)
    # Total
    cur.execute(total_sql)
    totals = cur.fetchall()
    total = totals[0][0]
    # Average by day
    avg = total/numdays
    con.close()
    return (total, avg)

# Calls generateFigures to add single-series figure to the page's list of figures
def addFigure(condition_string, table, title, charts, totals, averages, cur):
    duration_string, title_addon = parseDuration(request.args.get('durationstart'), request.args.get('durationend'))
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    chart_sql, total_sql, avg_sql = generateSQL(table, starting_date_string, ending_date_string, duration_string, condition_string)
    chart, total, avg = generateFigures(chart_sql, total_sql, avg_sql, title + title_addon, [starting_date_string, ending_date_string], cur)
    charts.append(chart)
    totals.append(total)
    averages.append(avg)
    return charts, totals, averages

# Adds multi-series public disease figure to the page's list of figures
def addDiseaseFigures(diseases, charts, totals, averages, cur):
    duration_string, title_addon = parseDuration(request.args.get('durationstart'), request.args.get('durationend'))
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    num_days = (datetime.datetime.strptime(request.args.get('dateend'), '%Y-%m-%d') - datetime.datetime.strptime(request.args.get('datestart'), '%Y-%m-%d')).days + 1
    for i in range (0, len(diseases)):
        disease = diseases[i]
        menu_string = disease + "_menu"
        condition_string_all = menu_string + " IS NOT NULL"
        condition_string_overview = menu_string + "=1"
        condition_string_prevention = menu_string + "=2"
        chart_sql_all, total_sql_all, avg_sql_all = generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string_all)
        chart_sql_overview, total_sql_overview, avg_sql_overview = generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string_overview)
        chart_sql_prevention, total_sql_prevention, avg_sql_prevention = generateSQL("public", starting_date_string, ending_date_string, duration_string, condition_string_prevention)
        cur.execute(chart_sql_all)
        all_visits = cur.fetchall()
        cur.execute(chart_sql_overview)
        overview_visits = cur.fetchall()
        cur.execute(chart_sql_prevention)
        prevention_visits = cur.fetchall()
        dates = column(overview_visits, 0)
        all = column(all_visits, 1)
        overview = column(overview_visits, 1)
        prevention = column(prevention_visits, 1)
        disease_chart = chartmaker.overview_and_prevention_by_day(dates, all, overview, prevention, str.title(diseases[i]) + title_addon, [starting_date_string, ending_date_string])
        charts.append(disease_chart)
        #Total visits to menu
        cur.execute(total_sql_all)
        total = cur.fetchall()
        totals.append(total[0][0])
        #Average visits to menu
        averages.append(total[0][0]/num_days)
    return charts, totals, averages

# Adds multi-serires HC reports figure to the page's list of figures
def addHCReportChart(condition_strings, title, cur):
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    series = []
    for condition_string in condition_strings:
        cur.execute("SELECT week_id, sum(" + condition_string + ") FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "'" + " GROUP BY week_id;")
        series.append(cur.fetchall())
    dates = column(series[1], 0)
    series = [column(serie, 1) for serie in series]
    return chartmaker.case_reports_by_week(condition_strings, dates, series, title)

# Adds multi-series completed vs. attempted figure to the page's list of figures
def addOnTimeChart(table, title, cur):
    print("HEREE")
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    cur.execute("SELECT week_id, count(calls.call_id) FROM " + table + " WHERE (datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "')" + "AND ((CAST(strftime('%w', date) as integer) == 2 OR CAST(strftime('%w', date) as integer) == 3)) GROUP BY week_id ORDER BY week_id asc;")
    completed_reports_by_week = cur.fetchall()
    cur.execute("SELECT week_id, count(calls.call_id) FROM " + table + " WHERE (datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "')" + "AND ((CAST(strftime('%w', date) as integer) < 2 OR CAST(strftime('%w', date) as integer) > 3)) GROUP BY week_id ORDER BY week_id asc;")
    attempted_reports_by_week = cur.fetchall()
    weeks = column(completed_reports_by_week, 0)
    completed = column(completed_reports_by_week, 1)
    attempted = column(attempted_reports_by_week, 1)
    return chartmaker.reports_by_week(weeks, completed, attempted, title)

# Adds multi-series completed vs. attempted figure to the page's list of figures
def addCompletedAttemptedChart(charts, totals, averages, cur):
    starting_date_string = request.args.get('datestart')
    ending_date_string = request.args.get('dateend')
    duration_string, title_addon = parseDuration(request.args.get('durationstart'), request.args.get('durationend'))
    data_public = []
    data_hc = []
    statuses = ['incompleted', 'completed', 'terminated']
    for status in statuses:
        cur.execute("SELECT count(calls.call_id) FROM calls JOIN public_interactions ON calls.call_id = public_interactions.call_id WHERE datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "'" + duration_string + " AND status == '" + unicode(status) + "';")
        calls_by_status_public = cur.fetchall()
        data_public.append(calls_by_status_public[0][0])
        cur.execute("SELECT count(calls.call_id) AS count FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "'" + duration_string + " AND status == '" + unicode(status) + "';")
        calls_by_status_hc = cur.fetchall()
        data_hc.append(calls_by_status_hc[0][0])
    charts.append(chartmaker.calls_by_status(statuses, data_public, data_hc, "Calls by Status" + title_addon))
    totals.append(None)
    averages.append(None)
    return charts, totals, averages



