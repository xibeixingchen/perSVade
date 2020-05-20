#!/usr/bin/env python

# This is the perSVade pipeline main script, which shoul dbe run on the perSVade conda environment


##### DEFINE ENVIRONMENT #######

# module imports
import argparse, os
import pandas as pd
import numpy as np
from argparse import RawTextHelpFormatter
import copy as cp
import pickle
import string
import shutil 
from Bio import SeqIO
import random
import sys
from shutil import copyfile

# get the cwd were all the scripts are 
CWD = "/".join(__file__.split("/")[0:-1]); sys.path.insert(0, CWD)

# define the EnvDir where the environment is defined
EnvDir = "/".join(sys.executable.split("/")[0:-2])

# import functions
import sv_functions as fun

# packages installed into the conda environment 
picard = "%s/share/picard-2.18.26-0/picard.jar"%EnvDir
samtools = "%s/bin/samtools"%EnvDir
java = "%s/bin/java"%EnvDir

#######

description = """
Runs perSVade pipeline on an input set of paired end short ends. It is expected to be run on a coda environment and have several dependencies (see https://github.com/Gabaldonlab/perSVade). Some of these dependencies are included in the respository "installation/external_software". These are gridss (tested on version 2.8.1), clove (tested on version 0.17) and NINJA (we installed it from https://github.com/TravisWheelerLab/NINJA/releases/tag/0.95-cluster_only). If you have any trouble with these you can replace them from the source code.
"""
              
parser = argparse.ArgumentParser(description=description, formatter_class=RawTextHelpFormatter)

# general args
parser.add_argument("-r", "--ref", dest="ref", required=True, help="Reference genome. Has to end with .fasta")
parser.add_argument("-thr", "--threads", dest="threads", default=16, type=int, help="Number of threads, Default: 16")
parser.add_argument("-o", "--outdir", dest="outdir", action="store", required=True, help="Directory where the data will be stored")
parser.add_argument("--replace", dest="replace", action="store_true", help="Replace existing files")
parser.add_argument("-p", "--ploidy", dest="ploidy", default=1, type=int, help="Ploidy, can be 1 or 2")

# different modules to be executed
parser.add_argument("--testSVgen_from_assembly", dest="testSVgen_from_assembly", default=True, action="store_true", help="This indicates whether to generate a report of how the generation of SV from an assembly works for C. glabrata.")

parser.add_argument("--genomes_withSV_and_shortReads_table", dest="genomes_withSV_and_shortReads_table", type=str, default=None, help="This is the path to atable that has three fields: ID,assembly,short_reads1,short_reads2. These should be genomes that are close to the reference genome and some expected SV. Whenever this argument is provided, the pipeline will find SVs in these assemblies and generate a folder <outdir>/real_genomes_SVs/SVs_compatible_to_insert that will contain one file for each SV, so that they are compatible and ready to insert in a simulated genome. If this table has also short_reads* the pipeline can test which is the recall of these short reads for finding the 'real SVs' with the testRealDataAccuracy option.")

parser.add_argument("--SVs_compatible_to_insert_dir", dest="SVs_compatible_to_insert_dir", type=str, default=None, help="A directory with one file for each SV that can be inserted into the reference genome in simulations. It may be created with --genomes_withSV_and_shortReads_table. If both --SVs_compatible_to_insert_dir and --genomes_withSV_and_shortReads_table are provided, --SVs_compatible_to_insert_dir will be used, and --genomes_withSV_and_shortReads_table will have no effect. If none of them are provided, this pipeline will base the parameter optimization on randomly inserted SVs (the random behavior). The coordinates have to be 1-based, as they are ready to insert into RSVsim.")

parser.add_argument("--fast_SVcalling", dest="fast_SVcalling", action="store_true", default=False, help="Run SV calling with a default set of parameters. There will not be any optimisation nor reporting of accuracy. This is expected to work almost as fast as gridss and clove together.")

parser.add_argument("--testRealDataAccuracy", dest="testRealDataAccuracy", action="store_true", default=False, help="Reports the accuracy (recall) of your calling on the real data. This is defined with --genomes_withSV_and_shortReads_table.")

