import os
import sys
import json
import shutil
import datetime
import argparse
import subprocess
import pandas as pd
from pathlib import Path
from .common import *

TMPLATE = Path(os.path.abspath(__file__)).parent.parent / "template" / "template.DL.sh"

if not os.path.isfile(TMPLATE) :
    init("No template file (template.DL.sh) exists.")

def extraction(json_ewes, json_wts):

    df_ewes = load_json(json_ewes)
    df_wts = load_json(json_wts)
    df_ewes['prj_type'] = 'gxd-ewes'
    df_wts['prj_type'] = 'gxd-wts'
    df = pd.concat([df_ewes, df_wts], ignore_index=True)

    return df

def load_json(json_file):

    try:
        df_data = json.load(open(json_file, 'r'))
        df_data = pd.DataFrame(df_data['Contents'])
        df_data['ETag'] = [ x.replace('"','') for x in df_data['ETag'] ]
        df_data['batch'] = [ x.split('/')[0] for x in df_data['Key'] ]
        df_data['sample'] = [ x.split('/')[1] for x in df_data['Key'] ]
        df_data['file'] = [ x.split('/')[2] for x in df_data['Key'] ]
        df_data = df_data[['batch','sample','file','ETag']]
    except :
        print(f"Failure to load JSON file:{json_file}")
        df_data = pd.DataFrame(columns=['batch','sample','file','ETag'])

    return df_data

def run_download(args):

    now = datetime.datetime.now()
    now_str = str(now.strftime("%Y%m%d%H%M%S"))

    listfile = args.listfile
    sampleIDs = args.sample
    srcdir = args.srcdir

    if listfile is None :
        if sampleIDs is None :
            init('Incorrect argument specified.')
        else :
            sampleIDs = [x.strip() for x in sampleIDs.split(',') if not x.strip() == '']
    elif not os.path.isfile(listfile) :
        init('List file does not exist.')
    else :
        with open(listfile, 'r') as f:
            try:
                sampleIDs = f.read().splitlines()
            except FileNotFoundError as e:
                init(e)

    sampleIDs = rmdup_list(sampleIDs)

    JSON_wts = Path(srcdir) / "info" / f"{now_str}.gxd-wts.json"
    JSON_ewes = Path(srcdir) / "info" / f"{now_str}.gxd-ewes.json"
    INFOFILE = Path(srcdir) / "info" / f"{now_str}.tsv"
    SHFILE = Path(srcdir) / f"download.{now_str}.sh"
    SUMFILE = Path(srcdir) / 'checksum' / f"{now_str}.txt"
    ERRFILE = Path(srcdir) / f"error.{now_str}"

    os.makedirs(Path(srcdir) / "info", exist_ok=True)

    try :
        with open(JSON_wts, "w") as f:
            result = subprocess.run(['aws','s3api','list-objects-v2','--bucket', 'gxd-wts'], stdout=f, text=True)
    except subprocess.CalledProcessError as e:
        init(f"aws s3api error: {e}")

    try :
        with open(JSON_ewes, "w") as f:
            result = subprocess.run(['aws','s3api','list-objects-v2','--bucket', 'gxd-ewes'], stdout=f, text=True)
    except subprocess.CalledProcessError as e:
        init(f"aws s3api error: {e}")

    df = extraction(JSON_ewes, JSON_wts)
    os.remove(JSON_wts)
    os.remove(JSON_ewes)

    not_exist = list(set(sampleIDs) - set(df['sample']))
    if len(not_exist) > 0:
        print('The following samples have not been uploaded to AWS.')
        print('\n'.join(not_exist))

    df = df[ df['sample'].isin(sampleIDs) ]
    if df.shape[0] > 0 :
        df.to_csv(INFOFILE, index=False, header=False, sep="\t")
    else:
        init(f"No relevant samples available.")

    shutil.copy2(TMPLATE, SHFILE)
    with open(SHFILE, 'a') as f:
        print("timestamp=" + f"{now_str}", file=f)
        print("TMPDIR=" + str(srcdir), file=f)
        print("INFOFILE=" + str(INFOFILE), file=f)
        print("CHSFILE=" + str(SUMFILE), file=f)
        print("ERRFILE=" + str(ERRFILE), file=f)
        print("data_restore\nsleep 5h\ndata_download\nchecksum", file=f)
