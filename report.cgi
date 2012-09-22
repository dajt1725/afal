#!/usr/bin/python
# This can be used as either a cgi program or from the command line
from __future__ import print_function
import argparse
import afal
import cgi
import cgitb
import re


def format_share(s):
    s = str(s)
    if len(s) > 2 and s[-2:] == '.0':
        return s[:-2]
    return s

def format_plural(n, s, p = None):
    """if len(n) is 1, return a singular string, else a plural one"""

    n = len(n)
    if n == 1:
        return '1 ' + s
    elif p is None:
        return str(n) + ' ' + s + 's'
    else:
        return str(n) + ' ' + p

def format_date(d):
    if type(d) == int:
        d = afal.date_to_str(d)
    if args.text:
        return d
    else:
        l = re.sub(' Festival', '', d)
        l = re.sub(' ', '_', l)
        return '<a href="/logs/log_' + l + '.html">' + d + '</a>'

def format_party(p):
    if args.text:
        return p
    else:
        return '<a href="report.cgi?party_name=' + p + '&generate=Party">' + p + '</a>'

def format_character(c):
    if args.text:
        return c
    else:
        return '<a href="report.cgi?char_name=' + c + '&generate=Character">' + c + '</a>'

def party_to_log(p):
    return '<a href="/logs/log_' + re.sub(r'([^-]*)-([^-]*)-([^-]*)', r'\1_\2_\3', p) + '.html">'

def format_item(i, acquired_by = None, item_id = None):
    if args.text:
        return i
    else:
        if acquired_by is None:
            acquired_by = afal.get_item_acquired_by(item_id)
        party_name = afal.get_party_name(acquired_by)
        return party_to_log(party_name) + i + '</a>'

def fmt_date(m):
    return format_date(m.group(1))

def munge_html(s):
    if s is None:
        return ''
    ret = s
    if args.text:
        ret = re.sub(r'&frac12;', ' 1/2', ret)
        ret = re.sub(r'&frac14;', ' 1/4', ret)
        ret = re.sub(r'&quot;', '"', ret)
        ret = re.sub(r'</?i>', '', ret)
        ret = re.sub(r'</?sup>', '', ret)
        ret = re.sub(r'</?a[^>]*>', '', ret)
        ret = re.sub(r'<br>', '\n', ret)
    ret = re.sub(r'<d ([^>]*)>', fmt_date, ret)
    return ret

#############################################################################

