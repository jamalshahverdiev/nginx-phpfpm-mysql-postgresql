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
    print('Nginx server installed and configured...')
    print(' 1. If you want install and configure MySQL with PHP-FPM write 1 and press "Enter"!!!')
    print(' 2. If you want install and configure PostgreSQL with PHP-FPM write 2 and press "Enter"!!!')
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

def ngprintexit():
    print(' You have already installed and running Nginx web server...')
    print(' If you want add new VirtualHost, please use ./add-vhost-ngphfpmypg.py script.')
    sys.exit()

def hostnametohosts():
    ip = run('ifconfig `ifconfig | head -n1 | cut -f1 -d\':\'` | grep \'inet \' | awk \'{ print $2 }\'')
    name = run('hostname')
    run('echo \"'+ip+' '+name+'.lan '+name+'\" >> /etc/hosts')

def phpfpmconf():
    put(os.getcwd()+'/jinja2temps/f10php-fpm.conf', '/usr/local/etc/php-fpm.conf')
    put(os.getcwd()+'/jinja2temps/f10php.ini', '/usr/local/etc/php.ini')
    run('sysrc php_fpm_enable="YES"') 
    run('mkdir /var/run/php-fpm/')
    run('/usr/local/etc/rc.d/php-fpm start')
    run('service nginx restart')

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

def fmysqlinstaller():
    print(' You have chose MySQL with PHP-FPM!')
    print(' Please be patient, it will take some time...')
    run('pkg install -y mysql56-server php56 php56-mysql')
    run('sysrc mysql_enable="YES"')
    run('pkg install -y php56-bz2 php56-mysql php56-mysqli php56-calendar php56-ctype php56-curl php56-dom php56-exif php56-fileinfo php56-filter php56-gd ph    p56-gettext php56-hash php56-iconv php56-json php56-mbstring php56-mcrypt php56-openssl php56-posix php56-session php56-simplexml php56-tokenizer php56-wddx php56-xml php56-xmlreader php56-xmlwriter php56-xmlrpc php56-xsl php56-zip php56-zlib')
    run('/usr/local/etc/rc.d/mysql-server start')
    run('echo -e "\n\nfreebsd\nfreebsd\n\n\n\n\n" | mysql_secure_installation 2>/dev/null')
    msqlpid = run('ps waux|grep mysql | grep -v grep| grep -v safe | awk \'{ print $2 }\'')
    msqlpidf = run('cat /var/db/mysql/*.pid')
    sqlservicecheck(msqlpidf, msqlpid)
    dbcreds()
    createmysqldb()
    phpfpmconf()
    inphpcreater()
    print('MySQL, Nginx and PHP-FPM installed and configured...')

def fpgsqlinstaller():
    print(' You have chose PostgreSQL with PHP-FPM!')
    print(' Please be patient, it will take some time...')
    run('pkg install -y postgresql93-client')
    run('pkg install -y postgresql93-server php56 php56-pgsql ; sysrc postgresql_enable="YES" ; /usr/local/etc/rc.d/postgresql initdb')
    put(os.getcwd()+'/jinja2temps/f10postresql.conf', '/usr/local/pgsql/data/postgresql.conf')
    put(os.getcwd()+'/jinja2temps/f10pg_hba.conf', '/usr/local/pgsql/data/pg_hba.conf')
    run('/usr/local/etc/rc.d/postgresql start')
    pgsqlpid = run('ps waux|grep /usr/local/bin/postgres | grep -v grep | awk \'{ print $2 }\'')
    pgsqlpidf = run('cat /usr/local/pgsql/data/postmaster.pid | head -1')
    sqlservicecheck(pgsqlpidf, pgsqlpid)
    run('su - pgsql -c "createdb"')
    dbcreds()
    createpgsqldb(fuser)
    phpfpmconf()
    pgphpcreater()
    print('PostgreSQL, Nginx and PHP-FPM installed and configured...')

def nginstall():
    run('yum -y install epel-release')
    run('yum -y install nginx ; systemctl start nginx ; systemctl enable nginx')
    run('mkdir /etc/nginx/sites-enabled/ /etc/nginx/sites-available/')
    run('mkdir -p /var/www/'+sitename+'/html')
    put(os.getcwd()+'/jinja2temps/c7nginx.conf', '/etc/nginx/nginx.conf')
    run('chown -R nginx:nginx /var/www/ ; chmod -R 755 /var/www')

def c7vhostcreate():
    put(os.getcwd()+'/output/'+sitename+'.conf', '/etc/nginx/sites-available/')
    put(os.getcwd()+'/output/index.html', '/var/www/'+sitename+'/html/index.html')
    run('ln -s /etc/nginx/sites-available/* /etc/nginx/sites-enabled/')
    run('systemctl restart nginx')

