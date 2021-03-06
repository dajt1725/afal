#!/usr/bin/python
import sys
import mysql.connector
import random
import re
import afal_config
import os

############################## begin startup code here


conn = mysql.connector.connect(**afal_config.config)
conn.get_warnings = True
cur = conn.cursor()

auction = 'Auction'
sell = 'Sell'
destroyed = 'destroyed'
outside = 'Someone'
party = 'AFAL'
special = (auction, sell, destroyed, outside)

######## Cleanup and misc code

def commit():
    conn.commit()


def fini():
    """finish things up and close the database"""
    conn.commit()
    cur.close()
    conn.close()


# if may is None, don't check for extra keys at all
def check_dict(d, must = None, may = None):
    """ dict must contain every element in 'must', and may contain elements in 'may'"""

    if must is None:
        must = {}
    if may is not None:
        for i in d:
            if i not in must and i not in may:
                sys.stderr.write("\nUnexpected key '{i}' found in dict {d} only expected must={must}, may={may}\n".format(i=i,d=d,must=must,may=may))
                raise NameError("Unexpected key " + i)

    for i in must:
	if not i in d:
            sys.stderr.write("\nMissing key '{i}' in dict {d} expected must={must}\n".format(i=i,d=d,must=must))
            raise NameError("Missing key " + i)


def _ins_if_not(d, l):
    for k in l:
        if k not in d:
            d[k] = None


def _check_warnings():
    warnings = cur.fetchwarnings()
    if warnings:
        sys.stderr.write("\nWarnings!: {warnings}\n".format(warnings=warnings))

######## Formatted output

def pw(*args, **kwargs):
    """print-wrapped, which is like print, except linewrapps as appropriate"""

    
    eol = kwargs.get('end', '\n')
    asep = kwargs.get('sep', ' ')
    m = kwargs.get('max',None)
    indent = kwargs.get('indent',0) * ' '
    prefix = kwargs.get('prefix',0) * ' '
    pad = kwargs.get('pad')
    ret = ''
    sep = ''
    for i in args:
        ret += sep + str(i)
        sep = asep
    while m is not None and len(ret) > m:
        n = ret[0:m].rfind(' ')
        if n < m / 2:
            n = m
        sys.stdout.write(prefix)
        sys.stdout.write(ret[0:n])
        sys.stdout.write(eol)
        ret = ret[n+1:]
        if indent != prefix:
            m -= len(indent)
            prefix = indent
    sys.stdout.write(prefix)
    sys.stdout.write(ret)
    if pad and ret.rfind('\n') < 0:
        if len(ret) < pad:
            sys.stdout.write((pad - len(ret) ) * ' ')
        else:
            sys.stdout.write('  ')
    sys.stdout.write(eol)


######## File IO and parsing

def _nextline(f):
    if _nextline.line:
        ret = _nextline.line
        _nextline.line = None
        return ret
    ret = ''
    while True:
        tmp = f.readline()
        if len(tmp) < 1:
            break
        if tmp[0] == '#':
            continue
        if tmp[-1] == '\n':
            tmp = tmp[:-1]
            if len(tmp) < 1:
                break
        if tmp[-1] != '\\':
            ret += tmp
            break
        ret += tmp[:-1]
    return ret


_nextline.line = None
_indent = ' ,'

def _peekline(file):
    line = _nextline(file)
    if _nextline.line:
        raise NameError("Line already pushed")
    _nextline.line = line
    if line == '':
        return '\n'
    return line

def _add_entries(d, line):
    while line[0] in _indent:
        line = line[1:]
    h1 = ''
    while len(line) > 0:
        if ';' in line:
            sep = line.index(';')
            if sep > 0 and line[sep-1] == '\\':
                h1 += line[0:sep-1] + ';'
                line = line[sep+1:]
                continue
            hdr = h1 + line[0:sep]
            line = line[sep+1:]
            h1 = ''
        else:
            hdr = h1+line
            line = ''
        if '=' in hdr:
            e = hdr.index('=')
            name = hdr[0:e]
            value = hdr[e+1:]
        else:
            name = hdr
            value = True
        if name in d:
            sys.stderr.write("\nKey {name} already in {d}\n".format(name=name,d=d))
            raise NameError("Key '"+name+"' is already in dict")
        d[name] = value
    return d

def _compare_indent(l1, l2):
    len1 = 0
    while l1[len1] in _indent:
        len1 += 1
    len2 = 0
    while l2[len2] in _indent:
        len2 += 1
    return len2 - len1

# aaa:
#   We read a line
# bbb:
#   we create a hash
#   populate it with the entries we inherited
#   fill it with the entries for our current line
#   look at the indentation on the next line
#   If it's deeper or the same
#   If it's deeper
#     recurse, passing the hash
#     goto bbb
#   else
#     Create an object using the hash
#   If it's the same
#     goto aaa
#   return

def parse_file(file, doit, inherited):
    while True:
        line = _nextline(file)
        if line == '':
            break
        us = _add_entries(dict(inherited), line)
        hadsub = False
        while True:
            peek = _peekline(file)
            i = _compare_indent(line, peek)
            if i > 0:
                parse_file(file, doit, dict(us))
                hadsub = True
                continue
            if i == 0:
                if not hadsub:
                    doit(dict(us))
                break
            if i < 0:
                if not hadsub:
                    doit(dict(us))
                return

######## Date functions

month_names = (
 'Hammer',    'Alturiak', 'Ches',   'Tarsakh',   'Mirtul', 'Kythorn',
 'Flamerule', 'Eleasias', 'Eleint', 'Marpenoth', 'Uktar',  'Nightal')

festival_names = ('Midwinter', 'Greengrass', 'Midsummer', 'Higharvestide', 'Moon')

month_offset = {
 'Hammer':0,      'Midwinter Festival':30,      'Alturiak':31,   'Ches':61,
 'Tarsakh':91,    'Greengrass Festival':121,    'Mirtul':122,    'Kythorn':152,
 'Flamerule':182, 'Midsummer Festival':212,     'Eleasias':213,  'Eleint':243,
                  'Higharvestide Festival':273, 'Marpenoth':274, 'Uktar':304,
                  'Moon Festival':334,          'Nightal':335}

