#!/usr/bin/env python

# This is a pipeline to call small variants and CNV

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

######################################################
###############  DEFINE ENVIRONMENT ##################
######################################################

# get the cwd were all the scripts are 
CWD = "/".join(__file__.split("/")[0:-1]); sys.path.insert(0, CWD)

# define the EnvDir where the environment is defined
EnvDir = "/".join(sys.executable.split("/")[0:-2])

# import functions
import sv_functions as fun

# packages installed into the conda environment 
samtools = "%s/bin/samtools"%EnvDir
java = "%s/bin/java"%EnvDir
bcftools = "%s/bin/bcftools"%EnvDir
bedtools = "%s/bin/bedtools"%EnvDir

#vcfallelicprimitives = "%s/bin/vcfallelicprimitives"%EnvDir
#sift4g = "%s/bin/sift4g"%EnvDir
# gatk = "%s/bin/gatk"%EnvDir # this is gatk4, and it has to be installed like that
# freebayes = "%s/bin/freebayes"%EnvDir
# vcffilter = "%s/bin/vcffilter"%EnvDir
# picard = "%s/share/picard-2.18.26-0/picard.jar"%EnvDir



# bgzip = "%s/bin/bgzip"%EnvDir
# tabix = "%s/bin/tabix"%EnvDir
# qualimap = "%s/bin/qualimap"%EnvDir


# scripts installed with perSVade
run_vep = "%s/run_vep.py"%CWD


description = """
Run small variant calling and CNV analysis.
"""
              
parser = argparse.ArgumentParser(description=description, formatter_class=RawTextHelpFormatter)

# general args
parser.add_argument("-r", "--ref", dest="ref", required=True, help="Reference genome. Has to end with .fasta. This pipeline will create files under this fasta.")
parser.add_argument("-thr", "--threads", dest="threads", default=2, type=int, help="Number of threads, Default: 16")
parser.add_argument("-o", "--outdir", dest="outdir", action="store", required=True, help="Directory where the data will be stored")
parser.add_argument("--replace", dest="replace", action="store_true", help="Replace existing files")
parser.add_argument("--replace_var_integration", dest="replace_var_integration", action="store_true", help="Replace all the variant integration steps")
parser.add_argument("-p", "--ploidy", dest="ploidy", default=1, type=int, help="Ploidy, can be 1 or 2")
parser.add_argument("--log_file_all_cmds", dest="log_file_all_cmds", default=None, help="An existing log_file_all_cmds to store the cmds")


# alignment args
parser.add_argument("-sbam", "--sortedbam", dest="sortedbam", required=True, type=str, help="The path to the sorted bam file, which should have a bam.bai file in the same dir. This is mutually exclusive with providing reads")

# variant calling args
parser.add_argument("-caller", "--caller", dest="caller", required=False, default="all", help="SNP caller option to obtain vcf file. options: no/all/HaplotypeCaller/bcftools/freebayes.")
parser.add_argument("-c", "--coverage", dest="coverage", default=20, type=int, help="minimum Coverage (int)")
parser.add_argument("-mchr", "--mitochondrial_chromosome", dest="mitochondrial_chromosome", default="mito_C_glabrata_CBS138", type=str, help="The name of the mitochondrial chromosome. This is important if you have mitochondrial proteins for which to annotate the impact of nonsynonymous variants, as the mitochondrial genetic code is different. This should be the same as in the gff. If there is no mitochondria just put 'no_mitochondria'")
parser.add_argument("-mcode", "--mitochondrial_code", dest="mitochondrial_code", default=3, type=int, help="The code of the NCBI mitochondrial genetic code. For yeasts it is 3. You can find the numbers for your species here https://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi")
parser.add_argument("-gcode", "--gDNA_code", dest="gDNA_code", default=1, type=int, help="The code of the NCBI gDNA genetic code. You can find the numbers for your species here https://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi . For C. albicans it is 12. ")
parser.add_argument("--window_freebayes_bp", dest="window_freebayes_bp", default=10000, type=int, help="The window (in bp) in which freebayes regions are split to. If you increase this number the splitting will be in larger chunks of the genome.")

# CNV args
parser.add_argument("--skip_cnv_analysis", dest="skip_cnv_analysis", action="store_true", default=False, help="Skipp the running of the CNV pipeline, which outputs the number of copies that each gene has according to coverage. The gene ID's are based on the GFF3 files that have been provided in -gff")

