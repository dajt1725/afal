#!/usr/bin/python
import sys
import psycopg2
import random

# library functions used by various programs




def cp_to_gp(cp) :
    """ return the gp portion of a raw cp value"""
    return cp/200

def cp_to_cp_only(cp) :
    """ return the cp portion of a raw cp value"""
    return cp % 200

def gp_cp_to_cp(gp, cp) :
    """ turn gp and cp values into a raw cp value"""
    return int(gp * 200 + cp)

def str_gp_cp(gp, cp) :
    """ pretty-print a gp and cp value for human consumption"""
    if gp > 0 and cp > 0 :
        return str(gp)+"gp, "+str(cp)+"cp"
    elif gp > 0 :
        return str(gp)+"gp"
    elif cp > 0 :
        return str(cp)+"cp"
    else :
        return "nothing"

def str_cp(cp) :
    """ pretty-print a raw cp value"""
    return str_gp_cp(cp_to_gp(cp), cp_to_cp_only(cp))

def str_cp_to_fgp(cp) :
    """print copper pieces as fractional gold pieces"""
    return str(float(cp)/200.0)

def divide_cp(top, bottom) :
    """Perform an integer division, rounding up randomly"""

    whole = int(top/bottom)
    fract = (float(top)/float(bottom)) - whole
    if fract > random.random() :
        print top,"/",bottom,"=",whole,"fraction",fract,"rounded up"
        whole += 1
    return whole

def journal(date, by, to, amount, description) :
    """ add an entry to the transaction journal

Describe a transaction between two party members"""
    cur.execute (
 "insert into journal ( made_on, made_by, made_to, amount, description ) "
 " values ( %(date)s, %(by)s, %(to)s, (%(gp)s,%(cp)s), %(text)s )",
 { 'date' : date, 'by' : by, 'to' : to, 'gp' : cp_to_gp(amount), 'cp' : cp_to_cp_only(amount), 'text' :
 description + "." } )

def get_char_name(id) :
    """ given a char_id, return its corresponding char_name """
    cur.execute("select char_name from character where char_id = %(id)s", {'id':id })
    resp = cur.fetchall()
    if len(resp) != 1 or len(resp[0]) != 1 :
        raise NameError("Couldn't find char_id "+str(id))
    return resp[0][0]

def get_char_id(name) :
    """ given a char_name, return its corresponding char_id"""
    cur.execute("select char_id from character where char_name = %(name)s", {'name':name })
    resp = cur.fetchall()
    if len(resp) != 1 or len(resp[0]) != 1 :
        raise NameError("Couldn't find char_name "+name)
    return resp[0][0]

def get_party_id(party_name) :
    """given a party_name, return the corresponding party_id"""
    cur.execute("select party_id from party where party_name = %(party_name)s",
 { 'party_name': party_name })
    resp = cur.fetchall()
    if len(resp) != 1 or len(resp[0]) != 1 :
        raise NameError("Couldn't find party_name " + party_name)
    return resp[0][0]

def get_item_name(id) :
    """ given an item_id, return its corresponding item_name"""
    cur.execute("select item_name from item where item_id = %(id)s", {'id':id })
    resp = cur.fetchall()
    if len(resp) != 1 or len(resp[0]) != 1 :
        raise NameError("Couldn't find item_name for "+str(id))
    return resp[0][0]

def get_item_id(item_name) :
    """ given an item name, return its corresponding item_id

The database now has a unque constraint on item names, so this can't return
multiple items."""
    cur.execute("select item_id from item where item_name = %(name)s",
 {'name': item_name })
    resp = cur.fetchall()
    if len(resp) != 1 or len(resp[0]) != 1 :
        raise NameError("Couldn't find a unique item_id for " + item_name)
    return resp[0][0]

def get_item_owner(item_id) :
    cur.execute ( "select owned_by from item where item_id = %(item_id)s",
 { 'item_id' : item_id } )
    resp = cur.fetchall()
    if len(resp) != 1 or len(resp[0]) != 1 :
        raise NameError("Couldn't find seller for item id " + str(item_id))
    return resp[0][0]

def change_item_owner(item_id, date, char_id, cp = 0) :
    cur.execute("update item set ( owned_by, value, sale_date ) = "
 " ( %(char_id)s, (%(gp)s,%(cp)s), %(date)s ) "
 " where item_id = %(item_id)s returning acquired_by",
 { 'char_id' : char_id, 'gp' : cp_to_gp(cp),
 'cp' : cp_to_cp_only(cp), 'date' : date, 'item_id' : item_id } )
    resp = cur.fetchall()
    if len(resp) != 1 or len(resp[0]) != 1 :
        raise NameError("Error updating item "+str(item_id)+" "+resp)
    return resp[0][0]

