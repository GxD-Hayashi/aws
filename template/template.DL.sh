#$ -S /bin/bash
#$ -cwd
#$ -V
#$ -o Logs/
#$ -e Logs/
#$ -l qname=all.q

function data_restore(){

    while read batch sample file chsum tr_dir; do
        aws s3api restore-object --bucket $tr_dir --key $batch/$sample/$file --restore-request Days=7
    done < $INFOFILE

    echo "Finish restore request."
}

function data_download(){

    while read batch sample file chsum tr_dir; do

        is_restored=false
        while [ "$is_restored" = false ]; do
            result=$(aws s3api head-object --bucket $tr_dir --key $batch/$sample/$file --query "Restore" --output text 2>&1)
            if [[ "$result" == *"ongoing-request=\"false\""* ]]; then
                is_restored=true
            else
                sleep 10m
            fi
        done

        if [ ! -d $TMPDIR/data/$batch/$sample ]; then mkdir -p $TMPDIR/data/$batch/$sample; fi
        cd $TMPDIR/data/$batch/$sample
        aws s3 cp s3://$tr_dir/$batch/$sample/$file ./$file

    done < $INFOFILE

}


function checksum(){

    if [ ! -d $(dirname $CHSFILE) ]; then mkdir -p $(dirname $CHSFILE); fi
    declare -A FAIL=()
    while read batch sample file chsum tr_dir; do
        if [ -s $TMPDIR/data/$batch/$sample/$file ]; then
            cd $TMPDIR/data/$batch/$sample
            declare -a VAL=(`md5sum $file`)
            echo ${VAL[@]} >> $CHSFILE
            if [ $chsum != ${VAL[0]} ]; then
                FAIL[$file]='mismatch'
            fi
        else
            FAIL[$file]='not_exists'
        fi
    done < $INFOFILE

    if [ ${#FAIL[@]} -ne 0 ]; then
        echo -ne "" > $ERRFILE
        for file in ${!FAIL[@]}; do
            echo -e "${file}\t${FAIL[$file]}" >> $ERRFILE
        done
    fi
}
