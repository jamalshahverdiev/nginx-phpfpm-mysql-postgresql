#!/usr/bin/env python2.7

import sys
import os
import jinja2

from fabric.api import *
from fabric.tasks import execute
import getpass

templateLoader = jinja2.FileSystemLoader( searchpath="/" )
templateEnv = jinja2.Environment( loader=templateLoader )
TEMPNVFILE = os.getcwd()+'/jinja2temps/c7ngvhost.conf'
TEMPPFILE = os.getcwd()+'/jinja2temps/c7index.php'
TEMPHFILE = os.getcwd()+'/jinja2temps/c7index.html'
TEMPPGPFILE = os.getcwd()+'/jinja2temps/cfpginsert.php'

tempht = templateEnv.get_template( TEMPHFILE )
tempphp = templateEnv.get_template( TEMPPFILE )
tempnv = templateEnv.get_template( TEMPNVFILE )
temppgp = templateEnv.get_template( TEMPPGPFILE )

env.host_string = raw_input('Please enter WEB server IP address: ')
env.user = raw_input('Please enter username for UNIX/Linux server: ')
env.password = getpass.getpass()
sitename = raw_input('Please enter site name: ')

tempnvVars = { "sname" : sitename, "domain" : sitename, }

outputngvhText = tempnv.render( tempnvVars )
outputnghText = tempht.render( tempnvVars)

def vhhtmlwriter():
    with open(os.getcwd()+'/output/'+sitename+'.conf', 'wb') as ngvhfile:
        ngvhfile.write(outputngvhText)
    with open(os.getcwd()+'/output/index.html', 'wb') as indhtml:
        indhtml.write(outputnghText)

def sqlservicecheck(pidfile, pid):
    if pidfile == pid:
        print('SQL service already running...')
        pass
    else:
        print('SQL service is not running...')
        sys.exit()

def prandwainput():
    print('Virtual host '+sitename+' already configured...')
    print(' 1. To add MySQL database for this virtual host write 1 and press "Enter"!!!')
    print(' 2. To add PostgreSQL database for this virtual host write 2 and press "Enter"!!!')
    print(' 3. If you want to exit from script just press "Enter" button. ')
    global inst
    inst = raw_input('Please select: ')

def dbcreds():
    global sitedb
    sitedb = raw_input('Enter name for new database: ')
    global sitedbuser
    sitedbuser = raw_input('Enter user name for database: ')
    global sitedbpasswd
    sitedbpasswd = getpass.getpass('Enter pass for '+sitedbuser+': ')
    global sitedbpasswd1
    sitedbpasswd1 = getpass.getpass('Repeat pass for '+sitedbuser+': ')
    while sitedbpasswd != sitedbpasswd1:
        print('Entered passwords must be the same. Please enter passwords again. ')
        sitedbpasswd = getpass.getpass('Please enter password: ')
        sitedbpasswd1 = getpass.getpass('Please repeat password: ')
        if sitedbpasswd == sitedbpasswd1:
            print('The password set successfully!')
            break
        print('Entered passwords must be the same. Please enter passwords again. ')

def inphpcreater():
    tempphVars = { "sitedb" : sitedb, "sitedbuser" : sitedbuser, "sitedbpasswd" : sitedbpasswd}
    outputphpText = tempphp.render( tempphVars )
    with open(os.getcwd()+'/output/index.php', 'wb') as nginpfile:
        nginpfile.write(outputphpText)
    put(os.getcwd()+'/output/index.php', '/var/www/'+sitename+'/html/index.php')

def pgphpcreater():
    tempphVars = { "sitedb" : sitedb, "sitedbuser" : sitedbuser, "sitedbpasswd" : sitedbpasswd }
    outputpgpText = temppgp.render( tempphVars )
    with open(os.getcwd()+'/output/cfpgpinsert.php', 'wb') as pgphpfile:
        pgphpfile.write(outputpgpText)
    put(os.getcwd()+'/output/cfpgpinsert.php', '/var/www/'+sitename+'/html/insert.php')
    put(os.getcwd()+'/jinja2temps/cfindex.html', '/var/www/'+sitename+'/html/index.html')

def c7vhostcreate():
    run('mkdir -p /var/www/'+sitename+'/html')
    put(os.getcwd()+'/output/'+sitename+'.conf', '/etc/nginx/sites-available/')
    put(os.getcwd()+'/output/index.html', '/var/www/'+sitename+'/html/index.html')
    run('ln -s /etc/nginx/sites-available/* /etc/nginx/sites-enabled/')
    run('systemctl restart nginx')

def f10vhostcreate():
    run('mkdir -p /var/www/'+sitename+'/html')
    put(os.getcwd()+'/output/'+sitename+'.conf', '/usr/local/etc/nginx/sites-available/')
    put(os.getcwd()+'/output/index.html', '/var/www/'+sitename+'/html/')
    run('ln -s /usr/local/etc/nginx/sites-available/* /usr/local/etc/nginx/sites-enabled/ ; service nginx restart')

def checkvhexists():
    if sitename == domex:
        print(' Entered domain name '+sitename+' is already exists on the '+env.host_string+' server!!!')
        print(' Please enter different name than "'+sitename+'" !!!')
        sys.exit()
    else:
        pass

