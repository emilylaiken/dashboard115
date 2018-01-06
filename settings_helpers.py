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
def getDiseasePresences(all_diseases, chosen_diseases, hotline_type, years, cur):
    month_names = {1:'January', 2:'February', 3:'March', 4:'April', 5:'May', 6:'June', 7:'July', 8:'August', 9:'September', 10:'October', 11:'November', 12:'December'}
    disease_presences = []
    checked = {}
    for disease in sorted(all_diseases):
        if hotline_type == "public_interactions":
            disease_lst = [disease]
            disease_var_name = disease + "_menu"
        else:
            disease_lst = [disease, disease.split("_")[1] + " " + disease.split("_")[2]]
            disease_var_name = disease
        for year in years:
            year_str = []
            cur.execute("SELECT DISTINCT month FROM calls JOIN " + hotline_type + " ON calls.call_id = " + hotline_type + ".call_id WHERE year = " + str(year) + " AND " + disease_var_name + " IS NOT NULL;")
            months = cur.fetchall()
            months = ", ".join([month_names[int(month[0])] for month in months])
            disease_lst.append(months)
        # If disease is currently marked as to-be-viewed, mark it to be checked in the HTML template
        if disease in chosen_diseases:
            checked[disease] = 1
        else:
            checked[disease] = 0
        disease_presences.append(disease_lst)
    return disease_presences, checked