# other args
parser.add_argument("-gff", "--gff-file", dest="gff", default=None, help="path to the GFF3 annotation of the reference genome. Make sure that the IDs are completely unique for each 'gene' tag. This is necessary for both the CNV analysis (it will look at genes there) and the annotation of the variants.")
parser.add_argument("--repeats_table", dest="repeats_table", default=None, help="path to the table with repeats that is generated by repeat masker. If provided, each variant will have an annotation of whether the ")
parser.add_argument("--pooled_sequencing", dest="pooled_sequencing", action="store_true", default=False, help="It is a pooled sequencing run, which means that the small variant calling is not done based on ploidy. If you are also running SV calling, check that the simulation_ploidies, resemble a population,")
parser.add_argument("--minAF_smallVars", dest="minAF_smallVars", default="infer", help="The minimum fraction of reads covering a variant to be called. The default is 'infer', which will set a threshold based on the ploidy. This is only relevant for the final vcfs, where only PASS vars are considered. It can be a number between 0 and 1.")
parser.add_argument("--generate_alternative_genome", dest="generate_alternative_genome", default=False, action="store_true", help="Generate an alternative genome in smallVariantCalling.")
parser.add_argument("--minPASSalgs_alternativeGenome", dest="minPASSalgs_alternativeGenome", default=2, type=int, help="The number of PASS programs that should be considered for generating an alternative genome if --generate_alternative_genome is provided.")


# removing args
parser.add_argument("--remove_smallVarsCNV_nonEssentialFiles", dest="remove_smallVarsCNV_nonEssentialFiles", action="store_true", default=False, help="Will remove all the varCall files except the integrated final file, the filtered and normalised vcfs, the raw vcf and the CNV files.")

# stopping options
parser.add_argument("--StopAfter_smallVarCallSimpleRunning", dest="StopAfter_smallVarCallSimpleRunning", action="store_true", default=False, help="Stop after obtaining the filtered vcf outputs of each program.")


# get arguments
opt = parser.parse_args()

######################################################
######################################################
######################################################

# add the cmds file
fun.log_file_all_cmds = opt.log_file_all_cmds
if fun.log_file_all_cmds is not None and fun.file_is_empty(fun.log_file_all_cmds): raise ValueError("The provided --log_file_all_cmds %s should exist"%fun.log_file_all_cmds)

# debug commands
if opt.replace is True: fun.delete_folder(opt.outdir)
fun.make_folder(opt.outdir)
if not opt.gff is None and fun.file_is_empty(opt.gff): raise ValueError("%s is not a valid gff"%opt.gff)

# define the minimum AF
ploidy_to_minAF = {1:0.9, 2:0.25, 3:0.15, 4:0.1}
if opt.minAF_smallVars=="infer": minAF_smallVars = ploidy_to_minAF[opt.ploidy]
elif float(opt.minAF_smallVars)<=1 and float(opt.minAF_smallVars)>=0: minAF_smallVars = float(opt.minAF_smallVars)
else: raise ValueError("The value provided in --minAF_smallVars is incorrect")


print("running small vars and CNV pipeline into %s"%opt.outdir)

# check that the environment is correct
fun.run_cmd("echo 'This is a check of the environment in which the pipeline is running'; which bedtools")

# correct the gff file, so that it doesn't have lines starting with # and also add biotype (important for ensembl VEP)
if not opt.gff is None: correct_gff, gff_with_biotype = fun.get_correct_gff_and_gff_with_biotype(opt.gff, replace=opt.replace)
  
# First create some files that are important for any program

# Create a reference dictionary
fun.create_sequence_dict(opt.ref, replace=opt.replace)

# Index the reference
fun.index_genome(opt.ref, replace=opt.replace)

# define the sorted bam
sorted_bam = opt.sortedbam
print("running VarCall for %s"%sorted_bam)


######### DEBUG THE FACT THAT THE VARIANT ANNOTATION IS ALREADY DONE ##########

# define the final file
variantAnnotation_table = "%s/variant_annotation_ploidy%i.tab"%(opt.outdir, opt.ploidy)
if opt.gff is not None and not fun.file_is_empty(variantAnnotation_table) and opt.replace is False: 

    print("WARNING: There is already a variant annotation file, indicating that the pipeline was already ran. Remove %s if you want to run again. Exiting..."%variantAnnotation_table)
    sys.exit(0)

###############################################################################


#####################################
############### CNV #################
#####################################