def get_party_members(party_id) :
    cur.execute("select char_id, share from char_party where party_id = %(p)s",
 { 'p' : party_id } )
    resp = cur.fetchall()
    if len(resp) < 1 or len(resp[0]) < 1 :
        raise NameError("Couldn't find characters for party "+str(party_id))
    return resp

def char_add_cash(char_id, cp) :
        cur.execute("update character set ( cash ) = "
 " ( ((cash).gp + %(gp)s,(cash).cp + %(cp)s) ) where char_id = %(char_id)s",
 { 'gp' : cp_to_gp(cp), 'cp' : cp_to_cp_only(cp), 'char_id' : char_id } )

# 0 debt_id,
# 1 from_char
# repay_order
# 3 amount
# 4 share
def get_char_receivable(char_id) :
    cur.execute (
 "select debt_id, from_char, repay_order, (owed).gp * 200 + (owed).cp, share "
 " from debt where to_char = %(id)s order by from_char, repay_order",
 { 'id' : char_id } )
    return cur.fetchall()

# 0 debt_id
# 1 to_char
# 2 repay_order
# 3 amount
# 4 share
def get_char_payable(char_id) :
    cur.execute ( "select "
 " debt_id, to_char, repay_order, (owed).gp * 200 + (owed).cp, share "
 " from debt where from_char = %(id)s order by to_char, repay_order",
 { 'id' : char_id } )
    return cur.fetchall()

def get_char_rec_xferable(char_id) :
    cur.execute (
 "select tob.debt_id, tob.from_char, tob.repay_order, (tob.owed).gp * 200 + (tob.owed).cp, tob.share "
 "from debt as tob where tob.to_char = %(char_id)s and tob.repay_order = "
 " ( select min(froma.repay_order) from debt as froma where froma.from_char = tob.from_char ) order by from_char",
 { 'char_id' : char_id })
    return cur.fetchall()

def get_char_pay_xferable(char_id) :
    cur.execute(
 "select fromb.debt_id, fromb.to_char, fromb.repay_order, (fromb.owed).gp * 200 + (fromb.owed).cp, fromb.share, fromb.item_id "
 "from debt as fromb where fromb.from_char = %(char_id)s and fromb.repay_order = ( select min(toc.repay_order) from debt as toc where toc.from_char = %(char_id)s) order by to_char",
 {'char_id':char_id})
    return cur.fetchall()

def adjust_debt_repay_order(debt_id, new_order) :
    cur.execute ( "update debt set repay_order = %(new_order)s where debt_id = %(debt_id)s", {'debt_id':debt_id,'new_order':new_order})

def delete_debts_from_to(from_id, to_id) :
    cur.execute ( "delete from debt where "
 " from_char = %(from_id)s and to_char = %(to_id)s" ,
 {'from_id' : from_id, 'to_id' : to_id})

def get_char_selfdebt(char_id) :
    cur.execute ( "select debt_id, (owed).gp * 200 + (owed).cp from debt where to_char = %(char_id)s and from_char = %(char_id)s", { 'char_id' : char_id } )
    return cur.fetchall()

def remove_char_selfdebt(char_id) :
    cur.execute ( "delete from debt where to_char = %(char_id)s and from_char = %(char_id)s", { 'char_id' : char_id } )
    conn.commit()

def set_debt_owed(debt_id, amount) :
    """lower owed of a debt by the given amount"""
    cur.execute(
 "update debt set ( owed ) = ( (%(gp)s,%(cp)s) )"
 "where debt_id = %(debt_id)s",
 { 'debt_id' : debt_id, 'gp' : cp_to_gp(amount),
   'cp' : cp_to_cp_only(amount) } )

