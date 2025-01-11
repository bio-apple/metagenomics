import os,sys,re
import subprocess
import argparse

docker="meta:latest"
def run(R1,R2,prefix,outdir,db):
    R1=os.path.abspath(R1)
    db=os.path.abspath(db)
    outdir = os.path.abspath(outdir)
    if not os.path.exists(outdir):
        subprocess.check_call('mkdir -p %s' % outdir, shell=True)
    db_name=db.split('/')[-1]
    cmd = (f"docker run -v {outdir}:/outdir/ -v {os.path.dirname(db)}:/ref/ -v {os.path.dirname(R1)}:/raw_data/ {docker} sh -c\'"
           f"diamond blastx --fast --threads 48 --evalue 0.00001 --max-target-seqs 1 "
           f"--outfmt 6 qseqid sseqid evalue length pident staxids sscinames sskingdoms skingdoms sphylums "
           f"--db /ref/{db_name}")
    if not R2==None:
        R2=os.path.abspath(R2)
        if R2.endswith(".gz") and R1.endswith(".gz"):
            subprocess.check_call(f"zcat {R1} {R2} >{outdir}/{prefix}.merge.fastq",shell=True)
        else:
            subprocess.check_call("cat {R1} {R2} >{outdir}/{prefix}.merge.fastq",shell=True)
        cmd+=f"-q /outdir/{prefix}.merge.fastq"
    else:
        file=R1.split("/")[-1]
        cmd += f"-q /raw_data/{file}"
    subprocess.check_call(cmd, shell=True)
    subprocess.check_call("rm -rf %s/%s.merge.fastq" % (args.outdir, args.prefix), shell=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("")
    parser.add_argument("-p1","--pe1",help="R1 fastq file",required=True)
    parser.add_argument("-p2","--pe2",help="R2 fastq file",default=None)
    parser.add_argument("-p","--prefix",help="prefix of output",required=True)
    parser.add_argument("-o","--outdir",help="output directory",required=True)
    parser.add_argument("-d","--db",help="diamond database file,**.dmnd",required=True)
    args = parser.parse_args()
    run(args.pe1,args.pe2,args.prefix,args.outdir,args.db)