if opt.skip_cnv_analysis is False and opt.gff is not None:

    print("Starting CNV per gene analysis. This step only runs if -gff is specified.")

    # make a folder for the CNV anlysis
    cnv_outdir = "%s/CNV_results"%opt.outdir
    if not os.path.isdir(cnv_outdir): os.mkdir(cnv_outdir)

    # get the bed file, and also the one of the regions surrounding each gene
    bed_file = "%s.bed_index1"%correct_gff; bed_file_regions = fun.extract_BEDofGENES_of_gff3(correct_gff, bed_file, replace=opt.replace, reference=opt.ref)

    # define the interetsing beds
    gene_to_coverage_file = "%s/gene_to_coverage_genes.tab"%cnv_outdir
    gene_to_coverage_file_regions = "%s/gene_to_coverage_regions.tab"%cnv_outdir

    # go through each region of bed file
    for bed, final_coverge_file in [(bed_file, gene_to_coverage_file), (bed_file_regions, gene_to_coverage_file_regions)]: fun.write_coverage_per_gene_mosdepth_and_parallel(sorted_bam, opt.ref, cnv_outdir, bed, final_coverge_file, replace=opt.replace, threads=opt.threads)

 
    # write the integrated file
    integrated_coverage_file = "%s/genes_and_regions_coverage.tab"%cnv_outdir; integrated_coverage_file_tmp = "%s.tmp"%integrated_coverage_file
    if fun.file_is_empty(integrated_coverage_file) or opt.replace is True: 

       # integrate in one
        df_genes = pd.read_csv(gene_to_coverage_file, sep="\t")
        df_regions = pd.read_csv(gene_to_coverage_file_regions, sep="\t")
        df_integrated = df_genes.merge(df_regions, on="ID", validate="one_to_one", suffixes=("", "_+-10kb_region"))

        # write
        df_integrated.to_csv(integrated_coverage_file_tmp, sep="\t", header=True, index=False)
        os.rename(integrated_coverage_file_tmp, integrated_coverage_file)

    # remove everyhing that is not the coverage file
    for f in os.listdir(cnv_outdir): 
        if f not in {fun.get_file(gene_to_coverage_file), fun.get_file(gene_to_coverage_file_regions), fun.get_file(integrated_coverage_file)}: fun.delete_file_or_folder("%s/%s"%(cnv_outdir, f))
 
    # In Laia's script, she calculates coverage as the median reads per gene (cov per gene) / mean of the cov per gene across all genes

print("per gene CNV analysis finished")


#####################################
######## VARIANTCALLING #############
#####################################

# initialize an array of files that have the VCF results filtered
filtered_vcf_results = []

# debug the fact that you don't want any pooled_sequencing for bcftools
if opt.pooled_sequencing is True: opt.caller = "freebayes"

# Go through the callers, creating in outdir a folder with the results of each
if opt.caller == "no": print("Stop. Doing the variant calling is not necessary.")
    
if "HaplotypeCaller" in opt.caller or opt.caller == "all":

    print("RUNNING GATK: HaplotypeCaller")

    # create a folder that will contain the output of VCF
    outdir_gatk = "%s/HaplotypeCaller_ploidy%i_out"%(opt.outdir, opt.ploidy)

    # run gatk and get the filtered filename
    gatk_out_filtered = fun.run_gatk_HaplotypeCaller(outdir_gatk, opt.ref, sorted_bam, opt.ploidy, opt.threads, opt.coverage, replace=opt.replace)

    # keep
    filtered_vcf_results.append(gatk_out_filtered)
    
    print("HaplotypeCaller is done")

