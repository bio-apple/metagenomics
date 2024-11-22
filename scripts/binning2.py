#Banerjee G, Papri S R, Banerjee P. Protocol for the construction and functional profiling of metagenome-assembled genomes for microbiome analyses[J]. STAR protocols, 2024, 5(3): 103167.
import os,sys,re
import subprocess
import argparse

docker="meta:latest"
parser = argparse.ArgumentParser("metaWRAP:binning process with CONCOCT, MaxBin2, and metaBAT2.\n")
parser.add_argument("-f","--fasta",help="final assembly fasta",required=True)
parser.add_argument("-o","--outdir",help="output directory",default=os.getcwd())
parser.add_argument("-m1",'--checkm1',help="a location for the CheckM1 database",required=True)
parser.add_argument("-p1","--pe1",help="R1 fastq",required=True)
parser.add_argument("-p2","--pe2",help="R2 fastq",required=True)
parser.add_argument("-p","--prefix",help="prefix for output files")
parser.add_argument("-g",'--gtdbtk',help="GTDB-Tk reference data",required=True)
args = parser.parse_args()

args.outdir=os.path.abspath(args.outdir)
if not os.path.exists(args.outdir):
    os.makedirs(args.outdir)

args.fasta=os.path.abspath(args.fasta)
args.pe1=os.path.abspath(args.pe1)
args.pe2=os.path.abspath(args.pe2)

if os.path.dirname(args.pe1) != os.path.dirname(args.pe2):
    print("Read1 and Read2 fastq must be the same directory")
    exit(1)
R1=args.pe1.split("/")[-1]
R2=args.pe2.split("/")[-1]

ref=args.fasta.split("/")[-1]
args.checkm1=os.path.abspath(args.checkm1)
#step1:Binning
refinement=0
if os.path.exists(f'{args.outdir}/{args.prefix}_initial_binning/'):
     subprocess.check_call(f'rm -rf {args.outdir}/{args.prefix}_initial_binning/',shell=True)
cmd=(f"docker run -v {os.path.dirname(args.fasta)}:/ref/ "
     f"-v {os.path.dirname(args.pe1)}:/raw_data/ "
     f"-v {args.outdir}:/outdir -v {args.checkm1}:/srv/whitlam/bio/db/checkm_data/1.0.0 {docker} "
     f"sh -c \'export PATH=/opt/conda/envs/metawrap/bin:$PATH && "
     f"metawrap binning -o /outdir/{args.prefix}_initial_binning/ -t 48 -a /ref/{ref} "
     f"--universal --run-checkm --metabat2 --maxbin2 --concoct /raw_data/{R1} /raw_data/{R2} \'")
print(cmd)
subprocess.check_call(cmd,shell=True)

for i in ['maxbin2','metabat2','concoct']:
     infile=open(f'{args.outdir}/{args.prefix}_initial_binning/{i}_bins.stats',"r")
     for line in infile:
          line=line.strip()
          array=line.split('\t')
          if not re.search(r'completeness',line):
               if float(array[1])>=90 and float(array[2])<=5:
                    refinement=1
                    break
     infile.close()
if refinement==1:
     # step2:Bin refinement
     if os.path.exists(f'{args.outdir}/{args.prefix}_bin_refinement'):
          subprocess.check_call(f'rm -rf {args.outdir}/{args.prefix}_bin_refinement', shell=True)
     cmd=(f"docker run -v {args.outdir}:/outdir -v {os.path.abspath(args.checkm1)}:/ref/ "
          f"-v {args.checkm1}:/srv/whitlam/bio/db/checkm_data/1.0.0 {docker} "
          f"sh -c \'export PATH=/opt/conda/envs/metawrap/bin:$PATH && "
          f"metawrap bin_refinement -o /outdir/{args.prefix}_bin_refinement -t 48 "
          f"-A /outdir/{args.prefix}_initial_binning/metabat2_bins/ "
          f"-B /outdir/{args.prefix}_initial_binning/maxbin2_bins/ "
          f"-C /outdir/{args.prefix}_initial_binning/concoct_bins/ "
          f"-c 90 -x 5\'")
     print(cmd)
     subprocess.check_call(cmd,shell=True)
     # step3:bin-reassembled
     if os.path.exists(f'{args.outdir}/{args.prefix}_bin_reassembly'):
          subprocess.check_call(f'rm -rf {args.outdir}/{args.prefix}_bin_reassembly', shell=True)
     cmd=(f"docker run -v {args.outdir}:/outdir -v {os.path.dirname(args.pe1)}:/raw_data/ "
          f"-v {args.checkm1}:/srv/whitlam/bio/db/checkm_data/1.0.0 {docker} "
          f"sh -c \'export PATH=/opt/conda/envs/metawrap/bin:$PATH && "
          f"metawrap reassemble_bins -o /outdir/{args.prefix}_bin_reassembly "
          f"-1 /raw_data/{R1} -2 /raw_data/{R2} "
          f"-t 48 -m 256 -c 90 -x 5 "
          f"-b /outdir/{args.prefix}_bin_refinement/metawrap_90_5_bins \'")
     print(cmd)
     subprocess.check_call(cmd,shell=True)

     #step4:Dereplication of Bins
     # -comp/--completeness 75
     # -con/--contamination 25
     # -pa/--P_ani 0.9
     # -sa/--S_ani 0.95
     cmd=(f"docker run -v {args.outdir}:/outdir {docker} "
          f"sh -c \'export PATH=/opt/conda/envs/rgi/bin:$PATH && "
          f"dRep dereplicate "
          f"-g /outdir/{args.prefix}_bin_reassembly/reassembled_bins/*fa -p 48 -comp 90 -con 5 "
          f"/outdir/{args.prefix}_dereplicated\'")
     print(cmd)
     if os.path.exists(f"/outdir/{args.prefix}_dereplicated/"):
          subprocess.check_call(f'rm -rf /outdir/{args.prefix}_dereplicated/',shell=True)
     subprocess.check_call(cmd,shell=True)

     #stetp5:Determine the taxonomy of each bin with the Classify_bins module
     args.gtdbtk=os.path.abspath(args.gtdbtk)
     cmd=(f"docker run -v {args.outdir}:/outdir -v {args.gtdbtk}:/ref/ {docker} "
          f"sh -c \'export PATH=/opt/conda/envs/gtdbtk/bin:$PATH "
          f"&& export GTDBTK_DATA_PATH=/ref/ && "
          f"gtdbtk classify_wf --cpus 48 "
          f"--genome_dir /outdir/{args.prefix}_dereplicated/dereplicated_genomes/ "
          f"--skip_ani_screen --out_dir /outdir/{args.prefix}_bin_classfication/ "
          f"-x fa --prefix {args.prefix}\'")
     print(cmd)
     subprocess.check_call(cmd,shell=True)