_day_names = (
 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th', 'th',
 'th', 'th', 'th', 'th', 'th', 'th', 'th', 'th', 'th', 'th',
 'th', 'th', 'th', 'th', 'th', 'th', 'th', 'th', 'th', 'th')

def _make_date(year, month, day):
    year = int(year)
    day = int(day)
    if year < 1369 or year > 1370 or day < 1 or day > 30 or month not in month_offset:
        raise ValueError("Invalid date {y} {m} {d}".format(y=year, m=month, d=day))
    return 1000 + 365 * (year - 1368) + month_offset[month] + day - 1

def str_to_date(date):
    """ turn a human readable date (day month year) into a date_id"""
# 365 * (year-1368) + month_offset[month] + day

    if date is None or type(date) is int:
        return date
    r = re.match(r'(\d+)\s+(\w+),?\s+(\d+)$', date)
    if r:
        return _make_date(r.group(3), r.group(2), r.group(1))
    r = re.match(r'(\w+)\s+Festival,?\s+(\d+)$', date)
    if r:
        return _make_date(r.group(2), r.group(1)+' Festival', 1)
    r = re.match(r'\((\d+),\s+(\w+),\s+(\d+)\)',date)
    if r:
        return _make_date(r.group(1), r.group(2), r.group(3))
    r = re.match(r'(\d+)\s+([a-zA-Z]+),?\s+(\d+)', date)
    if r:
        return _make_date(r.group(3), r.group(2), r.group(1))
    r = re.match(r'([a-zA-Z]+)\s+(\d+),?\s+(\d+)', date)
    if r:
        return _make_date(r.group(3), r.group(1), r.group(2))
    r = re.match(r'([a-zA-Z]+)\s+(\d+)([a-zA-Z]+?),?\s+(\d+)', date)
    if r:
	day = int(r.group(2))
        if _day_names[day-1] == r.group(3):
            return _make_date(r.group(4), r.group(1), day)
    raise NameError("Unknown date "+date)

#day_names = {
# 1:'First', 2:'Second', 3:'Third', 4:'Fourth', 5:'Fifth', 6:'Sixth',
# 7:'Seventh', 8:'Eighth', 9:'Ninth', 10:'Tenth', 11:'Eleventh', 12:'Twelth',
#13:'Thirteenth', 14:'Fourteenth', 15:'Fifteenth', 16:'Sixteenth', 17:'Seventeenth',
#18:'Eighteenth', 19:'Ninteenth', 20:'Twentieth', 21:'Twenty-First', 22:'Twenty-second',
#23:'Twenty-third', 24:'Twenty-fourth', 25:'Twenty-fifth', 26:'Twenty-sixth',
#27:'Twenty-seventh', 28:'Twenty-eighth', 29:'Twenty-ninth', 30:'Thirtyith'}

off_monthset = ((0, 29, 'Hammer'), (30, 30, 'Midwinter Festival'),
 (31, 60, 'Alturiak'), (61, 90, 'Ches'), (91, 120, 'Tarsakh'),
 (121, 121, 'Greengrass Festival'), (122, 151, 'Mirtul'), (152, 181, 'Kythorn'),
 (182, 211, 'Flamerule'), (212, 212, 'Midsummer Festival'), (213, 242, 'Eleasias'),
 (243, 272, 'Eleint'), (273, 273, 'Higharvestide Festival'), (274, 303, 'Marpenoth'),
 (304, 333, 'Uktar'), (334, 334, 'Moon Festival'), (335, 364, 'Nightal'))

def date_to_str(date, is_html = True):
    """return a human-readable form of a date-id"""

    try:
        date = int(date)
    except:
        sys.stderr.write("\ndate {d} already a string\n".format(d=date))
        return date
    if date < 1000:
        raise NameError("Invalid date " + str(date))
    date -= 1000
    year = 1368 + int(date/365)
    mo = date % 365
    for i in off_monthset:
        if mo >= i[0] and mo <= i[1]:
            month = i[2]
            if i[0] == i[1]:
                return month + ' ' + str(year)
            day = 1 + mo - i[0]
            if is_html:
                return month+' '+str(day)+'<font size="-1"><sup>'+_day_names[day-1]+'</sup></font>, '+str(year)
            return month+' '+str(day)+_day_names[day-1]+', '+str(year)
    raise NameError("Couldn't find date '" + repr(date))+"'"

def party_to_date(d):
    return str_to_date(re.sub(r'^([^-]*-)?([^-]+)-(Festival|[0-9]+)[A-Za-z]?-([^-]+)$', r'\2 \3 \4', d))

######## Copper and Gold piece functions

def _find_coin(m):
    q = m.group(2)
    if q is None:
        q = 1
    else:
        q = int(q)
    c = m.group(3)
    if c in str_to_coins.coins:
        str_to_coins.coins[c] += q
    else:
        str_to_coins.coins[c] = q
    return ''


def coins_add(c, coin, n):
    if coin not in coins_byname:
        raise NameError("Unknown coin '"+coin+"' in money")
    if n == 0:
        return c
    c['value_cp'] += n * coins_byname[coin]['copper_equiv']
    if 'abbrev' in coins_byname[coin]:
        name = coins_byname[coin]['abbrev']
    else:
        name = coins_byname[coin]['coin']
    if name in c:
        if c[name] == n:
            del c[name]
        else:
            c[name] += n
    else:
        c[name] = n
    return c


def coins_by_cpe(s):
    tmp = {}
    for i in s:
        if i == 'value_cp':
            continue
        if not i in coins_byname:
            pw(coins_byname,max=80)
            raise ValueError("Unknown coin '"+i+"' in coins")
        n = int(s[i])
        if n == 0:
            continue
        cpe = coins_byname[i]['copper_equiv']
        if cpe not in tmp:
            tmp[cpe] = {}
        tmp[cpe][i] = n
    ret = []
    l = tmp.keys()
    l.sort(reverse = True)
    for i in l:
        tmp_ret = []
        m = tmp[i].keys()
        m.sort()
        for j in m:
            tmp_ret.append([tmp[i][j], j])
        ret.append(tmp_ret)
    return ret


