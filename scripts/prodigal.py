import os
import sys
import subprocess
import argparse


docker="meta:latest"
def run(contig,prefix,outdir):
    contig=os.path.abspath(contig)
    file_name=contig.split("/")[-1]
    in_dir=os.path.dirname(contig)
    outdir=os.path.abspath(outdir)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    cmd=(f"docker run -v {in_dir}:/raw_data/ -v {outdir}:/outdir/ {docker} sh -c \'/opt/conda/envs/rgi/bin/prodigal "
         f"-f gff -i /raw_data/{file_name} -o /outdir/{prefix}.gff "
         f"-a /outdir/{prefix}.proteins.faa -d /outdir/{prefix}.gene.fna -p meta\'")
    print(cmd)
    subprocess.check_call(cmd,shell=True)

if __name__ == '__main__':
    parser=argparse.ArgumentParser("Fast, reliable protein-coding gene prediction for prokaryotic genomes.")
    parser.add_argument("-f","--fasta",help="fasta genome sequence",required=True)
    parser.add_argument("-p","--prefix",help="prefix of output files",required=True)
    parser.add_argument("-o","--outdir",help="output directory",required=True)
    args=parser.parse_args()
    run(args.fasta,args.prefix,args.outdir)