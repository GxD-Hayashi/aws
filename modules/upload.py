import os
import sys
import argparse
import pymysql
import warnings
import datetime
import shutil
import gzip
import errno
import pandas as pd
from pathlib import Path
from .common import *

TMPLATE = Path(os.path.abspath(__file__)).parent.parent / "template" / "template.UL.sh"
TMPLATE2 = Path(os.path.abspath(__file__)).parent.parent / "template" / "template.CS.sh"

if not os.path.isfile(TMPLATE) :
    init("No template file (template.UL.sh) exists.")
if not os.path.isfile(TMPLATE) :
    init("No template file (template.CS.sh) exists.")

def getinfo(fc_id):
    try :
        connection = pymysql.connect(host="192.168.9.100", user="gxd_pipeline", password="gw!2341234", database="gxd")
    except Exception as e:
        sys.exit({e})
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        db_tbl = pd.read_sql(SelectData(fc_id), connection)
    return db_tbl

def SelectData(fc_id):
    query = f"""
    SELECT tesh.run_id, concat(tesh.equip_side, tesh.fc_id) AS sub_name, gp.PRJ_TYPE, ghl.ANAL_STATUS, gp.SAMPLE_ID
    FROM gxd.tb_expr_seq_header tesh
    INNER JOIN gxd.gc_qc_sample gqs
    ON tesh.run_id = gqs.run_id
    INNER JOIN gxd.gc_project gp
    ON gqs.SAMPLE_ID = gp.SAMPLE_ID
    INNER JOIN gxd.gc_history_log ghl
    ON gqs.SAMPLE_ID = ghl.SAMPLE_ID
    AND ghl.idx = (SELECT MAX(idx) FROM gc_history_log WHERE SAMPLE_ID = gqs.SAMPLE_ID)
    WHERE tesh.fc_id = '{fc_id}'
    """
    return query

def fcDir_table(df, novaseqDir: Path):
    df = df[['sub_name','PRJ_TYPE']].drop_duplicates()
    df['seqDir'] = None

    for i, item in df.iterrows() :
        fcDir = Search_fcDir(item['sub_name'], Path(novaseqDir + '/' + item['PRJ_TYPE']), True)
        df.loc[i,'seqDir'] = fcDir

    df = df.dropna(subset=['seqDir'])

    return df

def Search_fcDir(batchID, novaseqDir : Path, full):

    fcDirs = [fcDir for fcDir in novaseqDir.iterdir() if fcDir.name.endswith(batchID)]
    fcDirs.sort()
    if len(fcDirs) != 1: return None
    if full :
        return os.path.abspath(fcDirs[-1])
    else:
        return os.path.basename(fcDirs[-1])

