#Ochkalova S, Tolstoganov I, Lapidus A, et al. Protocol for refining metagenomic binning with BinSPreader[J]. STAR protocols, 2023, 4(3): 102417.
#https://github.com/bxlab/metaWRAP/blob/master/bin/metawrap-modules/binning.sh
import os
import subprocess
import argparse

docker="meta:latest"
parser = argparse.ArgumentParser("Binning with metaBAT2+CheckM+GTDB-Tk.")
parser.add_argument("-p1","--pe1",help="R1 fastq",required=True)
parser.add_argument("-p2","--pe2",help="R2 fastq",default=None)
parser.add_argument('-c','--contig',type=str,required=True,help='contig sequence')
parser.add_argument('-o','--outdir',type=str,help='output directory',default=os.getcwd())
parser.add_argument("-g",'--gtdbtk',help="GTDB-Tk reference data",default=None)
parser.add_argument("-m2",'--checkm2',help="a location for the CheckM2 database",default=None)
parser.add_argument("-m1",'--checkm1',help="a location for the CheckM1 database",default=None)
parser.add_argument("-t","--threads",help="number of threads(defualt 24)",default=24)
parser.add_argument('-p','--prefix',type=str,required=True,help='prefix for output files')
args=parser.parse_args()


if not os.path.exists(args.outdir):
    os.makedirs(args.outdir)
args.outdir=os.path.abspath(args.outdir)
################################reads mapping contigs
args.pe1=os.path.abspath(args.pe1)
indir=os.path.dirname(args.pe1)
args.contig=os.path.abspath(args.contig)
ref=os.path.dirname(args.contig)
cmd=f'docker run -v {ref}:/ref/ -v {indir}:/raw_data/ -v {args.outdir}:/outdir {docker} sh -c \'export PATH=/opt/conda/envs/rgi/bin:$PATH'
if args.pe2 is not None:
    args.pe2=os.path.abspath(args.pe2)
    if indir!=os.path.dirname(args.pe2):
        print("read1 and reads2 must be in the same directory.")
        exit()
    else:
        cmd += f' && minimap2 -t {args.threads} -a -x sr /ref/{args.contig.split("/")[-1]} /raw_data/{args.pe1.split("/")[-1]} /raw_data/{args.pe2.split("/")[-1]} | samtools view -F 3584 -b -o - | samtools sort -@ {args.threads} -o /outdir/{args.prefix}.bam'
else:
    cmd += f' && minimap2 -t {args.threads} -a -x sr /ref/{args.contig.split("/")[-1]} /raw_data/{args.pe1.split("/")[-1]} | samtools view -F 3584 -b -o - | samtools sort -@ {args.threads} -o /outdir/{args.prefix}.bam'
################################Run MetaBAT2
cmd+=f" && jgi_summarize_bam_contig_depths --outputDepth /outdir/{args.prefix}.abundances.tsv /outdir/{args.prefix}.bam"
cmd+=(f' && metabat2 -i /ref/{args.contig.split("/")[-1]} -a /outdir/{args.prefix}.abundances.tsv -o /outdir/{args.prefix}_bin/bin '
      f'--numThreads {args.threads} --seed 42 -m 1500 --unbinned\'')
print(cmd)
subprocess.run(cmd, shell=True)
################################Run CheckM
if args.checkm1 is not None:
    ref = os.path.abspath(args.checkm1)
    if os.path.exists(f'{args.outdir}/{args.prefix}_bin/CheckM1'):
        subprocess.check_call(f'rm -rf {args.outdir}/{args.prefix}_bin/CheckM1',shell=True)
    cmd=f'docker run -v {args.outdir}:/outdir -v {ref}:/ref/ {docker} sh -c \' '
    cmd+=(f'export PATH=/opt/conda/envs/checkm2/bin/:$PATH && export CHECKM_DATA_PATH=/ref/ && '
          f'checkm lineage_wf -f /outdir/{args.prefix}_bin/CheckM1/SCG.txt '
          f'-t {args.threads} -x fa '
          f'/outdir/{args.prefix}_bin/ '
          f'/outdir/{args.prefix}_bin/CheckM1\'')
    print(cmd)
    subprocess.run(cmd, shell=True)
################################Run CheckM2
if args.checkm2 is not None:
    ref=os.path.abspath(args.checkm2)
    index = ""
    for i in os.listdir(ref):
        if i.endswith(".dmnd"):
            index = i
    if os.path.exists(f'{args.outdir}/{args.prefix}_bin/CheckM2'):
        subprocess.check_call(f'rm -rf {args.outdir}/{args.prefix}_bin/CheckM2',shell=True)
    cmd=f'docker run -v {args.outdir}:/outdir -v {ref}:/ref/ {docker} sh -c \' '
    cmd+=(f'export PATH=/opt/conda/envs/checkm2/bin/:$PATH && '
          f'checkm2 predict --threads {args.threads} -x fa '
          f'--database_path /ref/{index} '
          f'--input /outdir/{args.prefix}_bin/ '
          f'--output-directory /outdir/{args.prefix}_bin/CheckM2\'')
    print(cmd)
    subprocess.run(cmd, shell=True)

################################GTDB-Tk
if args.gtdbtk is not None:
    ref=os.path.abspath(args.gtdbtk)
    cmd=f'docker run -v {ref}:/ref/ -v {args.outdir}:/outdir {docker} sh -c \''
    cmd+=(f'export PATH=/opt/conda/envs/gtdbtk/bin:$PATH && export GTDBTK_DATA_PATH=/ref/ && '
          f'gtdbtk classify_wf --cpus {args.threads} '
          f'--genome_dir /outdir/{args.prefix}_bin/ --skip_ani_screen '
          f'--out_dir /outdir/ -x fa --prefix {args.prefix}.gtdbtk\'')
    print(cmd)
    subprocess.check_call(cmd, shell=True)