def decrease_debt(debt_id, amount) :
    """lower amount and owed of a debt by the given amount

If this would create a 0cp debt, delete it."""
    cur.execute("select "
 " (initial).gp * 200 + (initial).cp, "
 " (owed).gp * 200 + (owed).cp from debt "
 " where debt_id = %(debt_id)s", {'debt_id' : debt_id})
    resp = cur.fetchall()
    if len(resp) != 1 or len(resp[0]) != 2 :
        raise NameError("Couldn't find debt #"+str(debt_id))
    initial =resp[0][0]
    owed = resp[0][1]
    if amount > owed :
        print "Amount",amount,"> owed",owed
        amount = owed
    if owed == amount :
        cur.execute("delete from debt where debt_id = %(debt_id)s", {'debt_id' : debt_id})
    else :
        initial -= amount
        owed -= amount
        cur.execute("update debt set (initial, owed) = "
 " ((%(initial_gp)s, %(initial_cp)s),(%(owed_gp)s,%(owed_cp)s)) "
 " where debt_id = %(debt_id)s",
 {'initial_gp' :cp_to_gp(initial), 'initial_cp' : cp_to_cp_only(initial),
  'owed_gp' :cp_to_gp(owed), 'owed_cp' : cp_to_cp_only(owed),
  'debt_id' : debt_id})

def insert_debt(date, from_char, to_char, amount, share=1.0, item_id=None, repay_order=0) :
    """insert a debt into the database"""
    cur.execute("insert into debt "
 " (from_char, to_char, repay_order, share, item_id, initial, owed, owed_on) "
 " values ( %(from_char)s, %(to_char)s, %(repay_order)s, %(share)s, %(item_id)s, "
 " (%(gp)s,%(cp)s), (%(gp)s,%(cp)s), %(date)s)",
 {'from_char':from_char, 'to_char':to_char, 'repay_order':repay_order,
   'share':share, 'item_id':item_id, 'gp':cp_to_gp(amount),
   'cp':cp_to_cp_only(amount), 'date':date})

def insert_char(char_name, cp=0 ) :
    """ insert a character into the database"""
    cur.execute(
 "insert into character ( char_name, cash ) "
 " values ( %(char_name)s, (%(gp)s,%(cp)s) )",
 { 'char_name': char_name, 'gp': cp_to_gp(cp), 'cp': cp_to_cp_only(cp) } )

def insert_party(party_name) :
    """insert a party into the database"""
    cur.execute(
 "insert into party ( party_name ) values ( %(name)s ) returning party_id",
 { 'name': party_name } )
    resp = cur.fetchall()
    if len(resp) != 1 or len(resp[0]) != 1 :
        raise NameError("Bad response to party create request "+party_name+" "+resp)
    party_id = resp[0][0]
    return party_id

def insert_char_party(char_id, party_id, share=1.0) :
    """insert a char_party into the database"""
    cur.execute(
 "insert into char_party ( char_id, party_id, share ) values ( %(char_id)s, %(party_id)s, %(share)s )",
 { 'char_id' : char_id, 'party_id' : party_id, 'share' : share })

def insert_item(item_name, party_id, owner_id=None, value=None, sale_date=None, note=None) :
    """insert an item into the database"""
    if owner_id != None :
        s1a = "owned_by, "
        s2a = "%(owner_id)s, "
    else :
        s1a = ""
        s2a = ""
    if sale_date != None :
        s1b = "sale_date, "
        s2b = "%(sale_date)s, "
    else :
        s1b = ""
        s2b = ""
    if value != None :
        s1c = "value, "
        s2c = "(%(gp)s,%(cp)s), "
        gp = cp_to_gp(value)
        cp = cp_to_cp_only(value)
    else :
        s1c = ""
        s2c = ""
        gp = 0
        cp = 0
    if note != None :
        s1d = "note, "
        s2d = "%(note)s, "
    else :
        s1d = ""
        s2d = ""

    todo = "insert into item ( item_name, "+s1a+s1b+s1c+s1d+"acquired_by) values (" \
"%(item_name)s, "+s2a+s2b+s2c+s2d+"%(party_id)s ) returning item_id"
    cur.execute(todo,
{ 'item_name' : item_name, 'party_id' : party_id, 'owner_id' : owner_id,
  'gp' : gp, 'cp' : cp, 'sale_date' : sale_date, 'note' : note })
    resp = cur.fetchall()
    if len(resp) != 1 or len(resp[0]) != 1 :
        raise NameError("couldn't get item_id "+item_name+" " + resp)
    return resp[0][0]

def fini() :
    """finish things up and close the database"""
    conn.commit()
    cur.close()
    conn.close()

# begin startup code here
try :
    conn = psycopg2.connect("dbname='afal' user='afal'")
except :
    raise NameError("Database afal or user afal not found")
cur = conn.cursor()

