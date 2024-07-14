#!/bin/bash

movies=0
rm movielist
for dir in $1
do
  (cd "$dir" && pwd|cut -d \/ -f5|tr -s '\n' ', ' >> ../../movielist &&
    exiftool * -t -s3 -ImageSize -FileType|tr -s '\t' ',' >> ../../movielist )
echo "Movie $movies - $dir ADDED!"
let movies=movies+1
done

rm moviefinal
cat movielist | while read MovieName;
do 
    echo "$MovieName" | cut -d ',' -f2 | cut -d 'x' -f2 | sort | uniq | while read MovieRes;
    do
        if (($MovieRes>=461 && $MovieRes<=660))
        then
            echo "$MovieName,480p" 
        elif (($MovieRes>=661 && $MovieRes<=890))
        then
            echo "$MovieName,720p" 
        elif (($MovieRes>=891 && $MovieRes<=1200))
        then
            echo "$MovieName,1080p"
        else
            echo "$MovieName,DVD" 
        fi >> moviefinal
    done    
done
