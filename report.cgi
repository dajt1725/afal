#!/usr/bin/python
# This can be used as either a cgi program or from the command line
from __future__ import print_function
import argparse
import afal
import cgi
import cgitb
import re

def de_html(s):
    if s is None:
        return ''
    ret = s
    ret = re.sub(r'&frac12;', ' 1/2', ret)
    ret = re.sub(r'&frac14;', ' 1/4', ret)
    ret = re.sub(r'&quot;', '"', ret)
    ret = re.sub(r'</?i>', '', ret)
    ret = re.sub(r'</?sup>', '', ret)
    ret = re.sub(r'</?a[^>]*>', '', ret)
    ret = re.sub(r'<br>', '\n', ret)
    return ret

def format_share(s):
    if s == 1.0:
        return '1'
    if s == 0.0:
        return '0'
    return str(s)

def format_date(d):
    if args.text:
        return d
    else:
        return '<a href="/logs/log_'+re.sub(' ', '_', d)+'.html">'+d+'</a>'

def format_party(p):
    if args.text:
        return p
    else:
        return '<a href="report.cgi?party_name=' + p + '&generate=Party">' + p + '</a>'

def format_character(c):
    if text:
        return c
    else:
        return '<a href="report.cgi?char_name=' + c + '&generate=Character">' + c + '</a>'

def print_debt(l, tf, p):
    l1 = len(l)
    s = 0
    d={}
    needorder = False
    needshare = False
    needinitial = False
    for i in l:
        s += i['amount']
        ch = afal.get_char_name(i[tf])
        if ch not in d:
            d[ch] = {'sum':0, 'n':0}
        d[ch]['sum'] += i['amount']
        n = d[ch]['n']
        d[ch][n] = {}
        d[ch][n]['amount'] = afal.str_cp(i['amount'])
        d[ch][n]['date'] = i['contracted_on']
        d[ch][n]['order'] = str(i['order'])
        if i['order'] != 0:
            needorder = True
        d[ch][n]['share'] = format_share(i['share'])
        if i['share'] != 1.0:
            needshare = True
        if i['item_id'] is not None:
            d[ch][n]['item_name'] = afal.get_item_name(i['item_id'])
        else:
            d[ch][n]['item_name'] = None
        d[ch][n]['initial'] = afal.str_cp(i['initial_cp'])
        if i['initial_cp'] != i['amount']:
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
            if d[i]['n']>1:
                print('    ', i, ' Total ', afal.str_cp(d[i]['sum']), sep='')
            else:
                print('    ', i, sep='')
            for j in range(d[i]['n']):
                initial = ' of ' + d[i][j]['initial'] if d[i][j]['initial'] != d[i][j]['amount'] else ''
                order = ' repay order ' + d[i][j]['order'] if d[i][j]['order'] != '0' else ''
                share = ' for ' + d[i][j]['share'] + ' share' if d[i][j]['share'] != '1' else ''
                item = ' for ' + d[i][j]['item_name'] if d[i][j]['item_name'] is not None else ''
                print('      ', d[i][j]['date'], '  ', d[i][j]['amount'], initial, order, share, item, sep='')
        else:
            for j in range(d[i]['n']):
                if d[i]['n'] > 1 and j == 0:
                    print('<tr><td rowspan="', str(d[i]['n']), '">',
 format_character(i), ' (', str(d[i]['n']), ' Total ', afal.str_cp(d[i]['sum']), ')</td>', sep='')
                elif j == 0:
                    print('<tr><td>', format_character(i), '</td>', sep='', end='')
                else:
                    print('<tr>', end='')

                print('<td>', format_date(d[i][j]['date']), '</td><td>', d[i][j]['amount'], '</td>', sep='', end='')
                if needinitial:
                    print('<td>', d[i][j]['initial'], '</td>', sep='', end='')
                if needshare:
                    print('<td>', d[i][j]['share'], '</td>', sep='', end='')
                if needorder:
                    print('<td>', d[i][j]['order'], '</td>', sep='', end='')
                print('<td>', d[i][j]['item_name'], '</td></tr>', sep='', end='')
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
parser.add_argument('--journal', '-J', help='journal on this character', action='store_true', default=None)
parser.add_argument('--journal-char', '-C', help='journal on this character', default=None)
parser.add_argument('--journal-start', '-j', help='display the transaction journal starting from this date', default=None)
parser.add_argument('--journal-end', '-k', help='display the transaction journal up to this date', default = None)
parser.add_argument('--items', '-i', help='display unresolved items', default = False, action='store_true')
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
journal_character = None
if text:
    if args.all:
        chars = character_list
        parties = party_list
        args.journal = True
        args.items = True
    elif args.character is not None:
        chars = [args.character]
    elif args.party is not None:
        parties = [args.party]
    elif args.journal_start is not None or args.journal_end is not None or args.journal_char is not None:
        args.journal = True
        journal_start = afal.str_to_date(args.journal_start)
        journal_end = afal.str_to_date(args.journal_end)
        journal_character = afal.get_char_id(args.journal_char)
    elif args.items:
        pass
    elif args.journal:
        pass
    else:
        print("Dunno what to do")
        chars = character_list
        parties = party_list
        args.journal = True
        args.items = True
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

    print('      From <select name="journal_start">')
    print('        <option value="All">All</option>')
    for i in journal_list:
        print('        <option value="%s">%s</option>' % (i, i))
    print('      </select>')

    print('      to <select name="journal_end">')
    print('        <option value="All">All</option>')
    for i in journal_list:
        print('        <option value="%s">%s</option>' % (i, i))
    print('      </select>')

    print('      involving <select name="journal_character">')
    print('        <option value="All">All</option>')
    for i in character_list:
        print('        <option value="%s">%s</option>' % (i, i))
    print('      </select>')

    print('      <input type="submit" name="generate" value="Journal" />')
    print("    </form><br><b>or display unresolved items</b><br>")
    print('    <form action="report.cgi" method="GET">')
    print('      <input type="submit" name="generate" value="Items"/>')
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
        args.journal = True
        journal_start = form.getfirst("journal_start","")
        if journal_start == 'All':
            journal_start = None
        else:
            journal_start=afal.str_to_date(journal_start)
        journal_end = form.getfirst("journal_end","")
        if journal_end == 'All':
            journal_end = None
        else:
            journal_end = afal.str_to_date(journal_end)
        journal_character = form.getfirst("journal_character","")
        if journal_character == 'All':
            journal_character = None
        else:
            journal_character = afal.get_char_id(journal_character)
    elif todo == 'Items':
        args.items = True
    elif args.all:
        chars = character_list
        parties = party_list
        args.journal = True
        args.items = True

