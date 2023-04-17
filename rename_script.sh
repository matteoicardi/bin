#! /bin/bash

IFS='
'

ls > contents

CRDIR=$( pwd )

for FILE in ` ls `
      do 
            if [ -d $FILE ];then
                  DIR=$( echo $CRDIR/$FILE )
                  DIR=$(echo $DIR | tr -d ' ')
            fi

cd $DIR

for f in *; do # turn all spaces into underscores
   FILEOLD=\"$f\"
   FILEOLD=$( echo $FILEOLD | tr -d  '"')
   FILE=$( echo \"$f\" | tr [:space:]  _)
   FILE=$( echo $FILE | tr -d  '"')

 echo 
   echo ${FILE%.pdf_}.pdf
   echo 'Do you want to change the name of the file? [y/n]'
   read ANS
   echo $ANS
   if [ "$ANS" == "y" ];then
      echo 'Write the new name for the file'
      /usr/bin/evince $FILEOLD &
      read FILE
      echo $FILE
      mv $FILEOLD $FILE 
      kill -15 `pidof evince`
   else
      if [ ! ${FILE%.pdf_}.pdf == "$FILEOLD" ];then
            mv $FILEOLD ${FILE%.pdf_}.pdf
      fi
   fi
done

cd ..

      done 

