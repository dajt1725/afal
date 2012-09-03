create type fr_cash as (
    gp integer,
    cp integer
);

create type fr_month as enum (
	'Hammer', 'Midwinter Festival', 'Alturiak',
	'Ches', 'Tarsakh', 'Greengrass Festival', 'Mirtul', 'Kythorn',
	'Flamerule', 'Midsummer Festival', 'Eleasias', 'Eleint',
	'Highharvestide Festival', 'Marpenoth', 'Uktar', 'Moon Festival',
	'Nightal'
);

create type fr_date as (
	year integer,
	month fr_month,
	day integer
);

create sequence character_char_id_seq minvalue -1 start with -1;
CREATE TABLE character (
    char_id integer PRIMARY KEY default nextval('character_char_id_seq'),
    char_name text NOT NULL unique,
    cash fr_cash NOT NULL default ( 0, 0 )
);
alter sequence character_char_id_seq owned by character.char_id;

create sequence party_party_id_seq start with 100;
CREATE TABLE party (
    party_id integer PRIMARY KEY default nextval('party_party_id_seq'),
    party_name text unique NOT NULL
);
alter sequence party_party_id_seq owned by party.party_id;

create sequence item_item_id_seq start with 1000;
CREATE TABLE item (
    item_id integer PRIMARY KEY default nextval('item_item_id_seq'),
    item_name text unique NOT NULL,
    note text,
    acquired_by integer NOT NULL references party,
    owned_by integer references character,
    value fr_cash,
    sale_date fr_date
);
alter sequence item_item_id_seq owned by item.item_id;

CREATE TABLE char_party (
    char_id integer references character,
    party_id integer references party,
    share real not null default 1,
primary key (char_id, party_id)
);

create sequence debt_debt_id_seq start with 10000;
CREATE TABLE debt (
    debt_id integer PRIMARY KEY default nextval('debt_debt_id_seq'),
    from_char integer NOT NULL references character,
    to_char integer NOT NULL references character,
    repay_order integer,
    share real not null default 1,
    item_id integer references item,
    initial fr_cash NOT NULL,
    owed fr_cash NOT NULL,
    owed_on fr_date NOT NULL,
    constraint debt_share_ok check ( share > 0 ),
    constraint debt_initial_ok check ( (initial).gp >= 0 and (initial).cp >= 0 and (initial).cp < 200),
    constraint debt_owed_ok check ( (owed).gp >= 0 and (owed).cp >= 0 and (owed).cp < 200 ),
    constraint debt_owed_less_than_initial check ( (owed).gp <= (initial).gp ),
    constraint debt_date_ok check ( (owed_on).year > 1368 and (owed_on).day > 0 and (owed_on).day < 31 )
);
alter sequence debt_debt_id_seq owned by debt.debt_id;

create sequence journal_journal_id_seq start with 100000;
CREATE TABLE journal (
    journal_id integer primary key default nextval('journal_journal_id_seq'),
    ourtime timestamp not null default CURRENT_TIMESTAMP,
    made_on fr_date not null,
    made_by integer not null,
    made_to integer not null references character,
    amount fr_cash not null,
    description text not null,
    constraint journal_date_ok check ( (made_on).year > 1368 and (made_on).day > 0 and (made_on).day < 31 ),
    constraint journal_amount_ok check ( (amount).gp >= 0 and (amount).cp >= 0 and (amount).cp < 200 )
);
alter sequence journal_journal_id_seq owned by journal.journal_id;
