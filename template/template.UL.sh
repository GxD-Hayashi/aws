#$ -S /bin/bash
#$ -cwd
#$ -V
#$ -o Logs/
#$ -e Logs/
#$ -l qname=all.q

function data_upload() {
    aws s3 sync $TMPDIR/$timestamp/$tr_dir s3://$tr_dir/ --storage-class DEEP_ARCHIVE --exact-timestamps
}

function get_info() {
    echo -ne "" > $JSONFILE
    for f in `echo $FOLDER | sed -e "s/,/ /g"`; do
        aws s3api list-objects-v2 --bucket $tr_dir --prefix $f/ >> $JSONFILE
    done
}

function check_size(){
    for sub in `echo $FOLDER | sed -e "s/,/ /g"`; do
        cd $TMPDIR/$timestamp/$tr_dir/$sub
        for FILE in `ls ./*/*`; do
            raw_size=$(stat -Lc %s "$FILE")
            s3_info=$(aws s3api head-object --bucket "$tr_dir" --key "$sub/$FILE" 2>/dev/null)
            if [ $? -ne 0 ]; then
                echo "[ERROR] $timestamp/$tr_dir/$sub/$FILE not found in S3." >> $ERRORFILE
                continue
            fi
            s3_size=$(echo "$s3_info" | grep '"ContentLength"' | sed -E 's/[^0-9]*([0-9]+).*/\1/')
            if [ "$raw_size" -ne "$s3_size" ]; then
                echo "[MISMATCH] $timestamp/$tr_dir/$sub/$FILE size mismatch." >> $ERRORFILE
            fi
        done
    done
}