parser.add_argument("--species_tree_closeGenomes", dest="species_tree_closeGenomes", type=str, default=None, help="The path to a newick file that contains the species tree (the leaf names should match the 'ID' field) of the genomes provided in  --genomes_withSV_and_shortReads_table. This is important because the sorting of 'high-confidence vars' out of genomes_withSV_and_shortReads_table requires the tree of the genomes. By default, this is calculated with JolyTree, which is fast but not the most accurate method.")

# alignment args
parser.add_argument("-f1", "--fastq1", dest="fastq1", default=None, help="fastq_1 file. Option required to obtain bam files")
parser.add_argument("-f2", "--fastq2", dest="fastq2", default=None, help="fastq_2 file. Option required to obtain bam files")
parser.add_argument("-sbam", "--sortedbam", dest="sortedbam", default=None, help="The path to the sorted bam file, which should have a bam.bai file in the same dir. This is mutually exclusive with providing reads")
parser.add_argument("--run_qualimap", dest="run_qualimap", action="store_true", help="Run qualimap for quality assessment of bam files. This may be inefficient sometimes because of the ")

# other args
parser.add_argument("-mchr", "--mitochondrial_chromosome", dest="mitochondrial_chromosome", default="mito_C_glabrata_CBS138", type=str, help="The name of the mitochondrial chromosome. This is important if you have mitochondrial proteins for which to annotate the impact of nonsynonymous variants, as the mitochondrial genetic code is different. This should be the same as in the gff. If there is no mitochondria just put 'no_mitochondria'. If there is more than one mitochindrial scaffold, provide them as comma-sepparated IDs.")

opt = parser.parse_args()


# if replace is set remove the outdir, and then make it
if opt.replace is True: fun.delete_folder(opt.outdir)
fun.make_folder(opt.outdir)

# define the name that will be used as tag, it is the name of the outdir, without the full path
name_sample = opt.outdir.split("/")[-1]; print("working on %s"%name_sample)

# move the reference genome into the outdir, so that every file is written under outdir
reference_genome_dir = "%s/reference_genome_dir"%(opt.outdir); fun.make_folder(reference_genome_dir)
new_reference_genome_file = "%s/reference_genome.fasta"%reference_genome_dir
fun.run_cmd("cp %s %s"%(opt.ref, new_reference_genome_file))
opt.ref = new_reference_genome_file

# define files that may be used in many steps of the pipeline
if opt.sortedbam is None:

    bamfile = "%s/aligned_reads.bam"%opt.outdir
    sorted_bam = "%s.sorted"%bamfile
    index_bam = "%s.bai"%sorted_bam

else:

    # debug the fact that you prvided reads and bam. You should just provide one
    if any([not x is None for x in {opt.fastq1, opt.fastq2}]): raise ValueError("You have provided reads and a bam, you should only provide one")

    # get the files
    sorted_bam = opt.sortedbam
    index_bam = "%s.bai"%sorted_bam

#####################################
############# BAM FILE ##############
#####################################

##### YOU NEED TO RUN THE BAM FILE #####

if all([not x is None for x in {opt.fastq1, opt.fastq2}]):

    print("WORKING ON ALIGNMENT")
    fun.run_bwa_mem(opt.fastq1, opt.fastq2, opt.ref, opt.outdir, bamfile, sorted_bam, index_bam, name_sample, threads=opt.threads, replace=opt.replace)


else: print("Warning: No fastq file given, assuming that you provided a bam file")

#####################################
#####################################
#####################################


###########################################
############# NECESSARY FILES #############
###########################################

# check that all the important files exist
if any([fun.file_is_empty(x) for x in {sorted_bam, index_bam}]): raise ValueError("You need the sorted and indexed bam files in ")

#### bamqc
if opt.run_qualimap is True:
    
    bamqc_outdir = "%s/bamqc_out"%opt.outdir
    if fun.file_is_empty("%s/qualimapReport.html"%bamqc_outdir) or opt.replace is True:
        print("Running bamqc to analyze the bam alignment")
        qualimap_std = "%s/std.txt"%bamqc_outdir
        try: bamqc_cmd = "%s bamqc -bam %s -outdir %s -nt %i > %s 2>&1"%(qualimap, sorted_bam, bamqc_outdir, opt.threads, qualimap_std); fun.run_cmd(bamqc_cmd)
        except: print("WARNING: qualimap failed likely due to memory errors, check %s"%qualimap_std)

# First create some files that are important for any program

