<?php
ini_set('display_errors', 1); //Enable error print to the screen
$dblocation = "localhost"; //IP address for the database
$dbname = "linuxdb"; //Database name to which we will connect
$dbuser = "linuxuser"; //New username for new database
$dbpasswd = "jh"; //Password for the new username

$dbcnx = @mysql_connect($dblocation, $dbuser, $dbpasswd);
if (!$dbcnx){
    echo "<p>So pity MySQL is not working</p>";
    exit();
}
if (!@mysql_select_db($dbname,$dbcnx)){
    echo "<p>We are sorry, to connect to the database was not successfully.</p>";
    exit();
}
$ver = mysql_query("SELECT VERSION()");
if(!$ver){
    echo "<p>Request error</p>";
    exit();
}
echo mysql_result($ver, 0);
?>