if len(chars) > 1:
    if text:
        print('        ', str(len(chars)), ' Characters\n', sep='')
    else:
        print('<hr size="3"/><h1>Characters</h1><br>')
for char_name in chars:
    char_id = afal.get_char_id(char_name)
    cash = afal.get_char_cash(char_id)
    items = afal.get_items_owned_by(char_id)
    cparties = afal.get_char_parties(char_id)
    payable = afal.get_char_payable(char_id)
    receivable = afal.get_char_receivable(char_id)
    data = afal.get_char_data(char_id)
    a = de_html(data['alignment'])
    ass = de_html(data['association'])
    c = de_html(data['class'])
    fn = data['fullname']
    if fn is None:
        fn = data['name']
    else:
        fn = de_html(fn)
    g = de_html(data['gender'])
    r = de_html(data['race'])
    s = de_html(data['status'])
    if data['player'] is None:
        p = ''
        b = '/back3l15.gif'
    else:
        p = ' ('+data['player']+')'
        b = '/back3l16.gif'
    if text:
        print(char_name, "\n", sep='')
        print('  ', fn, p, '  ', ass, '  ', s, '  ', r, ' ', g, '  ', c, '  ', a, sep='')
        if data['equipment'] is not None:
            print('  Equipment:  ', de_html(data['equipment']), sep='')
        if data['characteristics'] is not None:
            print('  Characteristics:  ', de_html(data['characteristics']), sep='')
        if data['notes'] is not None:
            print('  Notes:  ', de_html(data['notes']), sep='')
        if cash > 0:
            print("  Cash ", afal.str_cp(cash), "\n", sep='')
    else:
        print('<hr /><h2><b>', char_name, '</b></h2>', sep='')
        print('<table border="border" width="90%" background="', b, '">', sep='')
        print('   <tr><td width="40%"><a name="', data['name'], '"><b>', fn,'</b></a>', p, '</td>', sep='')
        print('   <td width="20%">', r, ' ', g, '</td>', sep='')
        print('   <td width="20%">', c, '</td>', sep='')
        print('   <td width="20%">', a, '</td></tr>', sep='')
        if data['equipment'] is not None:
            print('  <tr><td colspan="3"><u>Equipment:</u>',data['equipment'],'	</td>', sep='')
            if data['picture_url'] is not None:
                print('<td colspan="1" rowspan="3" align="center" valign="center" bgcolor="white">')
                if data['large_picture_url'] is not None:
                    print('  <a href="/', data['large_picture_url'], '"><img src="/', data['picture_url'], '" alt="',fn,'"</a>', sep='')
                else:
                    print('  <img src="/', data['picture_url'], '" alt="', fn, '" alighn="left"></td>', sep='')
            print('</tr>')
        if data['characteristics'] is not None:
            print('  <tr><td colspan="3"><u>Characteristics:</u>', data['characteristics'], '  </td></tr>', sep='')
        if data['notes'] is not None:
            print('   <tr><td colspan="3"><u>Notes:</u>', data['notes'],'   </td></tr>', sep='')
        print('</table><br>')

        if cash > 0:
            print('<h3>Cash ', afal.str_cp(cash), '</h3><br>', sep='')
        else:
            print('<br>')
    if len(cparties):
        needshare = False
        for i in cparties:
            if i[1] != 1.0:
                needshare = True
                break
        if text:
            print('  ', str(len(cparties)), ' Parties', sep='')
        elif needshare:
            print('<table border=1><tr><th>Party</th><th>Share</th><th>Party</th><th>Share</th></tr>')
        else:
            print('<table border=1><tr><th colspan="2">Party</th></tr>')
        a1=('<tr>','','')
        a2=('','','</tr>')
        n = 0
        for i in cparties:
            p = format_party(afal.get_party_name(i[0]))
            s1=''
            if text:
                if i[1] != 1.0:
                    s1 += ' for ' + format_share(i[1]) + ' share'
                print('    ',p , s1, sep='')
            else:
                if needshare:
                    s1 = '<td>' + format_share(i[1]) + '</td>'
                print(a1[n%3], '<td>', p, '</td>', s1, a2[n%3], sep='', end='')
                n += 1
        if text:
            print()
        else:
            print('</table><br>')

    if len(items):
        if text:
            print('  ', str(len(items)), ' Items', sep='')
        else:
            print('<table border="1"><tr><th>', str(len(items)),' Items</th><th>History</th></tr>', sep='')
        for i in items:
            l1=i['item_name']
            s1 = ''
            if i['note'] is not None:
                l1 += "  Note: " + i['note']
            if i['sale_date'] is None:
                s1 += "  (Party item)"
            elif i['value'] > 0:
                s1 += "  bought on " + format_date(i['sale_date']) + " for " + afal.str_cp(i['value'])
            else:
                s1 += "  given on " + format_date(i['sale_date'])
            if text:
                print('    ', l1, s1, sep='')
            else:
                print('<tr><td>', l1, '</td><td>', s1, '</td></tr>', sep='')
        if text:
            print()
        else:
            print('</table><br>')

    if len(receivable):
        print_debt(receivable, 'from_id', 'Receivable')

    if len(payable):
        print_debt(payable, 'to_id', 'Payable')

    j = afal.get_journal(character=char_id, primary=True)
    if len(j):
        if text:
            print('  ', str(len(j)), ' Journal Entries', sep='')
            for e in j:
                print('    ', format_date(e['made_on']), '  ', e['description'], sep='')
            print()
        else:
            print('<br><h3>', str(len(j)), ' Journal Entries</h3><table border="1"><tr><th>Date</th><th>Journal Entry</th></tr>', sep='')
            for e in j:
                print("<tr><td>", format_date(e['made_on']), "</td><td>", e['description'], "</td></tr>", sep='')
            print("</table><br>")

    if text:
        print()

