#!/usr/bin/python
# This can be used as either a cgi program or from the command line
from __future__ import print_function
import argparse
import afal
import cgi
import cgitb

def print_debt(l, tf, p):
    l1 = len(l)
    s = 0
    d={}
    needorder = False
    needshare = False
    needinitial = False
    for i in l:
        s += i['owed_cp']
        ch = afal.get_char_name(i[tf])
        if ch not in d:
            d[ch] = {'sum':0, 'n':0}
        d[ch]['sum'] += i['owed_cp']
        n = d[ch]['n']
        d[ch][n] = {}
        d[ch][n]['amount'] = afal.str_cp(i['owed_cp'])
        d[ch][n]['date'] = i['date']
        if i['order'] != 0:
            d[ch][n]['order'] = str(i['order'])
            needorder = True
        if i['share'] != 1.0 :
            d[ch][n]['share'] = str(i['share'])
            needshare = True
        if i['item'] is not None:
            d[ch][n]['item'] = afal.get_item_name(i['item'])
        if i['initial_cp'] != i['owed_cp']:
            d[ch][n]['initial'] = afal.str_cp(i['initial_cp'])
            needinitial = True
        n += 1
        d[ch]['n'] = n

    s = afal.str_cp(s)
    if text:
        print('  ', l1, ' ', p, ' Debts (Total ', s, ')', sep='')
    else:
        print("<h3>",l1, ' ', p, ' Debts (Total ', s, ')</h3>', sep='')
        print('<table border="1"><tr><th>Who</th><th>Date</th><th>Amount</th>', end='')
        if needinitial:
            print('<th>Initial</th>',end='')
        if needshare:
            print('<th>Share</th>',end='')
        if needorder:
            print('<th>Order</th>',end='')
        print('<th>Item</th></tr>')
    k = d.keys()
    k.sort()
    for i in k:
        if text:
            print('    ', i, ' ', sep='')
            for j in range(d[i]['n']):
                initial = ''
                if 'initial' in d[i][j]:
                    initial = ' of ' + d[i][j]['initial']
                order = ''
                if 'order' in d[i][j]:
                    order = ' repay order ' + d[i][j]['order']
                share = ''
                if 'share' in d[i][j]:
                    share = ' for ' + d[i][j]['share'] + ' share'
                item = ''
                if 'item' in d[i][j]:
                    item = ' for ' + d[i][j]['item']
                print('      ', d[i][j]['date'], '  ', d[i][j]['amount'], initial, order, share, item, sep='')
        else:
            if d[i]['n'] > 1:
                t1 = '<tr><td rowspan="' + str(d[i]['n']) + '">(' + str(d[i]['n']) + ') ' + i + ' (Total ' +  afal.str_cp(d[i]['sum']) + ')</td>'
                t2 = '<tr>'
            else:
                t1='<tr><td>' + i + '</td>'
                t2 = '<tr>'
            for j in range(d[i]['n']):
                initial = ''
                if 'initial' in d[i][j]:
                    initial = d[i][j]['initial']
                order = ''
                if 'order' in d[i][j]:
                    order = d[i][j]['order']
                share = ''
                if 'share' in d[i][j]:
                    share = d[i][j]['share']
                item = ''
                if 'item' in d[i][j]:
                    item = d[i][j]['item']
                print(t1, '<td>', d[i][j]['date'], '</td><td>',
 d[i][j]['amount'], '</td>', sep='', end='')
                if needinitial:
                    print('<td>', initial, '</td>',sep='',end='')
                if needshare:
                    print('<td>', share, '</td>',sep='',end='')
                if needorder:
                    print('<td>', order, '</td>',sep='',end='')
                print('<td>', item, '</td></tr>', sep='', end='')
                t1 = t2
            print('</tr>')
    if text:
        print()
    else:
        print('</table>')


parser = argparse.ArgumentParser('Generate a report')
parser.add_argument('--text', '-t', help='text, not CGI', action='store_true', default=False)
parser.add_argument('--all', '-a', help='report on everything', action='store_true', default=False)
parser.add_argument('--character', '-c', help='report on this character', default=None)
parser.add_argument('--party', '-p', help='report on this party', default=None)
parser.add_argument('--journal-start', '-j', help='display the transaction journal starting from this date', default=None)
parser.add_argument('--journal-end', '-k', help='display the transaction journal up to this date', default = None)
args=parser.parse_args()

tmp = afal.get_characters()
character_list = []
for i in tmp:
    character_list.append(i[1])

