# Email:yucai.fan@illumina.com
import multiprocessing
import os,sys,re
import subprocess
import argparse

parser = argparse.ArgumentParser("\nMetagenomics pipeline.\nEmail:yucai.fan@illumina.com\n")
parser.add_argument("-p1","--pe1",help="comma-separated list of fasta/q paired-end #1 files",required=True)
parser.add_argument("-p2","--pe2",help="comma-separated list of fasta/q paired-end #2 files",required=True)
parser.add_argument("-o","--outdir",help="output directory",default=os.getcwd())
parser.add_argument("-p","--prefix",help="prefix of output files")
parser.add_argument("-h","--host",help="path of bowtie2 host index")
parser.add_argument("-k","--kraken2",help="kraken2 database")
parser.add_argument("-m1","--checkm1",help="checkm1 database")
parser.add_argument('-s','--staramr',help='staramr database directory')
parser.add_argument("-g",'--gtdbtk',help="GTDB-Tk reference data")
parser.add_argument("-m","--metaphlan",help="directory contains metaphlan index")
args = parser.parse_args()

