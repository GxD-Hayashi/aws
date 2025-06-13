import os
import sys
import argparse
from pathlib import Path
from modules import *

VERSION="v3.0.0"

def main():

    if '--help' in sys.argv or '-h' in sys.argv:
        print(f"version: {VERSION}")

    parser = argparse.ArgumentParser(description="Backup analysis data to AWS.")
    parser.add_argument('--version','-v', action='version', version=f'%(prog)s {VERSION}')
    subparsers = parser.add_subparsers(dest="command", required=True)

    # upload
    parser_ul = subparsers.add_parser("upload", aliases=['up'], help="Upload to AWS.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_ul.add_argument("--flowcellid","-fc", required=True, help="flowcell id")
    parser_ul.add_argument("--project_type","-t", required=True, help="project type", default=None, choices=["WTS","eWES"])
    parser_ul.add_argument("--directory","-d", required=False, help="parent analytical directory", default="/data1/data/result")
    parser_ul.add_argument("--inclusion","-i", required=False, help="sample IDs to include (comma separated)", default="")
    parser_ul.add_argument("--exclusion","-e", required=False, help="sample IDs to exclude (comma separated)", default="")
    parser_ul.add_argument("--srcdir","-s", required=False, help="output destination for bash files", default="/data1/work/AWS/uploads")
    parser_ul.set_defaults(func=run_upload)

    # download
    parser_dl = subparsers.add_parser("download", aliases=['dl'], help="Download from AWS.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_dl.add_argument("--sample","-s", required=False, help="sample ID (comma separated)")
    parser_dl.add_argument("--listfile","-f", required=False, help="List of samples to be download.")
    parser_dl.add_argument("--srcdir","-d", required=False, help="output destination for bash files", default="/data1/work/AWS/downloads")
    parser_dl.set_defaults(func=run_download)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":

    main()