def c7mysqlinstaller():
    print(' You have selected "Enter" button!!!')
    print(' Please be patient, it will take some time...')
    run('yum -y install php php-mysql php-fpm')
    put(os.getcwd()+'/jinja2temps/c7php.ini', '/etc/php.ini')
    put(os.getcwd()+'/jinja2temps/c7www.conf', '/etc/php-fpm.d/www.conf')
    run('systemctl start php-fpm ; systemctl enable php-fpm')
    run('yum -y install mariadb-server mariadb ; systemctl enable mariadb ; systemctl start mariadb')
    run('echo -e "\n\nfreebsd\nfreebsd\n\n\n\n\n" | mysql_secure_installation 2>/dev/null')
    msqlpidfile = run('ps waux|grep mysql | grep -v grep| grep -v safe | awk \'{ print $2 }\'')
    msqlpid = run('cat /var/run/mariadb/mariadb.pid')
    sqlservicecheck(msqlpidfile, msqlpid)
    dbcreds()
    createmysqldb()
    inphpcreater()
    run('systemctl restart nginx')
    print('MySQL, Nginx and PHP-FPM installed and configured...')

def c7pgsqlinstaller():
    print(' You have chose PostgreSQL with PHP-FPM!')
    print(' Please be patient, it will take some time...')
    run('yum -y install epel-release ; yum -y groupinstall "Development Tools" ; yum -y install php php-fpm php-gd php-pgsql php-mbstring php-xml ; yum -y install postgresql-server')
    run('postgresql-setup initdb')
    put(os.getcwd()+'/jinja2temps/c7php.ini', '/etc/php.ini')
    put(os.getcwd()+'/jinja2temps/c7www.conf', '/etc/php-fpm.d/www.conf')
    run('systemctl start php-fpm ; systemctl enable php-fpm')
    put(os.getcwd()+'/jinja2temps/f10pg_hba.conf', '/var/lib/pgsql/data/pg_hba.conf')
    put(os.getcwd()+'/jinja2temps/c7postresql.conf', '/var/lib/pgsql/data/postgresql.conf')   
    run('systemctl start postgresql ; systemctl enable postgresql')
    psqlpidf = run('ps waux|grep pgsql | grep -v grep | grep -v safe | awk \'{ print $2 }\'')
    psqlpid = run('cat /var/run/postgresql/.s.PGSQL.5432.lock | head -1')
    sqlservicecheck(psqlpidf, psqlpid)
    run('su - postgres -c "createdb"')
    dbcreds()
    createpgsqldb(cuser)
    phpfpmconf()
    pgphpcreater()
    print('PostgreSQL, Nginx and PHP-FPM installed and configured...')

with settings(
        hide('warnings', 'running', 'stdout', 'stderr'), 
        warn_only=True
):
    osver = run('uname -s')
    lintype = run('cat /etc/redhat-release | awk \'{ print $1 }\'')
    ftype = run('uname -v | awk \'{ print $2 }\' | cut -f1 -d \'.\'')

    if osver == 'FreeBSD' and ftype >= 10:
        print(' This is FreeBSD server...')
        getnginxbin = run('which nginx')
        nginxpidf = run('cat /var/run/nginx.pid')
        nginxpid = run('ps waux | grep nginx | grep root | grep -v grep | awk \'{ print $2 }\'')

        if getnginxbin == '/usr/local/sbin/nginx' and nginxpidf == nginxpid:
            ngprintexit()
        elif getnginxbin != '/usr/local/sbin/nginx':
            print(' Please be patient, installing nginx server...')
            run('pkg install -y nginx ; echo \'nginx_enable=\"YES\"\' >> /etc/rc.conf')
            hostnametohosts()
            put(os.getcwd()+'/jinja2temps/f10nginx.conf', '/usr/local/etc/nginx/nginx.conf')
            run('mkdir -p /usr/local/etc/nginx/sites-enabled/ /usr/local/etc/nginx/sites-available/ /var/www/'+sitename+'/html')
            vhhtmlwriter()
            put(os.getcwd()+'/output/'+sitename+'.conf', '/usr/local/etc/nginx/sites-available/')
            put(os.getcwd()+'/output/index.html', '/var/www/'+sitename+'/html/')
            run('ln -s /usr/local/etc/nginx/sites-available/* /usr/local/etc/nginx/sites-enabled/ ; service nginx restart')
            prandwainput()

            if inst == "1":
                fmysqlinstaller()
            elif inst == "2":
                fpgsqlinstaller()
            else:
                print('You pressed "Enter" button, exiting!!!')

    elif osver == 'Linux' and lintype == 'CentOS':
        print(' This is CentOS server...')
        getlngdpack = run('which nginx')
        ngpidfile = run('cat /var/run/nginx.pid')
        ngpid = run('ps waux | grep nginx | grep root | grep -v grep | awk \'{ print $2 }\'')

        if getlngdpack == '/usr/sbin/nginx' and ngpidfile == ngpid:
            ngprintexit()
        elif getlngdpack != '/usr/sbin/nginx':
            print(' Please be patient, installing nginx server...')
            nginstall()
            hostnametohosts()
            vhhtmlwriter()
            c7vhostcreate()
            prandwainput()

            if inst == "1":
                c7mysqlinstaller()
            elif inst == "2":
                c7pgsqlinstaller()
            else:
                print('You pressed "Enter" button, exiting!!!')

    else:
        print(' This script supports FreeBSD or CentOS7 server...')