def createmysqldb():
    run('mysql -u root -p\'freebsd\' -e "CREATE DATABASE '+sitedb+';"')
    run('mysql -u root -p\'freebsd\' -e "GRANT ALL PRIVILEGES ON '+sitedb+'.* TO '+sitedbuser+'@localhost IDENTIFIED BY \''+sitedbpasswd+'\';"')
    run('mysql -u root -p\'freebsd\' -e "FLUSH PRIVILEGES;"')

cuser = 'postgres'
fuser = 'pgsql'
def createpgsqldb(username):
    oversitepass = "'\\'%s\\''" % sitedbpasswd
    run('su - '+username+' -c "psql -c \'CREATE DATABASE '+sitedb+';\'"')
    run('su - '+username+' -c "psql -c \'CREATE USER '+sitedbuser+' WITH PASSWORD '+oversitepass+';\'"')
    run('su - '+username+' -c "psql -c \'GRANT ALL PRIVILEGES ON DATABASE '+sitedb+' TO '+sitedbuser+';\'"')
    run('su - '+username+' -c "psql -c \'CREATE TABLE book( bookid CHAR(255), bookname CHAR(255), author CHAR(255), publisher CHAR(255), dop CHAR(255), price CHAR(255) );\' '+sitedb+'"')
    run('su - '+username+' -c "psql -c \'GRANT ALL PRIVILEGES ON TABLE book  TO '+sitedbuser+';\' '+sitedb+'"')

def dbornotselect():
    if inst == "1":
        print(' You have chose MySQL with PHP-FPM!')

        if osver == 'FreeBSD' and ftype >= 10:
            mysqlpidf = run('cat /var/db/mysql/*.pid')
            mysqlpid = run('ps waux|grep /usr/local/libexec/mysqld | grep -v grep | awk \'{ print $2 }\'')
            sqlservicecheck(mysqlpid, mysqlpidf)
            dbcreds()
            createmysqldb()
            inphpcreater()
            run('service php-fpm restart ; service nginx restart')
        elif osver == 'Linux' and lintype == 'CentOS':
            msqlpid = run('cat /var/run/mariadb/mariadb.pid')
            msqlpidfile = run('ps waux|grep mysql | grep -v grep| grep -v safe | awk \'{ print $2 }\'')
            sqlservicecheck(msqlpid, msqlpidfile)
            dbcreds()
            createmysqldb()
            inphpcreater()
            run('systemctl restart nginx ; systemctl restart php-fpm')
        print('MySQL database and Nginx configured for your site: '+sitename+'')

    elif inst == "2":
        print(' You have chose PostgreSQL with PHP-FPM!')

        if osver == 'FreeBSD' and ftype >= 10:
            psqlpidf = run('cat /usr/local/pgsql/data/postmaster.pid | head -1')
            psqlpid = run('ps waux|grep /usr/local/bin/postgres | grep -v grep | awk \'{ print $2 }\'')
            sqlservicecheck(psqlpid, psqlpidf)
            dbcreds()
            createpgsqldb(fuser)
        elif osver == 'Linux' and lintype == 'CentOS':
            pgsqlpidf =  run('cat /var/run/postgresql/.s.PGSQL.5432.lock | head -1')
            pgsqlpid = run('ps waux|grep /usr/bin/postgres | grep -v grep | awk \'{ print $2 }\'')
            sqlservicecheck(pgsqlpid, pgsqlpidf)
            dbcreds()
            createpgsqldb(cuser)
        else:
            print(' Server type is not detected!!!')

        pgphpcreater()
        print('PostgreSQL database and Nginx configured for your site: '+sitename+'')

    else:
        sys.exit()

with settings(
        hide('warnings', 'running', 'stdout', 'stderr'), 
        warn_only=True
):
    osver = run('uname -s')
    lintype = run('cat /etc/redhat-release | awk \'{ print $1 }\'')
    ftype = run('uname -v | awk \'{ print $2 }\' | cut -f1 -d \'.\'')

    if osver == 'FreeBSD' and ftype >= 10:
        print(' This is FreeBSD server...')
        domex = run('ls -la /usr/local/etc/nginx/sites-enabled/ | grep '+sitename+' | awk \'{ print $9 }\' | cut -f1,2 -d \'.\'')
        checkvhexists()
        nginxpidf = run('cat /var/run/nginx.pid')
        nginxpid = run('ps waux | grep nginx | grep root | grep -v grep | awk \'{ print $2 }\'')

        if nginxpid == nginxpidf:
            print(' You have already running Nginx web server...')
            vhhtmlwriter()
            f10vhostcreate()
        else:
            print(' Nginx server is not running. For install Nginx web server please use ./ngphfpmypg.py script...')
            sys.exit()

        prandwainput()
        dbornotselect()

    elif osver == 'Linux' and lintype == 'CentOS':
        print(' This is CentOS server...')
        domex = run('ls -la /etc/nginx/sites-enabled/ | grep '+sitename+' | awk \'{ print $9 }\' | cut -f1,2 -d \'.\'')
        checkvhexists()
        ngpidf = run('cat /var/run/nginx.pid')
        ngpid = run('ps waux | grep nginx | grep root | grep -v grep | awk \'{ print $2 }\'')

        if ngpid == ngpidf:
            print(' You have already running Nginx web server...')
            vhhtmlwriter()
            c7vhostcreate()
        else:
            print(' Nginx server is not running. For install Nginx web server please use ./ngphfpmypg.py script...')
            sys.exit()

        prandwainput()
        dbornotselect()

    else:
        print(' This script supports FreeBSD or CentOS7 server...')