tmp = afal.get_parties()
party_list = []
for i in tmp:
    party_list.append(i[1])

journal_list = afal.get_journal_dates()

text = args.text
chars = []
parties = []
party_name = None
journal_start = None
journal_end = None
if text:
    if args.all:
        chars = character_list
        parties = party_list
        journal_start = journal_list[0]
        jounal_end = journal_list[-1]
    elif args.character is not None:
        chars = [args.character]
    elif args.party is not None:
        parties = [args.party]
    elif args.journal_start is not None:
        journal_start = args.journal_start
    elif args.journal_end is not None:
        journal_end = args.journal_end
    else:
        print("Dunno what to do")
        chars = character_list
        parties = party_list
        journal_start = journal_list[0]
        jounal_end = journal_list[-1]
else:
    cgitb.enable()
    print("""Content-Type: text/html

<html>
<head><title>AFAL Finance Report</title></head>
<body background="http://flockhart.virtualave.net/afal/back3l07.gif">
  <center>
    <b>Select a character:</b><br />
    <form action="report.cgi" method="GET">
      <select name="char_name">
        <option value="All">All</option>""")
    for i in character_list:
        print('        <option value="%s">%s</option>' % (i, i))
    print("""      </select>
      <input type="submit" name="generate" value="Character" />
    </form>
    <br><b>or Select a party:</b><br>
    <form action="report.cgi" method="GET">
      <select name="party_name">
        <option value="All">All</option>""")
    for i in party_list:
        print('        <option value="%s">%s</option>' % (i, i))
    print("""      </select>
      <input type="submit" name="generate" value="Party" />
    </form>""")
    print("    <br><b>or select a journal range</b><br>")
    print('    <form action="report.cgi" method="GET">')

    print('      <select name="journal_start">')
    print('        <option value="All">All</option>')
    for i in journal_list:
        print('        <option value="%s">%s</option>' % (i, i))
    print('      </select>')

    print('      <select name="journal_end">')
    print('        <option value="All">All</option>')
    for i in journal_list:
        print('        <option value="%s">%s</option>' % (i, i))
    print('      </select>')

    print('      <input type="submit" name="generate" value="Journal" />')
    print("    </form>""")
    form = cgi.FieldStorage()
    todo = form.getfirst("generate","")
    if todo == 'Character':
        char_name = form.getfirst("char_name","")
        if char_name == 'All':
            chars = character_list
        else:
            chars = [char_name]
    elif todo == 'Party':
        party_name = form.getfirst("party_name","")
        if party_name == 'All':
           parties = party_list
        else:
            parties = [party_name]
    elif todo == 'Journal':
        journal_start = form.getfirst("journal_start","")
        if journal_start == 'All':
            journal_start = journal_list[0]
        journal_end = form.getfirst("journal_end","")
        if journal_end == 'All':
            journal_end = journal_list[-1]

if len(chars) > 1:
    if text:
        print('        Characters\n')
    else:
        print('<h3>Characters</h3><br>')
