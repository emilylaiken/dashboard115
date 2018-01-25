from __future__ import print_function
import sqlite3
import datetime
from flask import Flask, redirect, render_template, request, url_for, send_file, session
import chartmaker
import sys
import helpers
import datetime
import collections

# Color palette for graphs
palette = ["#147a14", "#ff6b6b", "#43b2ab", "#dbc65e", "#4f545a", "#59344f", "#eb8258", "#6689a1", "#9dad6f", "#7d6d61"]

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

# Wrapper for line chart that is used to build ontime vs. late chart used on HC reports page
def hcOntimeChart(cur, starting_date_string, ending_date_string, target):
    subquery2 = "SELECT DISTINCT calls.week_id as week2 FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "'" + " GROUP BY calls.week_id ORDER BY calls.week_id asc"
    subquery1_completed = "SELECT calls.week_id as week1, count(calls.call_id) as count FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE (datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "')" + "AND ((CAST(strftime('%w', date) as integer) == 2 OR CAST(strftime('%w', date) as integer) == 3)) GROUP BY calls.week_id ORDER BY calls.week_id asc"
    subquery1_attempted = "SELECT calls.week_id as week1, count(calls.call_id) as count FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE (datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "')" + "AND ((CAST(strftime('%w', date) as integer) < 2 OR CAST(strftime('%w', date) as integer) > 3)) GROUP BY calls.week_id ORDER BY calls.week_id asc"
    cur.execute("SELECT * FROM (" + subquery2 + ") LEFT OUTER JOIN (" + subquery1_completed + ") ON week1 = week2;")
    completed_reports_by_week = cur.fetchall()
    cur.execute("SELECT * FROM (" + subquery2 + ") LEFT OUTER JOIN (" + subquery1_attempted + ") ON week1 = week2;")
    attempted_reports_by_week = cur.fetchall()
    weeks = column(completed_reports_by_week, 0)
    completed = column(completed_reports_by_week, 2)
    completed = [entry if entry is not None else 0 for entry in completed]
    attempted = column(attempted_reports_by_week, 2)
    attempted = [entry if entry is not None else 0 for entry in attempted]
    if target[-4:] == '.pdf':
        pdf = chartmaker.lineChartDownload(weeks, [completed, attempted], ["On-Time Reports", "Late Reports"], palette[0:2], "HC Reports by Week - On-Time vs. Late", None, None, None, None, target)
    else:
        return lineChart([helpers.toWordDate(week) for week in weeks], [completed, attempted], ["On-Time Reports", "Late Reports"], palette[0:2], "HC Reports by Week - On-Time vs. Late", True, "None", "None", "Date (Beginning of Week)", target) + ("", "")