def check_files(sampleID, prj_type, analDir, linkDir:Path):
    os.makedirs(linkDir / sampleID, exist_ok=True)

    if prj_type == 'eWES':
        FQ1 = os.path.realpath( os.path.join(analDir, sampleID, 'Fastq', sampleID + '.tumour.R1.fastq.gz') )
        FQ2 = os.path.realpath( os.path.join(analDir, sampleID, 'Fastq', sampleID + '.tumour.R2.fastq.gz') )
        VCF = os.path.join(analDir, sampleID, 'SNV', 'somatic', sampleID + '_mutect2_freebayes_lofreq_vote_res.exome.vcf')
        VCF_ZIP = os.path.join(linkDir, sampleID, sampleID + '_mutect2_freebayes_lofreq_vote_res.exome.vcf.gz')

        if not os.path.isfile(FQ1) :
            return FQ1 + ': File does not exist.'
        if not os.path.isfile(FQ2) :
            return FQ2 + ': File does not exist.'
        if not os.path.isfile(VCF) :
            return VCF + ': File does not exist.'

        flag = symlink_force(Path(FQ1), linkDir / sampleID / f"{sampleID}.R1.fastq.gz")
        if flag :
            return f"{sampleID}.R1.fastq.gz: Symbolic link creation failure."
        flag = symlink_force(Path(FQ2), linkDir / sampleID / f"{sampleID}.R2.fastq.gz")
        if flag :
            return f"{sampleID}.R2.fastq.gz: Symbolic link creation failure."

        if os.path.isfile(VCF_ZIP) : os.remove(VCF_ZIP)
        with open(VCF, 'rb') as f_in:
            with gzip.open(VCF_ZIP, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        return 'success'

    elif prj_type == 'WTS':
        FQ1 = os.path.realpath( os.path.join(analDir, sampleID, 'Fastq', f"{sampleID}.R1.fastq.gz") )
        FQ2 = os.path.realpath( os.path.join(analDir, sampleID, 'Fastq', f"{sampleID}.R2.fastq.gz") )
        if not os.path.isfile(FQ1) :
            return FQ1 + ': File does not exist.'
        if not os.path.isfile(FQ2) :
            return FQ2 + ': File does not exist.'

        flag = symlink_force(FQ1, linkDir / sampleID / f"{sampleID}.R1.fastq.gz")
        if flag :
            return f"{sampleID}.R1.fastq.gz: Symbolic link creation failure."
        flag = symlink_force(FQ2, linkDir / sampleID / f"{sampleID}.R2.fastq.gz")
        if flag :
            return f"{sampleID}.R2.fastq.gz: Symbolic link creation failure."

        return 'success'

def symlink_force(target: Path, link_name):
    try:
        os.symlink(target, link_name)
        return False
    except OSError as e:
        if e.errno == errno.EEXIST:
            os.remove(link_name)
            os.symlink(target, link_name)
            return False
        elif e.errno == errno.ENOENT :
            os.makedirs(os.path.dirname(os.path.abspath(link_name)), exist_ok=True)
            os.symlink(target, link_name)
            return False
        else:
            return True

def run_upload(args):

    now = datetime.datetime.now()
    now_str = str(now.strftime("%Y%m%d%H%M%S"))

    flowcellid = args.flowcellid
    directory = args.directory
    project_type = args.project_type
    inclusion = [x.strip() for x in args.inclusion.split(',') if not x.strip() == '']
    exclusion = [x.strip() for x in args.exclusion.split(',') if not x.strip() == '']
    srcdir = args.srcdir

    inclusion = rmdup_list(inclusion)
    exclusion = rmdup_list(exclusion)

    if len(inclusion) > 0 and len(exclusion) > 0:
        init('ERROR: Inclusion and exclusion cannot be specified simultaneously.')

    df_info = getinfo(flowcellid)
    if df_info.shape[0] == 0 : init("No matching data found.")

    if len(inclusion) > 0:
        print ("inclusion sample: " + ",".join(inclusion))
        df_info = df_info[ df_info['SAMPLE_ID'].isin(inclusion)]
        mismatch = set(inclusion) - set(df_info['SAMPLE_ID'])
        if len(mismatch) > 0 :
            print('No entries in database: [' + ','.join(mismatch) + ']')
        if df_info.shape[0] == 0 : init("No corresponding sample IDs.")

    if len(exclusion) > 0:
        print ("exclusion sample: " + ",".join(exclusion))
        df_info = df_info[ ~df_info['SAMPLE_ID'].isin(exclusion)]
        if df_info.shape[0] == 0 : init("No corresponding sample IDs.")

    df_info['PRJ_TYPE'] = df_info['PRJ_TYPE'].str.replace('EWES',"eWES")
    if project_type == "both" :
        df_info[ df_info['PRJ_TYPE'].isin(['eWES','WTS']) ]
    else :
        df_info = df_info[ df_info['PRJ_TYPE']==project_type]
    if df_info.shape[0] == 0 : init("Test type error: no sample ID corresponds.")

    uniq_info = fcDir_table(df_info, directory)
    if uniq_info.shape[0] == 0: init("No samples to forward.")

    luck_samples = []
    out_bash_1 = Path(srcdir) / f"upload.{now_str}.sh"
    out_bash_2 = Path(srcdir) / f"checksum.{now_str}.sh"
    os.makedirs(srcdir, exist_ok=True)

    try :
        shutil.copy2(TMPLATE, out_bash_1)
    except FileExistsError as e:
        shutil.rmtree(srcdir / now_str)
        init(f'File does not exist.')
    except PermissionError as e:
        shutil.rmtree(srcdir / now_str)
        init(f'Error due to authorisation.')
    except Exception as e:
        shutil.rmtree(srcdir / now_str)
        init(f'unexpected error:{e}')

    try :
        shutil.copy2(TMPLATE2, out_bash_2)
    except FileExistsError as e:
        shutil.rmtree(srcdir / now_str)
        init(f'File does not exist.')
    except PermissionError as e:
        shutil.rmtree(srcdir / now_str)
        init(f'Error due to authorisation.')
    except Exception as e:
        shutil.rmtree(srcdir / now_str)
        init(f'unexpected error:{e}')

    with open(out_bash_1, 'a') as f:
        print('timestamp=' + now_str, file=f)
        print('TMPDIR='+ srcdir, file=f)
        print('INFOFILE=' + srcdir + '/checksum/' + now_str + '.txt' + '\n', file=f)

    with open(out_bash_2, 'a') as f:
        print('timestamp=' + now_str, file=f)
        print('TMPDIR='+ srcdir, file=f)
        print('INFOFILE=' + srcdir + '/checksum/' + now_str + '.txt' + '\n', file=f)
        print("get_checksum\n" , file=f)
     
    for i, item1 in uniq_info.iterrows() :

        if item1['PRJ_TYPE'] == 'WTS' :
            tr_dir = 'gxd-wts'
        elif item1['PRJ_TYPE'] == 'eWES' :
            tr_dir = 'gxd-ewes'
        else :
            continue

        outdir = Path(os.path.abspath(srcdir)) / now_str / tr_dir / os.path.basename(item1['seqDir'])
        temp_info = df_info[ (df_info['sub_name']==item1['sub_name']) & (df_info['PRJ_TYPE']==item1['PRJ_TYPE']) ].reset_index(drop=True)

        for j, item2 in temp_info.iterrows() :

            link_flag = check_files(item2['SAMPLE_ID'], item2['PRJ_TYPE'], item1['seqDir'], outdir)
            if not link_flag == 'success' :
                print(link_flag)
                luck_samples.append(item2['SAMPLE_ID'])
                shutil.rmtree(outdir / item2['SAMPLE_ID'])
                continue

        with open(out_bash_1, 'a') as f:
            print('FOLDER=' + ','.join( set([os.path.basename(a) for a in uniq_info[uniq_info['PRJ_TYPE']==item1['PRJ_TYPE']]['seqDir']]) ), file=f)
            print('tr_dir=' + tr_dir, file=f)
            print('JSONFILE=' + srcdir + '/info/' + now_str + '.' + item1['PRJ_TYPE'] + '.json', file=f)
            print('ERRORFILE=' + srcdir + '/' + now_str + '.' + item1['PRJ_TYPE'] + '.error', file=f)
            print("data_upload\nget_info\ncheck_size\n", file=f)

    if len(luck_samples) > 0 :
        print('Missing file:\n' + '\n'.join(luck_samples))
        os.remove(out_bash_1)
        os.remove(out_bash_2)
        init('Stop creating script files for transfer.')