if "bcftools" in opt.caller or opt.caller == "all":

    print("RUNNING bcftools")

    # create a folder that will contain the output of VCF
    outdir_bcftools = "%s/bcftools_ploidy%i_out"%(opt.outdir, opt.ploidy)
    if not os.path.isdir(outdir_bcftools): os.mkdir(outdir_bcftools)

    # only continue if the final file is not done
    filtered_output = "%s/output.filt.vcf"%outdir_bcftools;     
    if fun.file_is_empty(filtered_output) or opt.replace is True:

        # look for the mpileup bcf in sister directories, as it is the same for any other ploidy
        mpileup_output = "%s/output.mpileup.bcf"%outdir_bcftools; mpileup_output_tmp = "%s.tmp"%mpileup_output
        for folder in os.listdir(opt.outdir):
            if folder.startswith("bcftools_ploidy") and folder.endswith("_out"):

                # look for the potential previously calculated mpielup outputs
                potential_previosuly_calculated_mpileup_output = "%s/%s/output.mpileup.bcf"%(opt.outdir, folder)
                if not fun.file_is_empty(potential_previosuly_calculated_mpileup_output): 
                    print("taking %s from previous run"%potential_previosuly_calculated_mpileup_output)
                    mpileup_output = potential_previosuly_calculated_mpileup_output; break

        # if there is no previous run
        if fun.file_is_empty(mpileup_output) or opt.replace is True:

            print("Running mpileup...")
            cmd_bcftools_mpileup = '%s mpileup -a "AD,DP" -O b -f %s -o %s --threads %i %s'%(bcftools, opt.ref, mpileup_output_tmp, opt.threads, sorted_bam); fun.run_cmd(cmd_bcftools_mpileup)
            os.rename(mpileup_output_tmp, mpileup_output)


        # run bcftools call
        call_output = "%s/output.raw.vcf"%outdir_bcftools; call_output_tmp = "%s.tmp"%call_output
        if fun.file_is_empty(call_output) or opt.replace is True:
            print("Running bcftools call ...")

            # define the ploidy specification
            if opt.ploidy==1: ploidy_cmd = "--ploidy %i"%opt.ploidy # This is all haploid
            else:
                # create a ploidy file if ploidy is 2. There's no way to simpli specify ploidy 2
                ploidy_file_bcftools = "%s/ploidy_file.tab"%outdir_bcftools
                open(ploidy_file_bcftools, "w").write("* * * * %i\n"%opt.ploidy) # CHROM, FROM, TO, SEX, PLOIDY

                ploidy_cmd = "--ploidy-file %s"%ploidy_file_bcftools

            cmd_bcftools_call = "%s call -m -f GQ,GP -v -O v --threads %i -o %s %s %s"%(bcftools, opt.threads, call_output_tmp, ploidy_cmd, mpileup_output); fun.run_cmd(cmd_bcftools_call)

            os.rename(call_output_tmp, call_output)
      
        #As there are no recommendations for bcftools, we decided to apply exclusively the filter for coverage. To apply harder filters please edit this command!
        
        # this generates a filtered, vcf, which only has the PASS ones.
        filtered_output_tmp = "%s.tmp"%filtered_output
        if fun.file_is_empty(filtered_output) or opt.replace is True:
            print("Filtering bcftools ... ")
            cmd_filter = "%s filter -m x -e 'INFO/DP <= %i' -O v --threads %i -o %s %s"%(bcftools, opt.coverage, opt.threads, filtered_output_tmp, call_output); fun.run_cmd(cmd_filter)
            os.rename(filtered_output_tmp, filtered_output)

        # keep
    filtered_vcf_results.append(filtered_output)

    print("bcftools is done")

if "freebayes" in opt.caller or opt.caller == "all":

    print("RUNNING freebayes")

    # create a folder that will contain the output of VCF
    outdir_freebayes = "%s/freebayes_ploidy%i_out"%(opt.outdir, opt.ploidy)

    # run freebayes in normal configuratiom, in parallel for each chromosome
    freebayes_filtered = fun.run_freebayes_parallel_regions(outdir_freebayes, opt.ref, sorted_bam, opt.ploidy, opt.coverage, replace=opt.replace, threads=opt.threads, pooled_sequencing=opt.pooled_sequencing, window_fb=opt.window_freebayes_bp) 

    # keep
    filtered_vcf_results.append(freebayes_filtered)
    
    print("freebayes is done")

if opt.StopAfter_smallVarCallSimpleRunning is True:
    print("stopping after generation of each variant calling")
    sys.exit(0)

##########

###################################
##### GET THE INTEGRATED VARS ##### 
################################### 

# redefine opt.replace from --replace_var_integration
opt.replace = opt.replace or opt.replace_var_integration

# get the merged vcf records (these are multiallelic)
print("getting merged vcf without multialleles")
merged_vcf_all = fun.merge_several_vcfsSameSample_into_oneMultiSample_vcf(filtered_vcf_results, opt.ref, opt.outdir, opt.ploidy, replace=opt.replace, threads=opt.threads, repeats_table=opt.repeats_table)

# get the variants in a tabular format
variantInfo_table = "%s/variant_calling_ploidy%i.tab"%(opt.outdir, opt.ploidy)
df_variants = fun.write_variantInfo_table(merged_vcf_all, variantInfo_table, replace=opt.replace)

