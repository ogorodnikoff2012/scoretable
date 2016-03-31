#!/usr/bin/env python3
import requests
import json
import cgi

# -----------------------------------------------------------------------------
# Name:        html_table_parser
# Purpose:     Simple class for parsing an (x)html string to extract tables.
#              Written in python3
#
# Author:      Josua Schmid
#
# Created:     05.03.2014
# Copyright:   (c) Josua Schmid 2014
# Licence:     AGPLv3
# -----------------------------------------------------------------------------

from html.parser import HTMLParser


class HTMLTableParser(HTMLParser):
    """ This class serves as a html table parser. It is able to parse multiple
    tables which you feed in. You can access the result per .tables field.
    """
    def __init__(
        self,
        decode_html_entities=False,
        data_separator=' ',
    ):

        HTMLParser.__init__(self)

        self._parse_html_entities = decode_html_entities
        self._data_separator = data_separator

        self._in_td = False
        self._in_th = False
        self._current_table = []
        self._current_row = []
        self._current_cell = []
        self.tables = []

    def handle_starttag(self, tag, attrs):
        """ We need to remember the opening point for the content of interest.
        The other tags (<table>, <tr>) are only handled at the closing point.
        """
        if tag == 'td':
            self._in_td = True
        if tag == 'th':
            self._in_th = True

    def handle_data(self, data):
        """ This is where we save content to a cell """
        if self._in_td or self._in_th:
            self._current_cell.append(data.strip())

    def handle_charref(self, name):
        """ Handle HTML encoded characters """

        if self._parse_html_entities:
            self.handle_data(self.unescape('&#{};'.format(name)))

    def handle_endtag(self, tag):
        """ Here we exit the tags. If the closing tag is </tr>, we know that we
        can save our currently parsed cells to the current table as a row and
        prepare for a new row. If the closing tag is </table>, we save the
        current table and prepare for a new one.
        """
        if tag == 'td':
            self._in_td = False
        elif tag == 'th':
            self._in_th = False

        if tag in ['td', 'th']:
            final_cell = self._data_separator.join(self._current_cell).strip()
            self._current_row.append(final_cell)
            self._current_cell = []
        elif tag == 'tr':
            self._current_table.append(self._current_row)
            self._current_row = []
        elif tag == 'table':
            self.tables.append(self._current_table)
            self._current_table = []

# -----------------------------------------------------------------------------

# Useful constants
form = cgi.FieldStorage()
statement_id = form.getvalue("statement_id") or "10565"

group_id = form.getvalue("group_id") or "5078"

t = requests.get("http://informatics.mccme.ru/moodle/ajax/ajax.php?problem_id=0&group_id=" + group_id + "&user_id=0&lang_id=-1&status_id=-1&statement_id=" + statement_id + "&objectName=submits&count=5000&with_comment=&page=0&action=getHTMLTable").text

html = "<html><head><meta charset='utf-8'\></head><body><table" + json.loads(t).get("result").get("text").split("table")[1] + "table></body></html>"

p = HTMLTableParser()
p.feed(html)

table = dict()
tasks = set()

for row in p.tables[0]:
    name =  row[-8]
    task =  row[-7]
    try:
        score = int(row[-2])
    except:
        score = 0
    if name not in table:
        table[name] = dict()
    table[name][task] = max(table[name].get(task, 0), score)
    tasks.add(task)

task_scores = dict()
for v in table.values():
    for task, score in v.items():
        task_scores[task] = task_scores.get(task, 0) + score

def cell(x, center=False):
    print("<td>", "<center>" if center else "", x, "</center>" if center else "", "</td>")

def begin_row(*args):
    print("<tr class='", "odd" if odd else "even", ' '.join(map(str, args)), "'>")

def switch_row():
    global odd
    odd = not odd

def end_row():
    print("</tr>")

tasks = sorted(tasks)

print("Content-type: text/html\n")

print("""
<html>
    <head>
        <title>Score table</title>
        <meta charset='utf-8'/>
        <link href='../style.css' rel='stylesheet' type='text/css'>
        <link rel="shortcut icon" href="../favicon.png" type="image/png">
        <script src='../jquery-2.2.2.min.js'></script>
        <script src='../script.js'></script>
    </head>
    <body>
        <table>""")

odd = True

begin_row()
cell("")
cell("Task name:")
for task in tasks:
    cell(task)
cell("Sum")
end_row()

counter = 0
last_sum = 0
for k, v in sorted(table.items(), key=(lambda x: -sum(x[1].values()))):
    s = sum(v.values())
    if s != last_sum:
        switch_row()
    last_sum = s
    if k == "Владимир Огородников":
        begin_row("me")
    else:
        begin_row()
    counter += 1
    cell(counter)
    cell(k)
    for task in tasks:
        x = v.get(task, 0)
        cell(x, True)
    cell(s, True)
    end_row()

switch_row()
begin_row()
cell("")
cell("Average:")
avg_sum = 0
for task in tasks:
    s = task_scores.get(task, 0) / max(len(table), 1)
    cell("%.3f" % s)
    avg_sum += s

cell("%.3f" % avg_sum)
end_row()

print("</table></body></html>")

