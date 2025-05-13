#$ -S /bin/bash
#$ -cwd
#$ -V
#$ -o Logs/
#$ -e Logs/
#$ -l qname=all.q

function get_checksum(){
    if [ ! -d $TMPDIR/checksum ]; then mkdir -p $TMPDIR/checksum; fi
    cd $TMPDIR
    md5sum $timestamp/*/*/*/* > $INFOFILE
}