def str_to_coins(s):
    global coins_byname
    if s is None:
        return None
    str_to_coins.coins = {}
    tmp = s.lower()
    while len(tmp)>0:
        rest = re.sub(r'^\s*((\d+)[\*x]?)?\s*([^0-9,]+[^,]*)(,|$)', _find_coin, tmp)
        if rest == tmp:
            raise NameError ("invalid text '"+rest+"' in money")
        tmp = rest
    myret = {'value_cp': 0}
    for i in str_to_coins.coins:
        myret = coins_add(myret, i, int(str_to_coins.coins[i]))
    return myret


def coins_to_str(s):
    if s is None:
        return ''
    ret = ''
    sep = ''
    nsep = ', '
    for i in coins_by_cpe(s):
        for j in i:
            n = j[0]
            if n == 1:
                coin = j[1].format(s='', es='', y='y')
            else:
                coin = j[1].format(s='s', es='es', y='ies')
            ret += '{sep}{n} {coin}'.format(sep = sep, n = n, coin = coin)
            sep = nsep
    return ret


def str_to_cp(s):
    global coins_byname
    if s is None:
        return None
    return str_to_coins(s)['value_cp']


def cp_to_str(cp):
    """ pretty-print a raw cp value"""

    if cp is None:
        return ''
    if cp == 0:
        return "nothing"
    if cp < 0:
        return "NEGATIVE MONEY " + str(int(-cp/200)) + "gp, " + str(-cp%200) + "cp"
    gp = int(cp/200)
    cp = cp % 200
    if gp > 0 and cp > 0:
        return str(gp) + "gp, " + str(cp) + "cp"
    elif gp > 0:
        return str(gp) + "gp"
    else:
        return str(cp) + "cp"


def divide_cp(share, total, shares):
    """Perform an integer division, rounding up"""

    whole = int((share * total)/shares)
    fract = (float(share * total)/float(shares)) - whole
    if fract >= 0.5000:
        whole += 1
    return whole
#    if float(int(top/bottom)) != float(top)/float(bottom):
#        return 1 + int(top/bottom)
#    return int(top/bottom)

def insert_coin(coin, abbrev, copper_equiv, common=True, note = None):
    global coins_byname,coins_bycpe,coins_byid
    cur.execute(
 ' insert into fr_money_type (coin, abbrev, copper_equiv, priority, note) '
 ' values ( %(coin)s, %(abbrev)s, %(copper_equiv)s, %(common)s, %(note)s)',
 { 'coin': coin, 'abbrev': abbrev, 'copper_equiv': copper_equiv, 'common': common, 'note': note})
    _check_warnings()
    ret = cur.lastrowid
    (coins_byname, coins_bycpe, coins_byid) = get_coins()
    return ret

def get_coins():
    cur.execute('select money_id, coin, copper_equiv, priority, abbrev, note from fr_money_type order by copper_equiv desc')
    resp = cur.fetchall()
    ret_byname = {}
    ret_bycpe = {}
    ret_byid = {}
    for i in resp:
        tmp = {}
        tmp['money_id'] = i[0]
        tmp['coin'] = i[1]
        tmp['copper_equiv'] = i[2]
        tmp['priority'] = i[3]
        if i[4] is not None:
            tmp['abbrev'] = i[4]
            ret_byname[i[4]] = tmp
            ret_byname[i[4].lower()] = tmp
        if i[5] is not None:
            tmp['note'] = i[5]
        if i[2] in ret_bycpe:
            ret_bycpe[i[2]].append(tmp)
        else:
            ret_bycpe[i[2]] = [tmp]
        ret_byname[i[1]] = tmp
        ret_byname[i[1].lower()] = tmp
        ret_byname[i[1].format(s='', es='', y='y').lower()] = tmp
        ret_byname[i[1].format(s='s', es='es', y='ies').lower()] = tmp
        ret_byid[i[0]] = tmp
    return (ret_byname, ret_bycpe, ret_byid)


def get_char_money(char):
    cur.execute('select m.money_id, m.quantity from '
 ' fr_char_money as m natural join fr_money_type as t where m.owner ='
 ' %(char)s order by t.priority, t.copper_equiv desc, t.coin', {'char':char})
    resp = cur.fetchall()
    _check_warnings()
    ret = []
    for i in resp:
        id = i[0]
        t = coins_byid[id]
        tmp = {'money_id': id, 'coin': t['coin'], 'copper_equiv': t['copper_equiv'], 'priority': t['priority'], 'quantity': int(i[1])}
        if 'abbrev' in t:
            tmp['abbrev'] = t['abbrev']
        if 'note' in t:
            tmp['note'] = t['note']
        ret.append(tmp)
    return ret


def char_find_money(char, amount_cp):
    ret = {'value_cp': amount_cp}
    x = get_char_money(char)
    for i in x:
        if i['priority'] == 0:
            continue
        cpe = i['copper_equiv']
        if cpe > amount_cp:
            continue
        q = i['quantity']
        if cpe * q > amount_cp:
            n = int(amount_cp/cpe)
        else:
            n = q
        if n == 0:
            continue
        if 'abbrev' in i:
            name = i['abbrev']
        else:
            name = i['coin']
        ret[name] = n
        amount_cp -= n * cpe
        if amount_cp == 0:
            break
    if amount_cp:
#        pw("Error: getting {a} ({l} left) from {x} got {r}".format(a = ret['value_cp'], l = amount_cp, x = x, r = ret), max = 130)
        raise ValueError("Char {char} needs {amount_cp} change".\
format(char = char, amount_cp = amount_cp))
    return ret

def invent_money(amount_cp):
    if amount_cp is None or amount_cp == 0:
        return None
    ret = {'value_cp': amount_cp}
    l = coins_bycpe.keys()
    l.sort(reverse = True)
    print "invent money list",l
    for i in l:
        if i > amount_cp:
            continue
        for j in coins_bycpe[i]:
#            print "invent money",j
            if j['priority'] == 1 or j['priority'] == 0:
                continue
            n = int(amount_cp / i)
#            print "inventing",n,j['coin']
            if n == 0:
                continue
            if 'abbrev' in j:
                ret[j['abbrev']] = n
            else:
                ret[j['coin']] = n
            amount_cp -= n * i
            if amount_cp == 0:
                break
        if amount_cp == 0:
            break
    if amount_cp > 0:
        raise ValueError("Can't Happen")
    return ret

