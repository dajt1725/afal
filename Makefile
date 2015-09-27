B=1369-01-06.dat 1369-07-09.dat 1369-10-12.dat 1370-01-03.dat 1370-04.dat 1370-05.dat
D=-h127.0.0.1 -uafal -pBuffyStewart afal_devel
P=-h127.0.0.1 -uafal -pBuffyStewart afal
W=/var/www
H=$W/html
X=$W/devel
Y=$W/afal
M=MythDranor.svg Undermountain.svg
all: devel-setup devel-push prod-setup prod-push maps-push

devel-setup:
	rm -f report.devel.out bulk.devel.out bulk.devel.err afal_config.py
	mysql $D -e 'drop database afal_devel;' -e 'create database afal_devel;'
	mysql $D < afal-schema.sql.mysql
	ln -s afal_config.py.devel.write afal_config.py
	./bulk -v $B > bulk.devel.out 2> bulk.devel.err
	mysqldump -rdump.checkpoint.sql $D
	./report > report.devel.out
	./debt >> report.devel.out
	./cash >> report.devel.out
	echo Done

devel-retry:
	mysql $D < dump.checkpoint.sql
	./bulk -v checkpoint.dat > bulk.ck.out 2> bulk.ck.err
	./report > report.ck.out
	./debt >> report.ck.out
	./cash >> report.ck.out
	echo Done

prod-setup:
	rm -f afal_config.py report.prod.out bulk.prod.out bulk.prod.err
	mysql $P -e 'drop database afal;' -e 'create database afal;'
	mysql $P < afal-schema.sql.mysql
	ln -s afal_config.py.prod.write afal_config.py
	./bulk -v $B > bulk.prod.out
	./report > report.prod.out
	./debt >> report.prod.out
	./cash >> report.prod.out
	echo Done

devel-push:
	cp mw-escher.gif $H
	cp *.png *.jpg $H
	cp afal.py.mysql $X/afal.py
	cp afal_config.py.devel $X/afal_config.py
	cp cash debt map marching menu report $X/

prod-push:
	cp *.png *.jpg $H
	cp afal.py.mysql $Y/afal.py
	cp afal_config.py.prod $Y/afal_config.py
	cp cash debt map marching menu report $Y/

maps-push:
	cp $M $W/maps/