# Wrapper for line chart used to build two HC reports charts (one for cases, one for deaths) on HC reports page
def hcDiseaseChart(cur, starting_date_string, ending_date_string, addon, target):
    series = []
    # Initialize empty dictionary to hold reports
    reports = collections.OrderedDict()
    _, _, _, hc_diseases = helpers.getDiseases()
    diseases = [disease for disease in hc_diseases if addon in disease]
    for disease in sorted(diseases):
        reports[disease] = []
    reports['dates'] = []
    # Query database for sum of reports of each disease eah week
    cur.execute("SELECT calls.week_id, " + ", ".join(["sum(" + disease + ")" for disease in diseases]) + " FROM calls JOIN hc_reports ON calls.call_id = hc_reports.call_id WHERE datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "'" + " GROUP BY calls.week_id;")
    weeks = cur.fetchall()
    # Write sums from SQL query into database
    for week in weeks:
        reports['dates'].append(week[0])
        for i in range (0, len(diseases)):
            reports[diseases[i]].append(week[i+1])
    series, labels, colors = [], [], []
    i = 0
    for key, value in reports.items():
        if key != 'dates':
            series.append(value)
            labels.append(key.split("_")[1].title())
            colors.append(palette[i])
            i = i+1
    if target[-4:] == '.pdf':
        pdf = chartmaker.lineChartDownload(reports['dates'], series, labels, colors, "Reports of Disease " + addon[1:].title() + "s by Week", None, None, None, None, target)
    else:
        return lineChart([helpers.toWordDate(week) for week in reports['dates']], series, labels, colors, "Reports of Disease " + addon[1:].title() + "s by Week", True, "None", "None", "Date (Beginning of Week)", target) + ("", "")


# Wrapper for line chart used to build all-calls chart on overview page and all charts on public page
def publicLineChart(cur, table, condition_strings, starting_date_string, ending_date_string, duration_string, seriesnames, title, legend, target):
    series = []
    colors = []
    dates = []
    for i in range (0, len(condition_strings)):
        # Generate SQL
        condition_string = condition_strings[i]
        if table == "all":
            from_string = "calls"
        elif table == "public":
            from_string = "calls JOIN public_interactions ON calls.call_id = public_interactions.call_id"
        elif table == "hc_reports":
            from_string = "calls JOIN hc_reports ON calls.call_id = hc_reports.call_id"
        filter_string = " datenum >=" + "'" + helpers.dtoi(starting_date_string) + "'" " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "'" + duration_string + " "
        subquery = "SELECT date as date1, count(calls.call_id) as count FROM " + from_string + " WHERE " + condition_string + " AND " + filter_string + "GROUP BY date ORDER BY date asc"
        subquery2 = "SELECT DISTINCT date as date2 FROM " + from_string + " WHERE " + filter_string
        chart_sql = "SELECT * FROM (" + subquery2 + ") LEFT OUTER JOIN (" + subquery + ") ON date1 = date2;"
        #print(chart_sql)
        cur.execute(chart_sql)
        calls_by_date = cur.fetchall()
        # Translate SQL query into series of dates and series of data
        numcalls = []
        for log in calls_by_date:
            if i == 0:
                dates = dates + [log[0]]
            if log[2] is not None:
                numcalls = numcalls + [log[2]]
            else:
                numcalls = numcalls + [0]
        series.append(list(numcalls))
        colors.append(palette[i])
        # Calculate total and average to go along with chart
        if i == 0:
            total = sum(numcalls)
            if total == 0:
                avg = 0
            else:
                avg = sum(numcalls) / len(numcalls)
    if target[-4:] == ".pdf":
        pdf = chartmaker.lineChartDownload(list(dates), series, seriesnames, colors, title, starting_date_string, ending_date_string, total, avg, target)
        return
    else:
        return lineChart(list(dates), series, seriesnames, colors, title, legend, starting_date_string, ending_date_string, "None", target) + (total, avg)

# Calls charts.js script to build a line chart given raw data series and layout info
def lineChart(labels, data, seriesnames, colors, title, legend, minx, maxx, xlabel, canvasid):
    type_str = '"line"'
    # Each individual label is given as a list, meaning it must be structured for string wrapping
    labels_str = "[" + ", ".join(['"' + str(label) + '"' for label in labels]) + "]"
    data_str = "[" + ", ".join(["[" + ", ".join([str(point) for point in series]) + "]" for series in data]) + "]"
    seriesnames_str = '[' + ", ".join(['"' + name + '"' for name in seriesnames]) + ']'
    colors_str = '[' + ", ".join(['"' + color + '"' for color in colors]) + ']'
    title_str = '"' + title + '"'
    if legend:
        legend_str = '"True"'
    else:
        legend_str = '"False"'
    minx_str, maxx_str = '"' + minx + '"', '"' + maxx + '"'
    xlabel_str = '"' + xlabel + '"'
    canvasid_str = '"' + canvasid + '"'
    javascript_func = "setUpChart(" + type_str + ", " + labels_str + ", " + data_str + ", " + seriesnames_str + ", " + colors_str + ", " +  title_str + ", " + legend_str + ", " + minx_str + ", " + maxx_str + ", " + xlabel_str + ", " + canvasid_str +  ");"
    return canvasid_str, javascript_func

# Wrapper for pie charts used to break down actions of users to portion of hotline
def hotlineBreakdown(cur, table, labels, condition_strings, starting_date_string, ending_date_string, duration_string, title, target):
    if table == "all":
        from_string = "calls"
    elif table == "public":
        from_string = "calls JOIN public_interactions ON calls.call_id = public_interactions.call_id"
    elif table == "hc_reports":
        from_string = "calls JOIN hc_reports ON calls.call_id = hc_reports.call_id"
    filter_string = " datenum >=" + "'" + helpers.dtoi(starting_date_string) + "'" " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "'" + duration_string + " "
    values = []
    num_accounted_for = 0
    for condition_string in condition_strings:
        cur.execute("SELECT COUNT(*) FROM " + from_string + " WHERE " + condition_string + " AND " + filter_string + ";")
        value = cur.fetchall()
        values.append(value[0][0])
        num_accounted_for = num_accounted_for + value[0][0]
    # Get total
    cur.execute("SELECT COUNT(*) FROM " + from_string + " WHERE " + filter_string + ";")
    total = cur.fetchall()
    dif = total[0][0] - num_accounted_for
    if dif != 0:
        values.append(dif)
        labels.append('No Action')
    if target[-4:] == '.pdf':
        pdf = chartmaker.pieChartDownload(labels, values, palette[0:len(values)], title, target)
        return
    else:
        return pieChart(labels, values, palette[0:len(values)], title, target) + ("", "")

# Wrapper for pie chart used to build charts describing percentages of calls in each status
def statusChart(cur, table, starting_date_string, ending_date_string, duration_string, target):
    data = []
    statuses = ['completed', 'incompleted', 'terminated']
    if table == 'public':
        table_name = "public_interactions"
    else:
        table_name = "hc_reports"
    for status in statuses:
        cur.execute("SELECT count(calls.call_id) FROM calls JOIN " + table_name + " ON calls.call_id = " + table_name + ".call_id WHERE datenum >= " + "'" + helpers.dtoi(starting_date_string) + "'" + " AND datenum <= " + "'" + helpers.dtoi(ending_date_string) + "'" + duration_string + " AND status == '" + unicode(status) + "';")
        calls_by_status = cur.fetchall()
        data.append(calls_by_status[0][0])
    if target[-4:] == '.pdf':
        pdf = chartmaker.pieChartDownload([status.title() for status in statuses], data, palette[0:len(statuses)], "Calls by Status - " + table.title(), target)
    else:
        return pieChart([status.title() for status in statuses], data, palette[0:len(statuses)], "Calls by Status - " + table.title(), target) + ("", "")

# Calls charts.js script to build a pie chart given raw data series and layout info
def pieChart(labels, data, colors, title, canvasid):
    type_str = '"pie"'
    labels_str = "[" + ", ".join(['"' + str(label) + '"' for label in labels]) + "]"
    data_str = "[" + ", ".join([str(point) for point in data]) + "]"
    seriesnames_str = "[]"
    legend_str = '"False"'
    minx_str, maxx_str = '"None"', '"None"'
    colors_str = '[' + ", ".join(['"' + color + '"' for color in colors]) + ']'
    title_str = '"' + title + '"'
    xlabel_str = '"None"'
    canvasid_str = '"' + canvasid + '"'
    javascript_func = "setUpChart(" + type_str + ", " + labels_str + ", " + data_str + ", " + seriesnames_str + ", " + colors_str + ", " +  title_str + ", " + legend_str + ", " + minx_str + ", " + maxx_str + ", " + xlabel_str + ", " + canvasid_str +  ");"
    return canvasid_str, javascript_func