# Create a reference dictionary
rstrip = opt.ref.split(".")[-1]
dictionary = "%sdict"%(opt.ref.rstrip(rstrip)); tmp_dictionary = "%s.tmp"%dictionary; 
if fun.file_is_empty(dictionary) or opt.replace is True:

    # remove any previously created tmp_file
    if not fun.file_is_empty(tmp_dictionary): os.unlink(tmp_dictionary)

    print("Creating picard dictionary")
    cmd_dict = "%s -jar %s CreateSequenceDictionary R=%s O=%s TRUNCATE_NAMES_AT_WHITESPACE=true"%(java, picard, opt.ref, tmp_dictionary); fun.run_cmd(cmd_dict)   
    os.rename(tmp_dictionary , dictionary)

# Index the reference
if fun.file_is_empty("%s.fai"%opt.ref) or opt.replace is True:
    print ("Indexing the reference...")
    cmd_indexRef = "%s faidx %s"%(samtools, opt.ref); fun.run_cmd(cmd_indexRef) # This creates a .bai file of the reference

###########################################
###########################################
###########################################


#####################################
##### STRUCTURAL VARIATION ##########
#####################################

#### test how well the finding of SVs in an assembly works ####
if opt.testSVgen_from_assembly:

    outdir_test_FindSVinAssembly = "%s/test_FindSVinAssembly"%opt.outdir
    if __name__ == '__main__': fun.test_SVgeneration_from_assembly(opt.ref, outdir_test_FindSVinAssembly, threads=opt.threads, replace=opt.replace, n_simulated_genomes=2, mitochondrial_chromosome=opt.mitochondrial_chromosome)

###############################################################

##### find a dict that maps each svtype to a file with a set of real SVs (real_svtype_to_file) #####
all_svs = {'translocations', 'insertions', 'deletions', 'inversions', 'tandemDuplications'}

if opt.SVs_compatible_to_insert_dir is not None and opt.fast_SVcalling is False: 
    print("using the set of real variants from %s"%opt.SVs_compatible_to_insert_dir)

    # if it is already predefined
    real_svtype_to_file = {svtype : "%s/%s"%(opt.SVs_compatible_to_insert_dir) for svtype in all_svs}

elif opt.genomes_withSV_and_shortReads_table is not None and opt.fast_SVcalling is False:
    print("finding the set of compatible SVs from %s"%opt.genomes_withSV_and_shortReads_table)

    # if you provided a list of genomes with SV close to the ref genome
    outdir_finding_realVars = "%s/findingRealSVs"%opt.outdir
    real_svtype_to_file = fun.get_compatible_real_svtype_to_file(opt.genomes_withSV_and_shortReads_table, opt.ref, outdir_finding_realVars, species_treefile=opt.species_tree_closeGenomes, replace=opt.replace, threads=opt.threads)

    kjbdahjkadhkgadhghjgad


else: 
    print("Avoiding the simulation of real variants. Only inserting randomSV.")

    # define the set of vars as empty. This will trigger the random generation of vars
    real_svtype_to_file = {}

###################################################################################################

##### test the accuracy of the running on each of the 'real' genomes: #####
if opt.testRealDataAccuracy is True: 

    if opt.genomes_withSV_and_shortReads_table is None: raise ValueError("You have to provide --genomes_withSV_and_shortReads_table with short reads if you want to validate real data.")


###########################################################################

### run the actual perSVade function optimising parameters ###



###############################################################



sdflndljbdjkjbadkjbadmnbasdnbmasdnbasdnmb

# create the main output directory
SVdetection_outdir = "%s/SVdetection_output"%opt.outdir

# run pipeline, this has to be done with this if to run the pipeline
if __name__ == '__main__': fun.run_GridssClove_optimising_parameters(sorted_bam, opt.ref, SVdetection_outdir, replace_covModelObtention=opt.replace, threads=opt.threads, replace=opt.replace, mitochondrial_chromosome=opt.mitochondrial_chromosome, simulation_types=["uniform"], n_simulated_genomes=2, target_ploidies=["haploid", "diploid_hetero"], range_filtering_benchmark="theoretically_meaningful", expected_ploidy=opt.ploidy)


print("structural variation analysis with perSVade finished")

#####################################
#####################################
#####################################


print("perSVade Finished")