def print_char(data, verbose = False):
    al = munge_html(data['alignment'])
    if al == '':
        al = 'Unknown Alignment'
    ass = munge_html(data['association'])
    cl = munge_html(data['class'])
    if cl == '':
        cl = 'Unknown Class'
    fn = data['fullname']
    if fn is None:
        fn = data['name']
    else:
        fn = munge_html(fn)
    gn = munge_html(data['gender'])
    if gn == '':
        gn = 'Unknown Gender'
    ra = munge_html(data['race'])
    if ra == '':
        ra = 'Unknown Race'
    st = munge_html(data['status'])
    eq = munge_html(data['equipment'])
    ct = munge_html(data['characteristics'])
    no = munge_html(data['notes'])
    if data['player'] is None:
        pl = ''
        bg = '/back3l15.gif'
    else:
        pl = ' (' + munge_html(data['player']) + ')'
        bg = '/back3l16.gif'
    if args.text:
        a1 = ''
        c1 = '\n'
        a2 = '  '
        c2 = ''
        e2 = '  ' + ass + '  ' + st + '  '
        i2 = '  '
        k2 = '  '
        m2 = ''
        a3 = '  Equipment:  '
        c3 = ''
        a4 = '  Characteristics:  '
        c4 = ''
        a5 = '  Notes:  '
        c5 = ''
        a6 = ''
        a7 = '  Cash '
        c7 = ''
        a8 = '\n'
    else:
        if verbose:
            a1 = '<hr /><h2><b>'
            b1 = data['name']
            c1 = '</b></h2>'
        else:
            a1 = ''
            b1 = ''
            c1 = ''
        c1 += '<table border="border" width="90%" background="' + bg + '">'
        a2 = '   <tr><td width="40%"><a name="' + data['name'] + '"><b>'
        c2 = '</b></a>'
        e2 = '</td><td width="20%">'
        i2 = '</td><td width="20%">'
        k2 = '</td><td width="20%">'
        m2 = '</td></tr>'
        a3 = '  <tr><td colspan="3"><u>Equipment:</u>  '
        c3 = '</td>'
        a4 = '  <tr><td colspan="3"><u>Characteristics:</u>  '
        c4 = '  </td></tr>'
        a5 = '   <tr><td colspan="3"><u>Notes:</u>  '
        c5 = '   </td></tr>'
        a6 = '</table>'
        a7 = '<h3>Cash '
        c7 = '</h3>'
        a8 = '<br>'
        if eq == '':
            eq = 'Unknown'
        if ct == '':
            ct = 'Forgotten'
        if no == '':
            no = 'None'

    print(a1, b1, c1, sep='')
    print(a2, fn, c2, pl, e2, ra, ' ', gn, i2, cl, k2, al, m2, sep='')
    if eq != '':
        print(a3, eq, c3, sep='')
    if not args.text:
        if data['picture_url'] is not None:
            print('<td colspan="1" rowspan="3" align="center" valign="center" bgcolor="white">')
            if data['large_picture_url'] is not None:
                print('  <a href="/', data['large_picture_url'], '"><img src="/', data['picture_url'], '" alt="', fn, '"</a>', sep='')
            else:
                print('  <img src="/', data['picture_url'], '" alt="', fn, '" alighn="left"></td>', sep='')
        print('</tr>')

    if ct != '':
        print(a4, ct, c4, sep='')
    if no != '':
        print(a5, no, c5, sep='')
    print(a6)
    if verbose:
        cash = data['cash']
        if cash > 0:
            cash = afal.str_cp(cash)
            print(a7, cash, c7, sep='')
        print(a8)


def print_parties(parties):
        needshare = False
        if args.text:
            a1 = '  '
            c1 = ''
            a2 = ('    ', '   ', '   ')
            c2 = ''
            d2a = ' for '
            d2c = ' share'
            e2 = ('', '', '\n')
            a3 = ''
        else:
            for i in parties:
                if i[1] != 1.0:
                    needshare = True
                    break
            a1 = '<hr /><h3>'
            c1 = '</h3><table border=1><tr>'
            if needshare:
                c1 += '<th>Party</th><th>Share</th><th>|</th><th>Party</th><th>Share</th><th>|</th><th>Party</th><th>Share</th>'
            else:
                c1 += '<th colspan="3">Party</th>'
            c1 += '</tr>'
            a2 = ('<tr><td>', '<td>', '<td>')
            c2 = '</td>'
            if needshare:
                d2a = '<td>'
                d2c = '</td>'
                e2 = ('<td>|</td>','<td>|</td>','</tr>\n')
            else:
                d2=''
                e2 = ('','','</tr>\n')
            a3 = '</table><br>'
        print(a1, format_plural(parties, 'Party', 'Parties'), c1, sep = '')
        n = 0
        for i in parties:
            if needshare:
                d2 = d2a + format_share(i[1]) + d2c
            print(a2[n%3], format_party(afal.get_party_name(i[0])), c2, d2, e2[n%3], sep='', end='')
            n += 1
        if n % 3 != 0:
            print(e2[2], end='')
        print(a3)

