#!/bin/bash

# make_page - A script to produce an HTML file

title="My System Information"

cat << EOD > newdata.html
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
        
    <title>$title</title>

</head>
<body>
    <p>Updated on $(date +"%x %r %Z") by $USER</p>
</body>
</html>
EOD