for char_name in chars:
    char_id = afal.get_char_id(char_name)
    cash = afal.get_char_cash(char_id)
    items = afal.get_items_owned_by(char_id)
    cparties = afal.get_char_parties(char_id)
    payable = afal.get_char_payable(char_id)
    receivable = afal.get_char_receivable(char_id)
    if text:
        if cash > 0 :
            print(char_name, " cash ", afal.str_cp(cash), "\n", sep='')
        else :
            print(char_name, "\n", sep='')
    else:
        print('<h4>', char_name, '</h4>', sep='')
        if cash > 0:
            print('<h5>Cash ', afal.str_cp(cash), '</h5><br>', sep='')
        else:
            print('<br>')
    if len(cparties) :
        needshare = False
        for i in cparties :
            if i[1] != 1.0 :
                needshare = True
                break
        if text:
            print('  ', str(len(cparties)), ' Parties', sep='')
        elif needshare:
            print('<table border=1><tr><th>Party</th><th>Share</th><th>Items</th></tr>')
        else:
            print('<table border=1><tr><th>Party</th><th>Items</th></tr>')
        for i in cparties :
            pitems = afal.get_items_acquired_by(i[0])
            if text:
                s1=''
                if i[1] != 1.0 :
                    s1 += ' for ' + str(i[1]) + ' share'
                comma = ' Items: '
                for j in pitems:
                    if j['sale_date'] is None and j['owned_by'] is None:
                       s1 += comma + ' ' + j['item_name']
                       comma = ','
                print('    ', afal.get_party_name(i[0]), s1, sep='')
            else:
                print('<tr><td>', afal.get_party_name(i[0]), '</td>', sep='', end='')
                if needshare:
                    print("<td>", end='')
                    if i[1] != 1.0 :
                        print(str(i[1]), end='')
                    print("</td>", end='')
                print('<td>', end='')
                if len(pitems):
                    print('<ul>')
                    for j in pitems:
                        if j['sale_date'] is None and j['owned_by'] is None:
                            print('<li>', j['item_name'], sep='')
                    print('</ul>')
                print('</td></tr>')
        if text:
            print()
        else:
            print('</table><br>')

    if len(items) :
        if text:
            print('  ', str(len(items)), ' Items', sep='')
        else:
            print('<table border="1"><tr><th>', str(len(items)),' Items</th><th>History</th></tr>', sep='')
        for i in items :
            l1=i['item_name']
            s1 = ''
            if i['note'] is not None :
                l1 += "  Note: " + i['note']
            if i['sale_date'] is None :
                s1 += "  (Party item)"
            elif i['value'] > 0:
                s1 += "  bought on " + i['sale_date'] + " for " + afal.str_cp(i['value'])
            else:
                s1 += "  given on " + i['sale_date']
            if text:
                print('    ', l1, s1, sep='')
            else:
                print('<tr><td>', l1, '</td><td>', s1, '</td></tr>', sep='')
        if text:
            print()
        else:
            print('</table><br>')

    if len(receivable) :
        print_debt(receivable, 'from', 'Receivable')

    if len(payable) :
        print_debt(payable, 'to', 'Payable')

    if text:
        print()

if len(parties) > 1:
    if text:
        print("\n        Parties\n")
    else:
        print("<br><h3>Parties</h3><br>")
for party_name in parties:
    party_id = afal.get_party_id(party_name)
    members = afal.get_party_members(party_id)
    items = afal.get_items_acquired_by(party_id)
    if text:
        print(party_name)
    else:
        print("<h4>", party_name, "</h4><br>", sep='')
    if len(members):
        h = {}
        needshare = False
        for i in members :
            c = afal.get_char_name(i[0])
            if i[1] != 1.0 :
                h[c] = str(i[1])
                needshare = True
            else:
                h[c] = ''

        if text:
            print("  Members")
        elif needshare:
            print('<table border="1"><tr><th>Member</th><th>Share</th></tr>')
        else:
            print('<table border="1"><tr><th>Member</th></tr>')
        k = h.keys()
        k.sort()
        for i in k:
            n1 = h[i]
            if text:
                if h[i] != '' :
                    n1 = " for " + n1 + " share"
                print('    ', i, n1, sep='')
            elif needshare:
                print("<tr><td>", i, "</td><td>", n1, "</dt></tr>", sep='')
            else:
                print("<tr><td>", i, "</td></tr>", sep='')
        if text:
            print()
        else:
            print("</table><br>")

    if len(items):
        if text:
            print("  Items")
        else:
            print('<h4><table border="1"><tr><th>Item</th><th>Disposition</th></h4>')
        for i in items :
            i1 = i['item_name']
            s1 = ""
            if i['note'] is not None:
                i1 += "  Note: " + i['note']
            if i['sale_date'] is not None:
                if i['value'] > 0:
                    s1 += "  Sold to " + afal.get_char_name(i['owned_by']) + " on " +i['sale_date'] + " for " + afal.str_cp(i['value'])
                else:
                     s1 += "  Given to " + afal.get_char_name(i['owned_by']) + " on " + i['sale_date']
            elif i['owned_by'] is not None:
                s1 += "  Lent to " + afal.get_char_name(i['owned_by'])
            if text:
                print('    ', i1, s1, sep = '')
            else:
                print("<tr><td>", i1, "</td><td>", s1, "</td></tr>", sep = '' )
        if text:
            print()
        else:
            print("</table><br>")
    if text:
        print()

if journal_start or journal_end:
    if text:
        print("\n        Transaction Journal\n")
    else:
        print('<h3>Transaction Journal</h3><br><table border = "1"><tr><th>Date</th><th>Entry</th></tr>')
    j = afal.get_journal(journal_start, journal_end)
    for e in j:
        if text:
            print('  ',e['made_on'], '  ', e['description'], sep='')
        else:
            print("<tr><td>", e['made_on'], "</td><td>", e['description'], "</td></tr>", sep='')
    if not text:
        print("</table><br>")

if not text:
    print("""
  </center>
</body>
</html>
""")

afal.fini()