# define the used programs
if opt.caller=="all": all_programs = sorted(["HaplotypeCaller", "bcftools", "freebayes"])
else: all_programs = sorted(opt.caller.split(","))

# generate a report of the variant calling
variantCallingStats_tablePrefix = "%s/variant_calling_stats_ploidy%i"%(opt.outdir, opt.ploidy)
fun.report_variant_calling_statistics(df_variants, variantCallingStats_tablePrefix, all_programs)

##### KEEP VCFS THAT PASS some programs #########
for minPASS_algs in [1, 2, 3]:

    simplified_vcf_PASSalgs = "%s/variants_atLeast%iPASS_ploidy%i.vcf"%(opt.outdir, minPASS_algs, opt.ploidy)
    simplified_vcf_PASSalgs_multialleleles = "%s/variants_atLeast%iPASS_ploidy%i.withMultiAlt.vcf"%(opt.outdir, minPASS_algs, opt.ploidy)
    simplified_vcf_PASSalgs_tmp = "%s.tmp"%simplified_vcf_PASSalgs

    if fun.file_is_empty(simplified_vcf_PASSalgs) or opt.replace is True:

        print("getting vcf with vars called by >=%i programs"%minPASS_algs)


        # define the interesting variants
        df_PASS = df_variants[(df_variants["NPASS"]>=minPASS_algs) & (df_variants.mean_fractionReadsCov_PASS_algs>=minAF_smallVars) & (df_variants.mean_DP>=opt.coverage)]

        # add the FORMAT
        vcf_fields = ["#CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO", "FORMAT", "SAMPLE"]

        # write empty vcf
        if len(df_PASS)==0: 
            open(simplified_vcf_PASSalgs, "w").write("\t".join(vcf_fields) + "\n")
            continue

        # rename the ID
        df_PASS = df_PASS.rename(columns={"#Uploaded_variation":"ID"})

        # set the FILTER ad the number of pass programs
        df_PASS["FILTER"] = df_PASS.NPASS.apply(str) + "xPASS"

        # set an empty INFO, unless the GT is unknown
        boolean_to_GTtag = {True:"unknown_GT", False:"known_GT"}
        df_PASS["INFO"] = (df_PASS.common_GT==".").apply(lambda x: boolean_to_GTtag[x])

        # set the format
        df_PASS["FORMAT"] = "GT:AF:DP:AD"

        # check that there are no NaNs in mean_fractionReadsCov_PASS_algs and mean_DP
        for field in ["mean_fractionReadsCov_PASS_algs", "mean_DP", "common_GT", "mean_AD"]: 
            if any(pd.isna(df_PASS[field])): 
                df_nan = df_PASS[pd.isna(df_PASS[field])]
                print(df_nan, df_nan.mean_fractionReadsCov_PASS_algs, df_nan.mean_DP, df_nan["ID"])
                raise ValueError("There are NaNs in %s"%field)

        # add the sample according to FORMAT
        df_PASS["SAMPLE"] = df_PASS.common_GT.apply(str) + ":" + df_PASS.mean_fractionReadsCov_PASS_algs.apply(lambda x: "%.4f"%x) + ":" + df_PASS.mean_DP.apply(lambda x: "%.4f"%x) + ":" + df_PASS.mean_AD

        # initialize header lines
        valid_header_starts = ["fileformat", "contig", "reference", "phasing"]
        header_lines = [l for l in fun.get_df_and_header_from_vcf(merged_vcf_all)[1] if any([l.startswith("##%s"%x) for x in valid_header_starts])]

        # add headers
        header_lines += ['##FILTER=<ID=1xPASS,Description="The variant PASSed the filters for 1 algorithm">',
                         '##FILTER=<ID=2xPASS,Description="The variant PASSed the filters for 2 algorithms">',
                         '##FILTER=<ID=3xPASS,Description="The variant PASSed the filters for 3 algorithms">',

                         '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype. If there are discrepacncies in the GT between the algorithms where this var PASSed the filters GT is set to .">',
                         '##FORMAT=<ID=DP,Number=1,Type=Float,Description="Mean read depth of the locus from algorithms where this variant PASSed the filters">',
                         '##FORMAT=<ID=AF,Number=A,Type=Float,Description="Mean fraction of reads covering the ALT allele from algorithms where this variant PASSed the filters">',
                         '##FORMAT=<ID=AD,Number=R,Type=Integer,Description="The number of reads of each allele, as a mean of algorithms where this variant PASSed the filters">',

                         "##phasing=none",
                         '##source=%s'%("_".join(all_programs))]


        # write the split with split multialleles
        open(simplified_vcf_PASSalgs_tmp, "w").write("\n".join(header_lines) + "\n" + df_PASS[vcf_fields].to_csv(sep="\t", index=False, header=True))
        
        # write the split with joined multialleles
        if opt.ploidy==2 and opt.pooled_sequencing is False: fun.get_vcf_with_joined_multialleles_diploid(simplified_vcf_PASSalgs_tmp, simplified_vcf_PASSalgs_multialleleles, opt.ref, replace=opt.replace, threads=opt.threads)

        # rename the simplified
        os.rename(simplified_vcf_PASSalgs_tmp, simplified_vcf_PASSalgs)


    # generate alternative genome if specified
    if opt.generate_alternative_genome is True and opt.minPASSalgs_alternativeGenome==minPASS_algs:
        print("generating the alternative genome with vars that pass at leasy %i programs"%minPASS_algs)

        alternative_genome = "%s/variants_atLeast%iPASS_ploidy%i_alternative_genome.fasta"%(opt.outdir, minPASS_algs, opt.ploidy)
        fun.get_alternative_genome(opt.ref, simplified_vcf_PASSalgs, alternative_genome, replace=opt.replace, threads=opt.threads)