def print_debt(l, tf, p):
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
        d[ch][n]['date'] = format_date(i['contracted_on'])
        d[ch][n]['order'] = str(i['order'])
        if i['order'] != 0:
            needorder = True
        if i['share'] != 1.0:
            needshare = True
            d[ch][n]['share'] = format_share(i['share'])
        else:
            d[ch][n]['share'] = '1'
        if i['item_id'] is not None:
            d[ch][n]['item_id'] = i['item_id']
            d[ch][n]['item_name'] = afal.get_item_name(i['item_id'])
        d[ch][n]['initial'] = afal.str_cp(i['initial_cp'])
        if i['initial_cp'] != i['amount']:
            needinitial = True
        n += 1
        d[ch]['n'] = n

    b1 = format_plural(l, p + ' Debt') + ' (Total ' + afal.str_cp(s) + ')'
    if args.text:
        print('  ', b1, sep='')
    else:
        print('<hr /><h3>', b1, '</h3>', sep='')
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
        if args.text:
            if d[i]['n']>1:
                print('    ', i, ' Total ', afal.str_cp(d[i]['sum']), sep='')
            else:
                print('    ', i, sep='')
            for j in range(d[i]['n']):
                initial = '' if d[i][j]['initial'] == d[i][j]['amount'] else ' of ' + d[i][j]['initial']
                order = '' if d[i][j]['order'] == '0' else ' repay order ' + d[i][j]['order']
                share = '' if d[i][j]['share'] == '1' else ' for ' + d[i][j]['share'] + ' share'
                item = '' if 'item_name' not in d[i][j] else  ' for ' + format_item(d[i][j]['item_name'], item_id = d[i][j]['item_id'])
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

                print('<td>', d[i][j]['date'], '</td><td>', d[i][j]['amount'], '</td>', sep='', end='')
                if needinitial:
                    print('<td>', d[i][j]['initial'], '</td>', sep='', end='')
                if needshare:
                    print('<td>', d[i][j]['share'], '</td>', sep='', end='')
                if needorder:
                    print('<td>', d[i][j]['order'], '</td>', sep='', end='')
                print('<td>', '' if 'item_name' not in d[i][j] else format_item(d[i][j]['item_name'], item_id = d[i][j]['item_id']), '</td></tr>', sep='')
            print('</tr>')
    if args.text:
        print()
    else:
        print('</table>')

def print_items(items, show_note = True, show_acquired_by = False, show_held_by = False):
    if args.text:
        a1 = '  '
        c1a = ''
        c1b = ''
        c1c = ''
        c1d = ''
        c1e = ''

        a2 = '    '
# b2 = i['name']
        c2a = ', Note:  '
        c2b = ''
# d2 = i['note'] or ''
        e2 = ', Acquired by:  '
# f2 = i['acquired_by']
        g2a = ', Held by:  '
        g2b = ''
# h2 = i['held_by']
        i2 = ', History:  '
# j2 = ...
        k2 = ''

        a3 = ''
    else:
        a1 = '<hr /><h3>'
        c1a = '</h3><table border="1"><tr><th>Item</th>'
        c1b = '<th>Note</th>'
        c1c = '<th>Acquired by</th>'
        c1d = '<th>Held by</th>'
        c1e = '<th>History</th></tr>'

        a2 = '<tr><td>'
# b2 = i['name']
        c2a = '</td><td>'
        c2b = '</td><td>'
# d2 = i['note'] or ''
        e2 = '</td><td>'
# f2 = i['acquired_by']
        g2a = '</td><td>'
        g2b = '</td><td>'