def char_change_money(char, dir, d):
    global coins_byname
    if dir == 'give':
        sign = -1
    elif dir == 'get':
        sign = 1
    else:
        raise ValueError("Dir isn't 'give' or 'get': '"+dir+"'")
    total = 0
    coins = get_char_money(char)
    for coin in d:
        if coin == 'value_cp':
            continue
        if coin not in coins_byname:
            raise NameError("{char} invalid coin {coin}".format(char=char, coin=coin))
        amount = int(sign * int(d[coin]))
        if amount == 0:
            continue
        coin = coins_byname[coin]
        cc = None
        for i in coins:
            if coin['coin'] == i['coin']:
                cc = i['quantity']
                break
        if cc is None:
            if amount < 0:
                raise ValueError("{char} has no {coin}, needs {n}".format(char = char, coin = coin['coin'], n = -amount))
            cur.execute("insert into fr_char_money (owner, money_id, quantity)"
" values (%(char)s, %(id)s, %(amount)s)",
 {'char': char, 'id': coin['money_id'], 'amount': amount})
        elif cc + amount < 0:
            raise ValueError("{char} only has {cc} {coin}, needs {n}".format(char=char, cc = cc, coin = coin['coin'], n = -amount))
        elif cc + amount == 0:
            cur.execute("delete from fr_char_money where owner=%(char)s and money_id = %(id)s",
 {'char': char, 'id': coin['money_id']})
        else:
            cur.execute("update fr_char_money set quantity = %(amount)s where owner=%(char)s and money_id = %(id)s",
 {'char': char, 'id': coin['money_id'], 'amount': cc + amount})
        _check_warnings()
        total += amount * coin['copper_equiv']
    cur.execute("update fr_character set cash_cp = cash_cp + %(total)s where char_name = %(char)s",
 {'char': char, 'total': total})
    _check_warnings()


def chars_move_cash(i):
    """move cash from one character to another, journaling it"""

    check_dict(i, must=('date', 'by', 'to'), may=('cash', 'amount_cp', 'journal', 'item', 'for', 'note', 'part_of', 'journ_by', 'journ_to'))
    by = i['by']
    to = i['to']
    if get_party_data(by)['type'] == 'AFAL':
        by = party
    if get_party_data(to)['type'] == 'AFAL':
        to = party
    if 'cash' in i:
        cash = i['cash']
        if not 'value_cp' in cash:
            raise ValueError("invalid cash")
        amount_cp = cash['value_cp']
    else:
        cash = None
        amount_cp = i['amount_cp']
    if by not in special:
        if cash is None:
            cash = char_find_money(by, amount_cp)
        char_change_money(by, 'give', cash)
    if to not in special:
        if cash is None:
            cash = invent_money(amount_cp)
        char_change_money(to, 'get', cash)
    if i.get('journal', True):
        text = 'gave {cs}'+coins_to_str(cash)+'{ce} {each}to {to}'
        if i.get('item'):
            text += " for " + i['item']
        if i.get('for'):
            text += " for " + i['for']
        if i.get('note'):
          text += ' ' + i['note']
        if 'journ_by' in i and text in i['journ_by']:
            ret = i['journ_by'][text]
            journal_add_by(ret, i['by'])
        elif 'journ_to' in i and text in i['journ_to']:
            ret = i['journ_to'][text]
            journal_add_to(ret, i['to'])
        else:
            ret = journal(str_to_date(i['date']), i['by'], i['to'], amount_cp, None, text, i.get('part_of'))
            if 'journ_by' in i:
                i['journ_by'][text] = ret
            if 'journ_to' in i:
                i['journ_to'][text] = ret
        return ret
    return i.get('part_of')

######## Shares


def share_to_str(s):
    if float(s) == 1.0:
        return '1'
    if float(s) == 0.0:
        return 'no'
    if float(s) == 0.5:
        return '&frac12;'
    if float(s) == 0.25:
        return '&frac14;'
# Shouldn't get here, but who knows?
    if s == int(float(s)):
        return str(int(s))
    s = str(s)
    if s[0:2] == '0.':
        s = s[1:]
    return s


######## Journal entries

def journal(date, by, to, cash_cp, virtual_cp, text, part_of = None):
    """add an entry to the transaction journal, returning an id that may be used for subsequent calls"""

    if date is None or by is None or text is None:
        raise NameError("Missing required field in journal")
    date = str_to_date(date)
    cur.execute (
 "insert into fr_journal ( date, cash_cp, virtual_cp, description, part_of ) "
 " values ( %(date)s, %(cash)s, %(virtual)s, %(text)s, %(part_of)s )",
 {'date':date, 'cash':cash_cp, 'virtual': virtual_cp,
 'text':text + ".", 'part_of':part_of})
    _check_warnings()
    id = cur.lastrowid
    if type(by) is list:
        for i in by:
            cur.execute("insert into fr_journ_by ( journal_id, made_by ) value ( %(id)s, %(i)s )", { 'id': id, 'i': i })
            _check_warnings()
    else:
        cur.execute("insert into fr_journ_by ( journal_id, made_by ) value ( %(id)s, %(i)s )", { 'id': id, 'i': by })
        _check_warnings()
    if type(to) is list:
        for i in to:
            cur.execute("insert into fr_journ_to ( journal_id, made_to ) value ( %(id)s, %(i)s )", { 'id': id, 'i': i })
            _check_warnings()
    elif to:
        cur.execute("insert into fr_journ_to ( journal_id, made_to ) value ( %(id)s, %(i)s )", { 'id': id, 'i': to })
        _check_warnings()
    return id


def journal_add_by(id, by):
    cur.execute("insert into fr_journ_by(journal_id, made_by) values(%(id)s, %(by)s)", {'id': id, 'by': by})
    _check_warnings()


def journal_add_to(id, to):
    cur.execute("insert into fr_journ_to(journal_id, made_to) values(%(id)s, %(to)s)", {'id': id, 'to': to})
    _check_warnings()


def get_journal_dates(char = None):
    """return a list of dates (in text form) of entries in the journal"""

    if char:
        clause = "natural join fr_journ_by natural join fr_journ_to where fr_journ_by.made_by = %(char)s or fr_journ_to.made_to = %(char)s"
    else:
        clause = ""
    cur.execute('select distinct fr_journal.date from fr_journal {clause} order by date'.format(clause = clause), {'char': char})
    resp = cur.fetchall()
    _check_warnings()
    if resp == None or len(resp)==0:
        return resp
    ret=['latest']
    for i in resp:
        ret.append(date_to_str(i[0], False))
    return ret

    
