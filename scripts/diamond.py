import os,sys,re
import subprocess
import argparse

docker="meta:latest"

def run(R1,R2,prefix,outdir,db,top):
    R1=os.path.abspath(R1)
    a=R1.split("/")[-1]
    db=os.path.abspath(db)
    outdir = os.path.abspath(outdir)
    total_reads=0
    if not os.path.exists(outdir):
        subprocess.check_call('mkdir -p %s' % outdir, shell=True)
    db_name=db.split('/')[-1]
    # evalue=1e-10
    # Treiber M L, Taft D H, Korf I, et al. Pre-and post-sequencing recommendations for functional annotation of human fecal metagenomes[J]. BMC bioinformatics, 2020, 21: 1-15.
    cmd = (f"docker run -v {outdir}:/outdir/ -v {os.path.dirname(db)}:/ref/ -v {os.path.dirname(R1)}:/raw_data/ {docker} sh -c \'"
           f"/opt/conda/bin/diamond blastx --include-lineage --threads 48 --faster --evalue 0.0000000001 --max-target-seqs 5 "
           f"--db /ref/{db_name} --out /outdir/{prefix}.tsv")
    if not R2==None:
        R2=os.path.abspath(R2)
        if os.path.dirname(R2)!=os.path.dirname(R1):
            print("R1 and R2 paths differ")
            exit(1)
        else:
            b=R2.split("/")[-1]
            subprocess.check_call(f"docker run -v {os.path.dirname(R1)}:/raw_data/ {docker} sh -c \'"
                                  f"/opt/conda/bin/pear -f /raw_data/{a} -r /raw_data/{b} -o /raw_data/{prefix} --threads 24\'", shell=True)
            subprocess.check_call(f'cat {outdir}/{prefix}.assembled.fastq {outdir}/{prefix}.unassembled.forward.fastq {outdir}/{prefix}.unassembled.reverse.fastq >{outdir}/{prefix}.merge.fastq && '
                                  f'rm -rf {outdir}/{prefix}.assembled.fastq {outdir}/{prefix}.discarded.fastq {outdir}/{prefix}.unassembled.forward.fastq {outdir}/{prefix}.unassembled.reverse.fastq',shell=True)
        with open(f"{outdir}/{prefix}.merge.fastq", 'r') as f:
            total_reads = sum(1 for i, line in enumerate(f) if i % 4 == 0)
        cmd+=f" -q /outdir/{prefix}.merge.fastq"
    else:
        cmd += f" -q /raw_data/{a}"
        with open(f"{R1}", 'r') as f:
            total_reads = sum(1 for i, line in enumerate(f) if i % 4 == 0)
    cmd+=f" --outfmt 6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore staxids sskingdoms skingdoms sphylums sscinames\'"
    print(cmd)
    subprocess.check_call(cmd, shell=True)
    if os.path.exists(f"{outdir}/{prefix}.merge.fastq"):
        subprocess.check_call(f'rm -rf {outdir}/{prefix}.merge.fastq', shell=True)
    infile=open(f"{outdir}/{prefix}.tsv","r")
    tax,reads,species={},{},{}
    for line in infile:
        line=line.strip()
        array=line.split("\t")
        tmp=array[-4]+";"+array[-1]
        # bitscore  Giolai M, Verweij W, Martin S, et al. Measuring air metagenomic diversity in an agricultural ecosystem[J]. Current Biology, 2024, 34(16): 3778-3791. e4.
        if not re.search("N/A",array[-1]) and not re.search("0",array[-4]) and float(array[2])>=80 and float(array[-6])>=80:
            reads[array[0]]=tmp
        if not array[0] in tax:
            tax[array[0]] = tmp
        else:
            if tax[array[0]] != tmp:
                    tax[array[0]] = "F"
    infile.close()
    for key in reads:
        if tax[key] != "F":
            if reads[key] in species:
                species[reads[key]]+=1
            else:
                species[reads[key]] = 1
    sorted_dict = dict(sorted(species.items(), key=lambda item: item[1], reverse=True))
    virus,other=3,10
    outfile=open(f"{outdir}/{prefix}.stat.tsv","w")
    outfile.write(f"#Species\tRaw_Counts\tPercentage(%)\n")
    for key in sorted_dict:
        counts=float(sorted_dict[key])
        percent = float(sorted_dict[key])*100 / total_reads
        if re.search('Viruses', key) and counts >= 3:
            outfile.write(f"{key}\t{counts}\t{percent}\n")
        elif re.search('Bacteria|Archaea', key) and counts >=10:
            outfile.write(f"{key}\t{counts}\t{percent}\n")
        elif percent>0.1:
            outfile.write(f"{key}\t{counts}\t{percent}\n")
        else:
            top = top - 1
            if top>=0 and counts >= other:
                outfile.write(f"{key}\t{counts}\t{percent}\n")
    outfile.close()
if __name__ == '__main__':
    parser = argparse.ArgumentParser("")
    parser.add_argument("-p1","--pe1",help="R1 fastq file",required=True)
    parser.add_argument("-p2","--pe2",help="R2 fastq file",default=None)
    parser.add_argument("-p","--prefix",help="prefix of output",required=True)
    parser.add_argument("-o","--outdir",help="output directory",required=True)
    parser.add_argument("-d","--db",help="diamond database file,**.dmnd",required=True)
    parser.add_argument("-t","--top",help="Output the top species,defalut 5",default=5,type=int)
    args = parser.parse_args()
    run(args.pe1,args.pe2,args.prefix,args.outdir,args.db,args.top)