# h2 = i['held_by']
        i2 = '</td><td>'

        k2 = '</tr>'

        a3 = '</table><br>'

    if show_note:
        found = False
        for i in items:
            if i['note'] is not None:
                found = True
                break
        if not found:
            show_note = False

    if show_held_by:
        found = False
        for i in items:
            if i['held_by'] is not None:
                found = True
                break
        if not found:
            show_held_by = False

    c1 = c1a
    if show_note:
        c1 += c1b
    else:
        c2 = ''
        d2 = ''

    if show_acquired_by:
        c1 += c1c
    else:
        e2 = ''
        f2 = ''

    if show_held_by:
        c1 += c1d
    else:
        g2 = ''
        h2 = ''

    c1 += c1e
    print(a1, format_plural(items, 'Item'), c1, sep = '')
    for i in items:
        b2=format_item(i['item_name'], acquired_by = i['acquired_by'])
        if show_note:
            if i['note'] is not None:
                c2 = c2a
                d2 = i['note']
            else:
                c2 = c2b
                d2 = ''
        if show_acquired_by:
            f2 = format_party(afal.get_party_name(i['acquired_by']))
        if show_held_by:
            if i['held_by'] is not None:
                g2 = g2a
                h2 = format_character(afal.get_char_name(i['held_by']))
            else:
                g2 = g2b
                h2 = ''
        if i['sale_date'] is None:
            j2 = "Party item"
        elif i['value'] > 0:
            j2 = "Bought on " + format_date(i['sale_date']) + " for " + afal.str_cp(i['value'])
        else:
            j2 = "Given on " + format_date(i['sale_date'])
        print(a2, b2, c2, d2, e2, f2, g2, h2, i2, j2, k2, sep='')

    print(a3)


def print_journal(j, show_sub = False):
    if args.text:
        a1 = '  '
        c1a = ''
        c1b = ''
        c1c = ''
        a2 = '    '
        c2 = '  '
        d2a = 'Sub'
        d2b = ''
        f2 = ''
        a3 = ''
    else:
        a1 = '<hr /><h3>'
        c1a = '</h3><table border="1"><tr><th>Date</th>'
        c1c = '<th>Entry</th></tr>'
        c1b = '<th>Sub</th>'
        a2 = '<tr><td>'
        c2 = '</td><td>'
        d2a = 'No</td><td>'
        d2b = 'Yes</td><td>'

        f2 = '</td></tr>'
        a3 = '</table><br>'
    if show_sub:
        c1 = c1a + c1b + c1c
    else:
        c1 = c1a + c1c
        d2 = ''
    print(a1, format_plural(j, 'Transaction Journal Entry', 'Transaction Journal Entries'), c1, sep='')

    for e in j:
        b2 = format_date(e['made_on'])
        e2 = e['description']
        if show_sub:
            d2 =  d2a if e['part_of'] is None else d2b
        print(a2, b2, c2, d2, e2, f2, sep='')
    print(a3)

def print_full_character(c):
    if len(c) > 1:
        if args.text:
            a1 = '        '
            c1 = '\n'
        else:
            a1 = '<hr size="3"/><h1>'
            c1 = '</h1><br>'
        print(a1, format_plural(c, 'Character'), c1, sep='')
    for char_name in c:
        data = afal.get_char_data(char_name)
        print_char(data, verbose = True)
        char_id = afal.get_char_id(char_name)
        cparties = afal.get_char_parties(char_id)
        if len(cparties):
            print_parties(cparties)
        items = afal.get_items('Owned_by', char_id)
        if len(items):
            print_items(items, show_acquired_by = True)
        receivable = afal.get_char_receivable(char_id)
        if len(receivable):
            print_debt(receivable, 'from_id', 'Receivable')
        payable = afal.get_char_payable(char_id)
        if len(payable):
            print_debt(payable, 'to_id', 'Payable')
        j = afal.get_journal(character=char_id, primary=True)
        if len(j):
            print_journal(j)


