import os,re,sys
import argparse
import subprocess
import math

docker="meta:latest"
parser = argparse.ArgumentParser("")
parser.add_argument('-pr','--protein',type=str,required=True,help="protein fasta file")
parser.add_argument('-o','--outdir',type=str,help="output directory",default=os.getcwd())
parser.add_argument('-p','--prefix',type=str,help="prefix of output files",required=True)
parser.add_argument("-v","--vfdb",type=str,help="vfdb fasta file",required=True)
parser.add_argument("-t","--threads",help="number of threads(defualt 24)",default=24)
args = parser.parse_args()

if not os.path.isdir(args.outdir):
    os.mkdir(args.outdir)
args.outdir=os.path.abspath(args.outdir)
args.protein=os.path.abspath(args.protein)
args.vfdb=os.path.abspath(args.vfdb)
db=""
if os.path.isfile(args.vfdb):
    for i in os.listdir(os.path.dirname(args.vfdb)):
        if i.endswith(".pdb"):
            db = i.split(".pdb")[0]
if os.path.isdir(args.vfdb):
    for i in os.listdir(args.vfdb):
        if i.endswith(".pdb"):
            db = i.split(".pdb")[0]
print(db)
cmd=(f"docker run -v {args.outdir}:/outdir/ "
     f"-v {os.path.dirname(args.protein)}:/raw_data "
     f"-v {os.path.dirname(args.vfdb)}:/ref/ {docker} "
     f"sh -c \'export PATH=/opt/conda/envs/rgi/bin:$PATH && ")
query=args.protein.split("/")[-1]

cmd+=(f"blastp -query /raw_data/{query} -db /ref/{db} "
      f"-outfmt \"6 qseqid sseqid pident length mismatch evalue qcovs qcovhsp\" "
      f"-evalue 1e-10 -max_target_seqs 5 -num_threads {args.threads} -out /outdir/{args.prefix}.vfdb.tsv\'")
print(cmd)
subprocess.call(cmd,shell=True)
VF,VFC={},{}
infile=open(args.vfdb,"r")
for line in infile:
    line=line.strip()
    if line.startswith(">"):
        array=line[1:].split(" ")
        print(array[0])
        VFID=re.search(r'.*(VF\d+).*',line, re.M|re.I)
        VFCID=re.search(r'.*(VFC\d+).*',line,re.M|re.I)
        VF[array[0]]=VFID.group(1)
        VFC[array[0]]=VFCID.group(1)
infile.close()

infile=open(args.outdir+"/"+args.prefix+'.vfdb.tsv','r')
outfile=open(args.outdir+"/"+args.prefix+'.vfdb.clean.tsv','w')
outfile.writelines("query\tref\tpid\tAlignment_length\tmismatch\tExpect value\tQuery Coverage Per Subject\tQuery Coverage Per HSP\tVFID\tVFCID\n")
query={}
for line in infile:
    line=line.strip()
    array=line.split("\t")
    if float(array[2])>80 and float(array[6])>80 and float(array[7])>50:#identity >80% and query coverage > 80% and Query Coverage Per HSP>50
        if array[0] not in query:
            query[array[0]]=line
        else:
            if float(query[array[0]].split("\t")[5])==0:
                pass
            else:
                if float(array[5])<float(query[array[0]].split("\t")[5]):
                    query[array[0]]=line
infile.close()
for key in query:
    ref=query[key].split("\t")[1]
    outfile.write(f"{query[key]}\t{VF[ref]}\t{VFC[ref]}\n")
outfile.close()