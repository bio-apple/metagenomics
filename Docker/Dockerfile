FROM alpine:latest
RUN apk add --no-cache bash && mkdir -p /lib64/ /ref/ /script/ /raw_data/ /outdir/ && \
    wget -q -O /etc/apk/keys/sgerrand.rsa.pub https://alpine-pkgs.sgerrand.com/sgerrand.rsa.pub && \
    wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.35-r1/glibc-2.35-r1.apk &&  \
    apk add --no-cache --force-overwrite glibc-2.35-r1.apk && rm glibc-2.35-r1.apk && ln -s /usr/glibc-compat/lib/* /lib64/ && \
    wget -q -O /opt/Miniforge3-Linux-x86_64.sh https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh && \
    bash /opt/Miniforge3-Linux-x86_64.sh -f -b -p /opt/conda/ && rm -rf /opt/Miniforge3-Linux-x86_64.sh /var/cache/apk/* && \
    /opt/conda/bin/conda install bioconda::diamond bioconda::pear && \
    /opt/conda/bin/mamba create --name rgi --channel conda-forge --channel bioconda --channel defaults rgi &&  \
    /opt/conda/bin/conda config --add channels ursky && \
    /opt/conda/bin/mamba create -y --name metawrap --channel ursky --channel conda-forge --channel bioconda --channel defaults blas=2.5=mkl biopython metawrap-mg=1.3.2 checkm-genome drep && \
    /opt/conda/bin/mamba create --name gtdbtk --channel conda-forge --channel bioconda --channel defaults gtdbtk && \
    /opt/conda/bin/mamba create --name metaphlan --channel conda-forge --channel bioconda --channel defaults metaphlan && \
    /opt/conda/bin/mamba create --name kraken2 --channel conda-forge --channel bioconda --channel defaults kraken2 krakentools krona bracken taxonkit bioawk && \
    /opt/conda/bin/conda install -n rgi --channel conda-forge --channel bioconda --channel defaults staramr cd-hit freebayes fastqtk seqtk bbmap fastp fastqc prinseq cutadapt multiqc trimmomatic  \
    bcftools covtobed fastani megan coverm &&  \
    /opt/conda/bin/conda clean -a -y && /opt/conda/bin/mamba clean -a -y
ENV LD_LIBRARY_PATH=/lib/:/lib64/:$LD_LIBRARY_PATH