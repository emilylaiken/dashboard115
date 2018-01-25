from __future__ import print_function
import sys
import sqlite3
import datetime
import json
from flask import Flask, redirect, render_template, request, url_for, send_file, session
import helpers

# Used to set which diseases are currently available: which public and HC diseases are options, as well as which ones are currently selected to be viewed
def setDiseases(all_public, chosen_public, all_hc, chosen_hc):
    vars = ['all_public', 'chosen_public', 'all_hc', 'chosen_hc']
    with open('settings.json', 'w') as outfile:
        json.dump({'all_public':all_public, 'chosen_public':chosen_public, 'all_hc':all_hc, 'chosen_hc':chosen_hc}, outfile)
    return helpers.getDiseases()

# Searches database for available diseases (HC or public) and when they were used
def getDiseasePresences(all_diseases, chosen_diseases, hotline_type, cur):
    month_names = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'June', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
    disease_presences = []
    checked = {}
    for disease in sorted(all_diseases):
        if hotline_type == "public_interactions":
            disease_lst = [disease]
            disease_var_name = disease + "_menu"
            disease_lst.append(disease_var_name)
        else:
            disease_lst = [disease, disease.split("_")[1] + " " + disease.split("_")[2]]
            disease_var_name = disease
        # Get unique pairs of month and year for the disease
        if hotline_type == "public_interactions":
            nonexist_indicator = "IS NOT NULL"
        else:
            nonexist_indicator = "!= 0"
        cur.execute("SELECT DISTINCT month, year FROM calls JOIN " + hotline_type + " ON calls.call_id = " + hotline_type + ".call_id WHERE " + disease_var_name + " " + nonexist_indicator + " ORDER BY YEAR;")
        yearmonths = cur.fetchall()
        # Dictionary to hold lists of months in which disease is reported for each year, initialized to empty
        yeardict = {}
        for year in helpers.years():
            yeardict[str(year)] = []
        # Fill dictionary based on data from query
        for month, year in yearmonths:
            yeardict[str(year)].append(month)
        # Flatten dictionary into list
        for year in helpers.years():
            disease_lst.append(", ".join([month_names[int(month)] for month in yeardict[str(year)]]))
        disease_presences.append(disease_lst)
        # If disease is currently marked as to-be-viewed, mark it to be checked in the HTML template
        if disease in chosen_diseases:
            checked[disease] = 1
        else:
            checked[disease] = 0
    return disease_presences, checked