#################################################

# stop if there is no GFF provided
if opt.gff is None: 
    print("WARNING: No gff provided. Skipping the annotation of the variants")

else:

    ######### RUN VEP AND GENERATE ANNOTATION TABLE #########
    if fun.file_is_empty(variantAnnotation_table) or opt.replace is True:

        # run vep in parallel
        annotated_vcf = fun.run_vep_parallel(merged_vcf_all, opt.ref, gff_with_biotype, opt.mitochondrial_chromosome, opt.mitochondrial_code, opt.gDNA_code, threads=opt.threads, replace=opt.replace)

        # get into df
        df_vep = pd.read_csv(annotated_vcf, sep="\t")


        # get variant annotation table
        print("generating variant annotation table")

        # add fields 
        df_vep["ref"] = df_vep["#Uploaded_variation"].apply(lambda x: x.split("_")[-1].split("/")[-2])
        df_vep["alt"] = df_vep["#Uploaded_variation"].apply(lambda x: x.split("_")[-1].split("/")[-1])

        df_vep['is_snp'] = (df_vep["ref"].apply(len)==1) & (df_vep["ref"]!="-") & (df_vep["alt"].apply(len)==1) & (df_vep["alt"]!="-")

        def get_nan_to_str(cons):
            if pd.isna(cons): return "-"
            else: return cons
        df_vep["Consequence"] = df_vep.Consequence.apply(get_nan_to_str)

        df_vep["consequences_set"] = df_vep.Consequence.apply(lambda x: set(str(x).split(",")))

        df_vep["is_protein_altering"] = df_vep.Consequence.apply(fun.get_is_protein_altering_consequence)

        # generate a table that has all the variant annotation info
        varSpec_fields = ['#Uploaded_variation', 'Gene', 'Feature', 'Feature_type', 'Consequence', 'cDNA_position', 'CDS_position', 'Protein_position', 'Amino_acids', 'Codons', 'is_snp', 'is_protein_altering']

        # add whether it matches a repeat
        if opt.repeats_table is not None:

            variants_in_repeats = set(df_variants[df_variants.INREPEATS]["#Uploaded_variation"])
            df_vep["overlaps_repeats"] = df_vep["#Uploaded_variation"].isin(variants_in_repeats)

            print("There are %i/%i lines in the vep output that are in repeats"%(sum(df_vep.overlaps_repeats), len(df_vep)))

            varSpec_fields.append("overlaps_repeats")

        # write the final vars
        variantAnnotation_table_tmp = "%s.tmp"%variantAnnotation_table
        df_vep[varSpec_fields].drop_duplicates().to_csv(variantAnnotation_table_tmp, sep="\t", header=True, index=False)
        os.rename(variantAnnotation_table_tmp, variantAnnotation_table)

    #############################################


print("VarCall Finished")

# at the end remove all the non-essential files
if opt.remove_smallVarsCNV_nonEssentialFiles is True: fun.remove_smallVarsCNV_nonEssentialFiles(opt.outdir, opt.ploidy)