def print_members(members):
    h = {}
    needshare = False
    shares = 0
    for i in members:
        share = i[1]
        h[afal.get_char_name(i[0])] = format_share(share)
        shares += share
        if share != 1:
            needshare = True

    if args.text:
        a1 = '  '
        c1 = ''
        a2 = ('    ','  ','  ')
        c2a1 = ' for '
        c2a3 = ' share'
        c2b = ''
        d2 = ('', '', '\n')
        a3 = ''
    else:
        a1 = '<h3>'
        c1 = '</h3><br>'
        if needshare:
            c1 += '<table border="1"><tr><th>Member</th><th>Share</th><th>|</th><th>Member</th><th>Share</th><th>|</th><th>Member</th><th>Share</th></tr>'
        else:
            c1 += '<table border="1"><tr><th colspan="3">Member</th></tr>'
        a2 = ('<tr><td>','<td>', '<td>')
        if needshare:
            c2a1 = '</td><td>'
            c2a3 = ''
            c2b = '</td><td>1'
            d2 = ('</td><td>|</td>','</td><td>|</td>','</td></tr>')
        else:
            c2 = ''
            d2 = ('</td>','</td>','</td></tr>')
        a3 = '</table><br>'
    b1 = format_plural(members, 'Member')
    if shares != len(members):
        if shares == 1:
            b1 += ', ' + '1 Share'
        else:
            b1 += ', ' + format_share(shares) + ' Shares'

    print(a1, b1, c1, sep='')
    k = h.keys()
    k.sort()
    n = 0
    for i in k:
        if needshare:
            c2 = h[i]
            if c2 != 1:
                c2 = c2a1 + c2 + c2a3
            else:
                c2 = c2b
        print(a2[n%3], format_character(i), c2, d2[n%3], sep='', end='')
        n += 1
    if n % 3 != 0:
        print(d2[2], end='')
    print(a3)

def print_full_party(p):
    if len(p) > 1:
        if args.text:
            a1 = '\n        '
            c1 = '\n'
        else:
            a1 = '<hr size="3"/><h1>'
            c1 = '</h1>'
        print(a1, format_plural(p, 'Party', 'Parties'), c1, sep='')
    for party_name in p:
        party_id = afal.get_party_id(party_name)
        items = afal.get_items('Acquired_by', party_id)
        if args.text:
            print(party_name)
        else:
            print("<hr /><h2><b>", party_to_log(party_name), party_name, "</a></b></h2><br>", sep='')

        members = afal.get_party_members(party_id)
        if len(members):
            print_members(members)

        if len(items):
            print_items(items, show_acquired_by = False)

def print_people(p):
    if len(p) > 1:
        if args.text:
            a1 = '\n        '
            c1 = '\n'
        else:
            a1 = '<hr size="3"/><h1>'
            c1 = '</h1>'
        print(a1, format_plural(p, 'Person', 'People'), c1, sep='')
    for char_name in p:
        print_char(afal.get_char_data(char_name), verbose=False)


#############################################################################
parser = argparse.ArgumentParser('Generate a report')
parser.add_argument('--text', '-t', action='store_true', default=False, help='text, not CGI')
parser.add_argument('--all', '-a', action='store_true', default=False, help='report on everything')
parser.add_argument('--character', '-c', nargs='*', default=None, help='report on these characters')
parser.add_argument('--party', '-p', nargs='*', default=None, help='report on these parties')
parser.add_argument('--journal', '-j', nargs=3, default=None, help='journal on this character')
parser.add_argument('--items', '-i', help='display sepecified item type')
parser.add_argument('--members', '-m', help='display members of the specified group')
args=parser.parse_args()

character_list = afal.get_characters('Current')

tmp = afal.get_parties()
party_list = []
for i in tmp:
    party_list.append(i[1])

journal_list = afal.get_journal_dates()

if args.text:
    if args.all:
        args.character = character_list
        args.party = party_list
        args.journal = [None, None, None]
        args.items = 'All'
        args.members = 'All'
    elif args.character is not None or args.party is not None or args.items is not None or args.journal is not None or args.members is not None:
        pass
    else:
        print("Dunno what to do")
        args.character = character_list
        args.party = party_list
        args.journal = [None, None, None]
        args.items = 'All'
        args.members = 'All'
