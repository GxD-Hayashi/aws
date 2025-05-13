#$ -S /bin/bash
#$ -cwd
#$ -V
#$ -o Logs/
#$ -e Logs/
#$ -l qname=all.q

function data_upload() {
    aws s3 sync $TMPDIR/$timestamp/$tr_dir s3://$tr_dir/ --storage-class DEEP_ARCHIVE
}

function get_info() {
    echo -ne "" > $JSONFILE
    for f in `echo $FOLDER | sed -e "s/,/ /g"`; do
        aws s3api list-objects-v2 --bucket $tr_dir --prefix $f/ >> $JSONFILE
    done
}
