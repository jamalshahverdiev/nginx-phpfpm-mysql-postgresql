<?php
 $db = pg_connect("host=127.0.0.1 port=5432 dbname=centosdb user=centosuser password=freebsd");
 $query = "INSERT INTO book VALUES ('$_POST[bookid]','$_POST[bookname]', '$_POST[author]','$_POST[publisher]','$_POST[dop]', '$_POST[price]')";
 $result = pg_query($query);
?>