else:
    cgitb.enable()
    print("""Content-Type: text/html

<html>
<head><title>AFAL Finance Report</title></head>
<body background="/back3l07.gif">
  <center>
    <b>Select a character:</b>
    <form action="report.cgi" method="GET">
      <select name="char_name">
        <option value="All">All</option>""")
    for i in character_list:
        print('        <option value="%s">%s</option>' % (i, i))
    print("""      </select>
      <input type="submit" name="generate" value="Character" />
    </form>
    <b>or Select a party:</b>
    <form action="report.cgi" method="GET">
      <select name="party_name">
        <option value="All">All</option>""")
    for i in party_list:
        print('        <option value="%s">%s</option>' % (i, i))
    print("""      </select>
      <input type="submit" name="generate" value="Party" />
    </form>""")
    print("    <b>or Select a journal range</b>")
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
    print('       </form>')

    print('    <b>or Select items</b>')
    print('    <form action="report.cgi" method="GET">')
    print('      <select name="item_type">')
    print('        <option value="All">All</option>')
    print('        <option value="Unresolved">Unresolved</option>')
    print('        <option value="Party">Party</option>')
    print('        <option value="Sell">to Sell</option>')
    print('        <option value="Auction">to Auction</option>')
    print('        <option value="Identify">to Identify</option>')
    print('        <option value="Lent">Lent out</option>')
    print('      </select>')
    print('      <input type="submit" name="generate" value="Items"/>')
    print('</form>')

    print('    <b>or Select a group</b>')
    print('    <form action="report.cgi" method="GET">')
    print('      <select name="members">')
    print('        <option value="All">All</option>')
    print('        <option value="Current">Current AFAL members</option>')
    print('        <option value="Former">Former AFAL members</option>')
    print('        <option value="Dead">Dead AFAL members (in memorium)</option>')
    print('        <option value="ActiveNPCs">Active NPCs</option>')
    print('        <option value="InactiveNPCs">Inactive NPCs</option>')
    print('        <option value="DeadNPCs">NPCs we have kiled</option>')
    print('      </select>')
    print('      <input type="submit" name="generate" value="Group"/>')
    print('</form>')
    form = cgi.FieldStorage()
    todo = form.getfirst("generate","")
    if todo == 'Character':
        char_name = form.getfirst("char_name","")
        if char_name == 'All':
            args.character = character_list
        else:
            args.character = [char_name]
    elif todo == 'Party':
        party_name = form.getfirst("party_name","")
        if party_name == 'All':
           args.party = party_list
        else:
            args.party = [party_name]
    elif todo == 'Journal':
        args.journal = [form.getfirst("journal_start",""), form.getfirst("journal_end",""), form.getfirst("journal_character","")]
    elif todo == 'Items':
        args.items = form.getfirst("item_type","")
    elif todo == 'Group':
        args.members = form.getfirst("members","")
    elif args.all:
        args.character = character_list
        args.party = party_list
        args.journal = [None, None, None]
        args.items = 'All'
        args.members = 'All'

if args.character is not None:
    print_full_character(args.character)

if args.party is not None:
    print_full_party(args.party)

if args.journal:
    start = args.journal[0]
    if start == 'All':
        start = None
    elif start is not None:
        start = afal.str_to_date(start)
    end = args.journal[0]
    if end == 'All':
        end = None
    elif end is not None:
        end = afal.str_to_date(end)
    character = args.journal[2]
    if character == 'All':
        character = None
    elif character is not None:
        character = afal.get_char_id(character)
    j = afal.get_journal(start, end, character)
    if len(j) > 0:
        print_journal(j, show_sub = True)

if args.items is not None:
    items = afal.get_items(args.items)
    if len(items) > 0:
        print_items(items, show_acquired_by = True, show_held_by = True)

if args.members is not None:
    characters = afal.get_characters(args.members)
    if len(characters) > 0:
        print_people(characters)

if args.text:
    print()
else:
    print("""
  </center>
</body>
</html>
""")

afal.fini()