if len(parties) > 1:
    if text:
        print("\n        ", str(len(parties)), " Parties\n", sep='')
    else:
        print('<br><hr size="3"/><h1>Parties</h1><br>')
for party_name in parties:
    party_id = afal.get_party_id(party_name)
    members = afal.get_party_members(party_id)
    items = afal.get_items_acquired_by(party_id)
    if text:
        print(party_name)
    else:
        print("<hr /><h2>", party_name, "</h2><br>", sep='')
    if len(members):
        h = {}
        needshare = False
        for i in members:
            c = afal.get_char_name(i[0])
            if i[1] != 1.0:
                h[c] = format_share(i[1])
                needshare = True
            else:
                h[c] = '1'

        if text:
            print("  Members")
        else:
            print('<h3>'+str(len(members))+' Members</h3><br>')
            if needshare:
                print('<table border="1"><tr><th>Member</th><th>Share</th></tr>')
            else:
                print('<table border="1"><tr><th>Member</th></tr>')
        k = h.keys()
        k.sort()
        for i in k:
            n1 = h[i]
            if text:
                if n1 == '1':
                    n1 = ''
                else:
                    n1 = " for " + n1 + " share"
                print('    ', i, n1, sep='')
            else:
                if needshare:
                    n1 = '</td><td>' + n1
                else:
                    n1 = ''
                print('<tr><td>', format_character(i), n1, '</td></tr>', sep='')
        if text:
            print()
        else:
            print("</table><br>")

    if len(items):
        if text:
            print("  Items")
        else:
            print('<h3>'+str(len(items))+' Items</h3><br>')
            print('<table border="1"><tr><th>Item</th><th>Disposition</th>')
        for i in items:
            i1 = i['item_name']
            if i['note'] is not None:
                i1 += "  Note: " + i['note']
            c = ''
            if i['owned_by'] is not None:
                c = format_character(afal.get_char_name(i['owned_by']))
            s1 = ''
            if i['sale_date'] is not None:
                d = " on " + format_date(i['sale_date'])
                if i['value'] > 0:
                    s1 += "  Sold to " + c + " for " + afal.str_cp(i['value']) + d
                else:
                    s1 += "  Given to " + c + d
            elif i['owned_by'] is not None:
                s1 += "  Lent to " + c
            else:
                s1 += '  Unresolved'
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