def get_journal(cond = None):
    """return a list of dicts of entries in the journal"""

    if cond is None:
        cond = {}
    check_dict(cond, must=None, may=('char', 'char2', 'primary', 'on', 'starting_on', 'up_to', 'cash'))
    clause = ''
    pre = ' where '
    npre = ' and '
    date1 = None
    date2 = None
    char = []
    char_clause = ''
    args = {}
    if cond.get('char','').lower() == 'all':
        del cond['char']
    if cond.get('char2','').lower() == 'all':
        del cond['char2']
    if cond.get('on','').lower() == 'all':
        del cond['on']
    if cond.get('starting_on','').lower() == 'all':
        del cond['starting_on']
    if cond.get('up_to','').lower() == 'all':
        del cond['up_to']
    if 'char' in cond:
        char.append(cond['char'])
    if 'char2' in cond:
        char.append(cond['char2'])
    if len(char) > 0:
        if len(char) > 1:
            tmp = "(journal_id in (select journal_id from fr_journ_by where made_by in (%(ch1)s, %(ch2)s)) and journal_id in (select journal_id from fr_journ_to where made_to in (%(ch1)s, %(ch2)s)))"
            args['ch1'] = char[0]
            args['ch2'] = char[1]
        else:
            tmp = "(journal_id in (select journal_id from fr_journ_by where made_by = %(ch)s) or journal_id in (select journal_id from fr_journ_to where made_to = %(ch)s))"
            args['ch'] = char[0]
        clause += pre + tmp
        char_clause = ' where ' + tmp
        pre = npre
    if 'primary' in cond:
        clause += pre + ' part_of is NULL '
        pre = npre
    if 'on' in cond:
        if cond['on'].lower() == 'latest':
            clause += pre + ' date = (select max(date) from fr_journal {char_clause}) '.format(char_clause = char_clause)
        else:
            clause += pre + ' date = %(on)s '
            args['on'] = str_to_date(cond['on'])
        pre = npre
    if 'starting_on' in cond:
        if 'on' in cond:
            raise KeyError("Can't have both 'starting_on' and 'on' in condition")
        if cond['starting_on'].lower() == 'latest':
            clause += pre + ' date = (select max(date) from fr_journal {char_clause}) '.format(char_clause = char_clause)
        else:
            clause += pre + ' date >= %(s_o)s '
            args['s_o'] = str_to_date(cond['starting_on'])
        pre = npre
    if 'up_to' in cond:
        if 'on' in cond:
            raise KeyError("Can't have both 'up_to' and 'on' in condition")
        if cond['up_to'].lower() == 'latest':
            pass
        else:
            clause += pre + ' date <= %(u_t)s '
            args['u_t'] = str_to_date(cond['up_to'])
        pre = npre
    if 'cash' in cond:
        clause += pre + ' cash_cp > 0 '
        pre = npre

    cmd = 'select '\
' journal_id, part_of, ourtime, date, cash_cp, virtual_cp, description'\
' from fr_journal {clause} order by date, journal_id'.format(clause = clause)
    cur.execute(cmd, args)
    resp = cur.fetchall()
    _check_warnings()
    if resp == None or len(resp) == 0:
        return resp
    ids = []
    for i in resp:
        ids.append(i[0])
    if len(ids) == 1:
        ids = '({id})'.format(id=ids[0])
    elif len(ids) > 1:
        ids = str(tuple(ids))
    by_map = {}
    to_map = {}
    if len(ids) > 0:
        text = 'select journal_id, made_by from fr_journ_by where journal_id in '+ids
        cur.execute(text)
        by_tmp = cur.fetchall()
        _check_warnings()
        for i in by_tmp:
            if i[0] in by_map:
                by_map[i[0]].append(i[1])
            else:
                by_map[i[0]] = [i[1]]
        text = 'select journal_id, made_to from fr_journ_to where journal_id in '+ids
        cur.execute(text)
        to_tmp = cur.fetchall()
        _check_warnings()
        for i in to_tmp:
            if i[0] in to_map:
                to_map[i[0]].append(i[1])
            else:
                to_map[i[0]] = [i[1]]
    ret=[]
    for i in resp:
        id = i[0]
        to_list = to_map.get(id)
        t = {}
        t['journal_id'] = id
        t['by'] = by_map[i[0]]
        t['to'] = to_list
        t['part_of'] = i[1]
        t['ourtime'] = i[2]
        t['date'] = i[3]
        t['cash_cp'] = i[4]
        t['virtual_cp'] = i[5]
        t['description'] = i[6]
        ret.append(t)
    return ret

########## Characters


def insert_character(d):
    """ insert a character into the database"""

    global coins_byname
    check_dict(d, must=('name', 'status', 'association', 'date'), may=(
 'alignment', 'characteristics', 'class', 'hidden_note', 'equipment',
 'fullname', 'gender', 'note', 'player', 'race', 'cash', 'picture',
 'large_picture'))
    _ins_if_not(d, ('alignment', 'association', 'characteristics', 'class',
 'equipment', 'fullname', 'hidden_note', 'large_picture', 'note', 'picture',
'player', 'race'))
    if 'gender' not in d:
        d['gender'] = 'Unknown Gender'
    if 'cash' in d:
        d['cash_cp'] = 0
    else:
        d['cash_cp'] = None
    cur.execute(
 "insert into fr_character ( "
 " char_name, status, alignment, association, "
 " char_acteristics, class, hidden_note, equipment, "
 " fullname, gender, note, player, "
 " race, cash_cp, picture_url, large_picture_url ) "
 " values ( "
 " %(name)s, %(status)s, %(alignment)s, %(association)s, "
 " %(characteristics)s, %(class)s, %(hidden_note)s, %(equipment)s, "
 " %(fullname)s, %(gender)s, %(note)s, %(player)s, "
 " %(race)s, %(cash_cp)s, %(picture)s, %(large_picture)s )", d )
    _check_warnings()
# Every character is in a party of just themselves
# This is primarily to prevent someone accidentally creating a party and a
# character with the same names
    insert_party({'name': d['name'], 'type': 'Character', 'date': d['date'], 'members': {d['name']: 1}})
    if 'cash' in d:
        char_change_money(d['name'], 'get', str_to_coins(d['cash']))


