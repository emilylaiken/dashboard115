import html
import os
import plotly


def calls_by_type(hc_workers, public):
    figure = {
        "data": [
            {
                "labels": ["HC workers", "Public"],
                "hoverinfo": "none",
                "marker": {
                    "colors": [
                        "rgb(0,255,00)",
                        "rgb(255,0,0)",
                    ]
                },
                "type": "pie",
                "values": [hc_workers, public]
            }
        ],
        "layout": {
            "title": "Calls by Type (HC Worker vs Public)",
            "showlegend": True
            }
    }
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)

def calls_by_day(dates, call_totals, title):
    figure = {
        "data": [{
            'x': dates,
            'y': call_totals
        }],
        "layout": {
            "title": title,
            "showlegend": False
        }
    }
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)

def menu_visits_by_day(dates, h5n1, mers, zika):
    figure = {
        "data": [
            {'x': dates, 'y': h5n1, 'name': "H5N1"},
            {'x': dates, 'y': mers, 'name': "Mers"},
            {'x': dates, 'y': zika, 'name': "Zika"}
        ],
        "layout": {
            "title": "Visits to Each Public Disease Menu by Day",
            "showlegend": True,

        }
    }
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)

def calls_by_status(labels, data):
    figure = {
        "data": [
            {
                "labels": labels,
                "type": "pie",
                "values": [data[0], data[1], data[2], data[3]]
            }
        ],
        "layout": {
            "title": "Public calls by Status",
            "showlegend": True
        }
    }
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)


def reports_by_week(dates, completed, attempted, title):
    figure = {
        "data": [
            {'x': dates, 'y': completed, 'name': "Completed reports"},
            {'x': dates, 'y': attempted, 'name': "Attempted reports"},
        ],
        "layout": {
            "title": title,
            "showlegend": True,

        }
    }
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)

def case_reports_by_week(dates, diarrhea, fever, flaccid, respiratory, dengue, meningitis, jaundice, diphteria, rabies, neonatal, title):
    figure = {
        "data": [
            {'x': dates, 'y': diarrhea, 'name': "Diarrhea"},
            {'x': dates, 'y': fever, 'name': "Fever"},
            {'x': dates, 'y': flaccid, 'name': "Flaccid"},
            {'x': dates, 'y': respiratory, 'name': "Respiratory"},
            {'x': dates, 'y': dengue, 'name': "Dengue"},
            {'x': dates, 'y': meningitis, 'name': "Meningitis"},
            {'x': dates, 'y': jaundice, 'name': "Jaundice"},
            {'x': dates, 'y': diphteria, 'name': "Diphteria"},
            {'x': dates, 'y': rabies, 'name': "Rabies"},
            {'x': dates, 'y': neonatal, 'name': "Neonatal"}
        ],
        "layout": {
            "title": title,
            "showlegend": True,

        }
    }
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)