if args.journal:
    if text:
        print("\n        Transaction Journal\n")
    else:
        print('<hr size="3"/><h1>Transaction Journal</h1><br><table border = "1"><tr><th>Date</th><th>Sub</th><th>Entry</th></tr>')
    j = afal.get_journal(journal_start, journal_end, character=journal_character)
    for e in j:
        if text:
            s1 = '    ' if e['part_of'] is None else '      '
            
            print(s1, format_date(e['made_on']), '  ', e['description'], sep='')
        else:
            print('<tr><td>', format_date(e['made_on']), '</td><td>', 'No' if e['part_of'] is None else 'Yes', '</td><td>', e['description'], "</td></tr>", sep='')
    if text:
        print()
    else:
        print("</table><br>")

if args.items:
    items = afal.get_unresolved_items()
    if text:
        print('\n        ', str(len(items)), ' Unresolved Items\n')
    else:
        print('<hr size="3"/><h3>', str(len(items)),' Unresolved Items</h3><br><table border="1"><tr><th>Party</th><th>Item</th></tr>')
    for i in items:
        p = format_party(i['acquired_by'])
        n = '  Note: ' + i['note'] if 'note' in i and i['note'] is not None else ''
        iname = i['item_name'] + n
        if text:
            print('  ', p, '  ', iname, sep='')
        else:
            print('<tr><td>', p, '</td><td>', iname, '</td></tr>', sep='')
    if text:
        print()
    else:
        print('</table><br>')

if not text:
    print("""
  </center>
</body>
</html>
""")

afal.fini()