def get_characters(kind, match = None):
    """return a list of name entries for characters in the database"""

    clause = ''
    if kind == 'All':
        clause = 'status != "dummy"'
    elif kind == 'Current':
        clause = 'status = "active" and association = "AFAL"'
    elif kind == 'Former':
        clause = 'status = "inactive" and association = "AFAL"'
    elif kind == 'Dead':
        clause = 'status = "dead" and association = "AFAL"'
    elif kind == 'ActiveNPCs':
        clause = 'status = "active" and ( association is NULL or association != "AFAL")'
    elif kind == 'InactiveNPCs':
        clause = 'status = "inactive" and ( association is NULL or association != "AFAL")'
    elif kind == 'DeadNPCs':
        clause = 'status = "dead" and (association is NULL or association != "AFAL")'
    else:
        raise NameError("Unknown kind " + str(kind))
    cur.execute("select char_name from fr_character "
 " where " + clause + " order by char_name")
    resp = cur.fetchall()
    _check_warnings()
    ret = []
    if len(resp) < 1 or len(resp[0]) != 1:
        return ret
    for i in resp:
        ret.append(i[0])
    return ret


def get_char_data(char):
    """ given a char, return its data """

    cur.execute("select fullname, player, gender, "
 " race, class, alignment, picture_url, equipment, "
 " char_acteristics, note, association, status, cash_cp, "
 " large_picture_url "
 " from fr_character where char_name = %(char)s",
 {'char':char})
    resp = cur.fetchall()
    _check_warnings()
    if len(resp) != 1:
        raise NameError("Couldn't find char '" + char + "'")
    resp = resp[0]
    ret = {}
    ret['name'] = char
    ret['fullname'] = resp[0]
    ret['player'] = resp[1]
    ret['gender'] = resp[2]
    ret['race'] = resp[3]
    ret['class'] = resp[4]
    ret['alignment'] = resp[5]
    ret['picture_url'] = resp[6]
    ret['equipment'] = resp[7]
    ret['characteristics'] = resp[8]
    ret['note'] = resp[9]
    ret['association'] = resp[10]
    ret['status'] = resp[11]
    ret['cash_cp'] = resp[12]
    ret['large_picture_url'] = resp[13]
    ret['coins'] = get_char_money(char)
    return ret


########## Parties


def get_party_data(party):
    """Given a party, return a list [[[name, share]...], shares] of its members"""

    cur.execute("select date, type, note from fr_party where party_name = %(party)s",
{'party':party})
    resp = cur.fetchall()
    _check_warnings()
    if len(resp) != 1 or len(resp[0]) != 3:
         raise NameError("party not found " + party)
    ret = {'name': party, 'date': resp[0][0], 'type': resp[0][1], 'note': resp[0][2], 'members': {}}
    cur.execute("select char_name, share from fr_char_party where party_name = %(party)s",
{'party':party})
    resp = cur.fetchall()
    _check_warnings()
    if len(resp) < 1 or len(resp[0]) < 1:
         raise NameError("Members not found " + party)
    for i in resp:
        ret['members'][i[0]] = i[1]
    return ret


def get_char_parties(char):
    """Return a list of [party, share] that the character is in"""

    cur.execute("select fr_char_party.party_name, fr_char_party.share from "
 "fr_char_party natural join fr_party where fr_party.party_name != %(char)s"
 " and fr_char_party.char_name = %(char)s order by fr_party.date, fr_party.party_name",
 {'char':char})
    resp = cur.fetchall()
    _check_warnings()
    return resp


def get_parties():
    """Return a list of name entries for all the parties in the database"""

    cur.execute("select party_name from fr_party where type = 'AFAL' order by date, party_name")
    resp = cur.fetchall()
    _check_warnings()
    if len(resp) < 1 or len(resp[0]) < 1:
        return resp
    ret = []
    for i in resp:
        ret.append(i[0])
    return ret


def insert_party(d):
    """insert a party into the database"""

    check_dict(d, must=('name', 'date', 'type', 'members'), may=('note',))
    party = d['name']
    date = str_to_date(d['date'])
    cur.execute(
 "insert into fr_party (party_name, type, date, note) values (%(party)s,"
 " %(type)s, %(date)s, %(note)s)", {'party':party, 'type':d['type'], 'date':date, 'note':d.get('note')})
    _check_warnings()
    for char in d['members'].keys():
        cur.execute( "insert into fr_char_party (char_name, party_name, share)"
" values ( %(char)s, %(party)s, %(share)s )",
 {'char': char, 'party': party, 'share': d['members'][char]})
        _check_warnings()


def char_leave_parties(date, char, note = None):
    """set the share of the specified character to 0 in all parties they were in"""

    cur.execute("update fr_char_party set share = 0 where char_name = %(char)s", {'char':char})
    _check_warnings()
    text = "left AFAL"
    if note:
        text += ' ' + note
    journal(date, char, None, None, None, text)


def get_marching_names():
    ret = []
    cur.execute('select distinct marching_name from fr_marching order by marching_name')
    resp = cur.fetchall()
    for i in resp:
        ret.append(i[0])
    return ret


# ranks is a list of lists.  Each sublist contains Char_name, over, down, width, height
def insert_marching(name, ranks):
    """"insert a party marching order into the database"""

    for i in ranks:
        cur.execute('insert into fr_marching (marching_name, char_name, over, down, width, height) values (%(m)s, %(c)s, %(o)s, %(d)s, %(w)s, %(h)s)', {'m': name, 'c': i['char'], 'o': i['over'], 'd': i['down'], 'w': i['width'], 'h': i['height']})
        _check_warnings()


def get_marching(name):
    """ get the specified marching order from the database, returning a list-of-lists of characters"""

    ret = []
    cur.execute('select char_name, race, gender, class, hidden_note, over, down, width, height from fr_marching natural join fr_character where marching_name = %(name)s order by down, over', { 'name': name })
    n = 0
    resp = cur.fetchall()
    for (cn, r, g, cl, hn, o, d, w, h) in resp:
        ret.append({'char': cn, 'race': r, 'gender': g, 'class': cl, 'hidden_note': hn, 'over': o, 'down': d, 'width': w, 'height': h})
    return ret

########## Items


def insert_item(d):
    """insert an item into the database"""

    check_dict(d, must=('item', 'finder', 'owner', 'holder', 'note',
 'value_cp', 'date_found', 'date_xfrd'), may=())
    item = d['item']
    d['date_found'] = str_to_date(d['date_found'])
    d['date_xfrd'] = str_to_date(d['date_xfrd'])
    cur.execute ( "select item_name from fr_item where item_name = %(item)s or item_name like %(with)s", {'item': item, 'with':item + '  #%%'})
    resp = cur.fetchall()
    _check_warnings()
    if len(resp) == 1:
        cur.execute("update fr_item set item_name = %(new)s where item_name = %(old)s",
 {'new': item + "  #1", 'old':item})
    if len(resp) > 0:
        item += "  #" + str(len(resp)+1)
        sys.stdout.write("Note: renaming item to {item}\n".format(item = item))
        d['item'] = item

    cur.execute(
 "insert into fr_item(item_name, found_by, owned_by, held_by, note, value_cp, date_found, date_xfrd)"
 " values(%(item)s, %(finder)s, %(owner)s, %(holder)s, %(note)s, %(value_cp)s, "
 " %(date_found)s, %(date_xfrd)s)", d)
    _check_warnings()


def get_item_data(item):
    """Get the data about an item"""

    cur.execute ( "select found_by, owned_by, held_by, date_found, date_xfrd, note, value_cp from fr_item where item_name = %(item)s",
 {'item':item})
    resp = cur.fetchall()
    _check_warnings()
    if resp is None or len(resp) != 1:
        return resp
    resp = resp[0]
    t = {}
    t['item'] = item
    t['finder'] = resp[0]
    t['owner'] = resp[1]
    t['holder'] = resp[2]
    t['date_found'] = resp[3]
    t['date_xfrd'] = resp[4]
    t['note'] = resp[5]
    t['value_cp'] = None if resp[6] is None else int(resp[6])
    return t


def change_item(date, item, owner=None, holder=None, value_cp = None, part_of = None):
    """Change the ownership, transfer date, and/or value_cp of an item"""

    date = str_to_date(date)
    c1 = ''
    if owner is not None:
        c1 += ",owned_by=%(owner)s"
    if holder is not None:
        c1 += ",held_by=%(holder)s"
    if value_cp is not None:
        c1 += ",value_cp=%(value_cp)s"

    cur.execute('update fr_item set date_xfrd=%(date)s' + c1 + ' where item_name=%(item)s',
 {'date':date, 'item':item, 'owner':owner, 'holder':holder, 'value_cp':value_cp })
    _check_warnings()
    return part_of

def get_items(kind, match = None):
    clause = ''
    if kind == 'Unresolved':
        clause = 'where owned_by = found_by and held_by is NULL'
    elif kind == 'Party':
        clause = 'where owned_by = %(party)s'
    elif kind == 'Auction':
        clause = 'where held_by = %(auction)s or note like "%%Auction%%"'
    elif kind == 'Sell':
        clause = 'where held_by = %(sell)s or note like "%%Sell%%"'
    elif kind == 'Lent':
        clause = 'where held_by is not NULL and held_by != owned_by'
    elif kind == 'Identify':
        clause = 'where note like "%%Identify%%"'
    elif kind == 'All':
        pass
    elif kind == 'Found_by':
        clause = 'where found_by = %(match)s'
    elif kind == 'Owned_by':
        clause = 'where owned_by = %(match)s'
    elif kind == 'Held_by':
        clause = 'where held_by = %(match)s'
    cur.execute("select "
 " item_name, found_by, owned_by, held_by, date_found, date_xfrd, note, value_cp "
 " from fr_item " + clause + " order by item_name",
 {'party':party, 'auction':auction, 'sell':sell, 'match':match})
    resp = cur.fetchall()
    _check_warnings()
    ret = []
    for i in resp:
        t = {}
        t['item'] = i[0]
        t['finder'] = i[1]
        t['owner'] = i[2]
        t['holder'] = i[3]
        t['date_found'] = i[4]
        t['date_xfrd'] = i[5]
        t['note'] = i[6]
        t['value_cp'] = None if i[7] is None else int(i[7])
        ret.append(t)
    return ret


######## Debts


def get_char_debts(char, type):
    if type == 'Payable':
        clause = 'debtor = %(char)s'
        order = 'debtee'
    elif type == 'Receivable':
        clause = 'debtee = %(char)s'
        order = 'debtor'
    else:
        raise NameError("Unknown debt type " + type)
    text = 'select debt_id, debtor, debtee, repay_order, owed_cp, share, date, item, initial_cp from fr_debt where ' + clause + '  order by ' + order + ', repay_order'
    cur.execute(text , {'char':char})
    resp = cur.fetchall()
    _check_warnings()
    if resp is None or len(resp) == 0:
        return resp
    ret = []
    for i in resp:
        t = {}
        t['debt_id'] = i[0]
        t['by'] = i[1]
        t['to'] = i[2]
        t['order'] = i[3]
        t['amount_cp'] = i[4]
        t['share'] = i[5]
        t['date'] = i[6]
        t['item'] =  i[7]
        t['initial_cp'] = i[8]
        ret.append(t)
    return ret


def bump_debt_repay_order(debt_id):
    """increase the repay_order of the specified debt"""
    cur.execute ( "update fr_debt set repay_order = repay_order + 1 where debt_id = %(debt_id)s", {'debt_id':debt_id})
    _check_warnings()


def delete_debt(d):
    """Deletes the specified debt and journal it"""

    check_dict(d, must=('debt_id', 'by', 'to', 'date', 'amount_cp', 'verb' ), may=('item', 'note', 'journaled', 'journal', 'part_of'))
    cur.execute ( "delete from fr_debt where debt_id = %(debt_id)s", {'debt_id': d['debt_id']} )
    _check_warnings()
    if d.get('journal',True):
        text = d['verb'] + ' {a}debt{s} of {virtual} {each}to {to}'
        if d.get('item'):
            text += ' for ' + d['item']
        if d.get('note'):
            text += ' ' + d['note']
        if 'journaled' in d and text in d['journaled']:
            journal_add_to(d['journaled'][text], d['to'])
        else:
            journal_id = journal(d['date'], d['by'], d['to'], None, d['amount_cp'], text, d.get('part_of'))
            if 'journaled' in d:
                d['journaled'][text] = journal_id

def debt_lower_owed(d):
    """Lower the amount owed on the specified debt and journal it"""

    check_dict(d, must=('date', 'by','to', 'amount_cp', 'debt_id', 'lower_cp', 'verb'), may=('item', 'note', 'part_of'))
    cur.execute("update fr_debt set owed_cp = owed_cp - %(lower_cp)s "
 " where debt_id = %(debt_id)s", {'lower_cp':d['lower_cp'], 'debt_id':d['debt_id']})
    _check_warnings()
    if d.get('item'):
        fer = ' for ' + d['item']
    else:
        fer = ''
    if d.get('note'):
        note = ' ' + d['note']
    else:
        note = ''
    text = '{verb} {{virtual}} of a {old} debt to {{to}}{fer} leaving {new}{note}'.format(verb=d['verb'], old = cp_to_str(d['amount_cp']),fer=fer, new=cp_to_str(d['amount_cp'] - d['lower_cp']), note=note)
    journal(d['date'], d['by'], d['to'], None, d['lower_cp'], text, d.get('part_of'))


def insert_debt(d):
    """insert a debt into the database"""

    check_dict(d, must=('date', 'by', 'to', 'amount_cp'), may=('repay_order','share', 'item'))
    by = d['by']
    to = d['to']
    if by == to:
        raise ValueError("Can't insert a self-debt {by}".format(by=by))
    e = { 'by': by, 'to': to, 'amount_cp': d['amount_cp'], 'date': str_to_date(d['date']),
 'repay_order': d.get('repay_order',0), 'share': d.get('share',1.0), 'item': d.get('item')}

    cur.execute("insert into fr_debt "
 " (date,debtee,debtor,repay_order,share,item,initial_cp,owed_cp) "
 " values(%(date)s, %(by)s, %(to)s, %(repay_order)s, %(share)s, %(item)s, "
 " %(amount_cp)s, %(amount_cp)s)", e)
    _check_warnings()

#############################################################################

global coins_byname,coins_bycpe,coins_byid
(coins_byname, coins_bycpe, coins_byid) = get_coins()
character_list = get_characters('Current')
party_list = get_parties()
date_list = get_journal_dates()
marching_names = get_marching_names()

if 'QUERY_STRING' in os.environ:
    def _map_to_name(m):
        ret = m
        if len(ret)>4 and ret[-4:] == '.svg':
            ret = ret[:-4]
        return ret

    maps = os.listdir("../maps")
    maps.sort()
    map_names = []
    for i in maps:
        map_names.append(_map_to_name(i))
    items_values = ('Unresolved','Party','Auction','Sell','Lent','Identify')
    items_texts = ('Unresolved Items', 'Party Items', 'Items to Auction', 'Items to Sell', 'Items Lent Out', 'Items to Identify')
    people_values = ('Current', 'Former', 'Dead', 'ActiveNPCs', 'InactiveNPCs', 'DeadNPCs')
    people_texts = ('Current AFAL Members', 'Former AFAL Members', 'Dead AFAL Members', 'People We Might Meet', "People We Probably Won't Meet", 'People We Have Killed')

    def _format_group(has_all, name_singular, name_plural, val_pre, sel, values, texts):
        ret = \
 '    <optgroup label="{ns}">\n'.format(vp = val_pre,
 ns = name_singular, np = name_plural)
        if has_all:
            ret += \
 '     <option value="{vp}All">All {np}</option>\n'.format(
 vp = val_pre, np = name_plural)

        for v,t in zip(values,texts):
            s = ''
            if v == sel:
                s = 'selected '
            ret += \
'      <option {s}value="{vp}{v}">{t}</option>\n'.format(s = s, vp = val_pre, v = v, t = t)
        ret += '     </optgroup>'
        return ret

    def html_header(title, style = ''):
        return """Content-Type: text/html

<html>
 <head>
  <title>{title}</title>
  <META http-equiv="Content-Script-Type" content="text/javascript">
  <META HTTP-EQUIV="Content-Language" Content="en">
  {style}
 </head>
 <body background="{background}" lang="en">
  <div align="center">
   <form action="{menu_url}" method="GET">
    <noscript>
     <input type="submit" name="generate" value="Show"/>
    </noscript>
    <label for="start">From</label>
    <select name="start">
{dates_group}
    </select>
    <label for="end">to</label>
    <select name="end">
{dates_group}
    </select>
    <label for="char">involving</label>
    <select name="char">
{char_group}
    </select>
    <select name="todo" onchange='this.form.submit()'>
     <option selected label="Choose" value="Noop">Pick Something</option>
     <optgroup label="Executive Summary">
      <option label="Cash" value="Cash">Cash Summary</option>
      <option label="Debt" value="Debt">Debt Summary</option>
     </optgroup>
     <optgroup label="Show it all">
      <option label="Everything" value="All">Everything</option>
      <option label="Journal" value="Journal">Journal</option>
     </optgroup>
{char_group}
{maps_group}
{party_group}
{items_group}
{people_group}
{marching_group}
    </select>
   </form>
  </div>
  <hr />
  <div align="center">""".format(
 title = title,
 style = style,
 background = afal_config.background,
 menu_url = afal_config.menu_url,
 char_group = _format_group(True, 'Character', 'Characters', 'char.', '', character_list, character_list),
 party_group = _format_group(True, 'Party', 'Parties', 'party.', '', party_list, party_list),
 items_group = _format_group(True, 'Items', 'Items','items.', '', items_values, items_texts),
 people_group = _format_group(True, 'Groups','Groups', 'people.', '', people_values, people_texts),
 dates_group = _format_group(True, 'Date', 'Dates', '', 'latest', date_list, date_list),
 maps_group = _format_group(False, 'Map', 'Maps', 'map.', '', maps, map_names),
 marching_group = _format_group(False, 'Marching Order', 'Marching Orders', 'marching.', '', marching_names, marching_names))

    def html_footer():
        return '   <br>\n  </div>\n  <hr />\n  <div align="center"><a href="{menu_url}"><b>Return to Menu</b></a></div>\n </body>\n</html>'.format(menu_url = afal_config.menu_url)
######## End
