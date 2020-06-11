# this has a lot of code that is not used


### a way to get tandem duplications in non random simulations

#### ADD THE TANDEM DUPLICATIONS #### 
"""

# deifine the currently generated svtypes
random_svtypes_generated = {"insertions", "deletions", "translocations", "inversions"}

# get the randomly simulated svs into a dict, together with the randomly generated ones.
random_svtype_to_svfile = {svtype : "%s/%s.tab"%(random_sim_dir, svtype) for svtype in random_svtypes_generated}

# get the remaining bed regions
bed_regions_prefix = "%s/bed_regions_rmaining_afterInsInvDelTra"%genome_outdir
all_regions_bed_df =  pd.read_csv(regions_without_SV_bed, sep="\t", header=None, names=["chromosome", "start", "end"]) # these are the remining after removing the already present ones
regions_without_SV_bed, svtype_to_nSVs = get_bed_df_not_overlapping_with_SVs(all_regions_bed_df, random_svtypes_generated, random_svtype_to_svfile, bed_regions_prefix)

# get the tandem duplications for the 
tandemDuplications_file = "%s/tandemDuplications.tab"%random_sim_dir
sizes = list(pd.read_csv("%s/deletions.tab"%random_sim_dir, sep="\t")["Size"])
get_tandemDuplications_file_in_target_regions(regions_without_SV_bed, sizes, tandemDuplications_file)
"""

####################################


def get_tandemDuplications_file_in_target_regions(target_regions_bed, sizes, tanDup_file, max_n_copies=5):

    """This function writes a file that contains tandem duplications (format like RSVsim) of 'sizes' into tanDupl_file. max_n_copies would be the maxium number of tanDups inserted.

    We will try all the sizes down to 50, and if it is not possible to find them we'll drop them """

    # load the regions bed and sort by size
    regions_df = pd.read_csv(target_regions_bed, sep="\t", header=None, names=["chromosome", "start", "end"])
    regions_df["size"] = regions_df.end - regions_df.start
    regions_df = regions_df.sort_values(by="size", ascending=False)

    # define the total number of tanDels
    maximum_tan = len(sizes); n_tan_simulated = 0

    # initialize a dict
    tanDict = {}

    # define the order of the sizes to try
    if min(sizes)<=50: tried_sizes = list(reversed(sorted(sizes)))
    else: tried_sizes = list(reversed(sorted(sizes))) + list(range(min(sizes), 50))

    for size in tried_sizes:

        # break if you have already simulated all the desired tandels
        if n_tan_simulated>=maximum_tan: break

        # find if there is a region in regions_df where it fits
        df = regions_df[regions_df["size"]>=size]

        # try another size if not found
        if len(df)==0: continue

        # get the largest window (upmost) to insert the tandem duplication and calculate the randomly inserted tanDup
        target_window = df.iloc[0]
        start_tanDup = random.randrange(target_window.start, (target_window.end-size-1))
        end_tanDup = start_tanDup + size

        # keep them
        n_tan_simulated += 1
        tanDict[n_tan_simulated] = {"Chr": target_window.chromosome, "Start":start_tanDup, "End":end_tanDup, "Name":"tandemDuplication%i_%s"%(n_tan_simulated, target_window.chromosome), "Duplications":random.randrange(2, max_n_copies), "Size":(end_tanDup-start_tanDup)}

        # get a df with the left and right parts that would be kept after the tanDup is inserted
        maxI = max(regions_df.index) # get the maxium current idx of the SVs
        df_surrounding_regions = pd.DataFrame(
            {maxI+1: {"chromosome":target_window.chromosome, "start":target_window.start, "end":start_tanDup-1000}, # 
            maxI+2: {"chromosome":target_window.chromosome, "start":end_tanDup+1000, "end":target_window.end}}
            ).transpose()

        df_surrounding_regions["size"] = df_surrounding_regions.end - df_surrounding_regions.start

        # add this df and remove the previous one
        regions_df = regions_df.drop(target_window.name, axis=0) # remove the window were the dup was inserted
        regions_df = regions_df.append(df_surrounding_regions, sort=True).sort_values(by="size", ascending=False) # add the newly broken regions 

    # get the tan dict as numbers
    tan_cols = ["Name", "Chr", "Start", "End", "Size", "Duplications"]
    if len(tanDict)==0: tan_df = pd.DataFrame(columns=tan_cols)
    else: tan_df = pd.DataFrame(tanDict).transpose()

    # write
    tan_df[tan_cols].to_csv(tanDup_file, sep="\t", header=True, index=False)


############# distance to the telomere #################


def get_distance_to_telomere_through_breakpoints(genome, df_bedpe, df_gridss_filt, genomeGraph_outfileprefix):

    """This function returns a df where each genomic position is mappend to the real distance to the telomere through all the breakpoints"""

    adlkadjhdlajthisdoesnotwork


    # get the graoh as a genome
    genome_graph, chrom_to_offset, chrom_to_lenSeq, all_positions, chromosome_end_nodes, chromosome_start_nodes = get_genomeGraph_object(genome, df_bedpe, df_gridss_filt)

    # initialize a df where each col is a telomeric position and the rows are the the positions of the genome graph
    telomericNode_to_pos_to_dist = {}

    # get the shortest paths mapping each node to the 
    for I, telomeric_node in enumerate(chromosome_end_nodes.union(chromosome_start_nodes)):
        print("working on telomeric_node %i"%telomeric_node)

        # get the connected positions list
        connected_positions = genome_graph.subcomponent(telomeric_node)
        print("There are %i connected positions"%len(connected_positions))

        # get the shortest paths to all the others
        all_shorest_paths_len = map(len, genome_graph.get_all_shortest_paths(v=telomeric_node, to=connected_positions, mode="OUT"))
        pos_to_shortestPathLen = dict(zip(connected_positions, all_shorest_paths_len))

        telomericNode_to_pos_to_dist[telomeric_node] = pos_to_shortestPathLen

        if I==2: break

    df_telomeric_dist = pd.DataFrame(telomericNode_to_pos_to_dist)

    print(df_telomeric_dist)


    ldjhdljjhlsfd

    return df_telomeric_dist


##### GRAPH GENOME OPERATIONS #####
if type_coverage_to_filterTANDEL=="coverage_rel_to_predFromFeats":

    # only take into account if you want to correct by coverage_rel_to_predFromFeats

    # get a graph of the genome
    genomeGraph_outfileprefix = "%s.genomeGraph_incluingBPs%s"%(raw_bedpe_file, include_breakpoints_in_genomeGraph)
    if include_breakpoints_in_genomeGraph is True:
        df_bedpe_arg = df_bedpe
        df_gridss_filt_arg = df_gridss_filt
    
    else: df_bedpe_arg = df_gridss_filt_arg = None

    genome_graph, df_positions_graph = get_genomeGraph_object(reference_genome, df_bedpe_arg, df_gridss_filt_arg, genomeGraph_outfileprefix, replace=replace_FromGridssRun)

    # get a function that takes the GC content, chromosome and distance to the telomere and returns coverage. This is actually a lambda function
    outdir_coverage_calculation = "%s/coverage_per_regions2kb_incluingBPs%s"%(working_dir, include_breakpoints_in_genomeGraph); make_folder(outdir_coverage_calculation)
    df_coverage_train = pd.read_csv(generate_coverage_per_window_file_parallel(reference_genome, outdir_coverage_calculation, sorted_bam, windows_file="none", replace=replace_FromGridssRun, window_l=2000), sep="\t")

    distToTel_chrom_GC_to_coverage_fn = get_distanceToTelomere_chromosome_GCcontent_to_coverage_fn(df_coverage_train, reference_genome, genome_graph, df_positions_graph, outdir_coverage_calculation, mitochondrial_chromosome=mitochondrial_chromosome, replace=replace_FromGridssRun)


elif type_coverage_to_filterTANDEL=="mediancov_1": distToTel_chrom_GC_to_coverage_fn = genome_graph = df_positions_graph = None


####### monophyly of vars

    # add to the tree if it is there
            for l in species_tree.get_leaves():

                if svID in ID_to_svIDs[l.name]: l.svID = svID
                else: l.svID = "none"

            # ask if it is monophyletic
            svID_is_monophyletic, type_phyly, nodes_monophyletic = species_tree.check_monophyly(values=[svID], target_attr="svID")

            # length monophyletic nodes
            max_len_monophyletic_nodes = {len(mn) for mn in nodes_monophyletic}



            print(max_len_monophyletic_nodes)


    adlkdalkad


def get_clove_output_with_coverage_forTANDEL(outfile_clove, reference_genome, sorted_bam, distToTel_chrom_GC_to_coverage_fn, genome_graph, df_positions_graph, replace=False, run_in_parallel=False, delete_bams=False):

    """Takes the output of clove and adds the coverage of the TAN and DEL, or -1.

    If you set genome_graph to None it will skip adding the coverage relative to sequence features"""

    # first load clove into a df
    df_clove = get_clove_output(outfile_clove)

    if len(df_clove)>0:

        # now write a bed with the TANDEL regions
        bed_TANDEL_regions = "%s.TANDEL.bed"%outfile_clove
        df_TANDEL = df_clove[df_clove.SVTYPE.isin({"TAN", "DEL"})][["#CHROM", "POS", "END"]].rename(columns={"#CHROM":"chromosome", "POS":"start", "END":"end"})
        
        if len(df_TANDEL)>0:

            df_TANDEL.to_csv(bed_TANDEL_regions, sep="\t", header=True, index=False)

            # get a file that has the coverage of these windows
            coverage_df = get_coverage_per_window_df_without_repeating(reference_genome, sorted_bam, bed_TANDEL_regions, replace=replace, run_in_parallel=run_in_parallel, delete_bams=delete_bams)

            # get the coverage relative to prediction from features
            if genome_graph is not None:

                outdir_rel_cov_calculation = "%s_calculatig_rel_coverage"%outfile_clove
                coverage_df["coverage_rel_to_predFromFeats"] = get_coverage_list_relative_to_predictedFromTelomereAndGCcontent(coverage_df, reference_genome, distToTel_chrom_GC_to_coverage_fn, genome_graph, df_positions_graph, outdir_rel_cov_calculation, real_coverage_field="mediancov_1", replace=replace)

            else: coverage_df["coverage_rel_to_predFromFeats"] = -1

        else: coverage_df = pd.DataFrame(columns=["chromosome", "end", "length", "mediancov_1", "nocoveragebp_1", "percentcovered_1", "start"])

        # merge
        merged_df = df_clove.merge(coverage_df, how="left", left_on=["#CHROM", "POS", "END"], right_on=["chromosome", "start", "end"], validate="many_to_one")

        # change types of fields
        merged_df["POS"] = merged_df.POS.apply(get_int)
        merged_df["END"] = merged_df.END.apply(get_int)
        merged_df["START"] = merged_df.START.apply(get_int)

        return merged_df 

    else: return pd.DataFrame()





########### CALCULATE GC CONTENT BASED ON PREVIOUSLY MEASURED REGIONS  ###########

def get_df_with_GCcontent(df_windows, genome, gcontent_outfile, replace=False):

    """This function takes a df with windows of the genome and adds the gc content for each window, writing a file under gcontent_outfile. It will only do those that have been already measured"""

    print("Getting GC content")

    if file_is_empty(gcontent_outfile) or replace is True:

        # define the initial index
        initial_index = list(df_windows.index)

        # define a file that has all the GC content per windows of the genome
        all_gcontent_outfile = "%s.GCcontent_all_windows.py"%genome

        # load the previously generated windows
        GCcontent_cols = ["chromosome", "start", "end", "GCcontent"]
        if file_is_empty(all_gcontent_outfile) or replace is True: 
        #if True:
            remove_file(all_gcontent_outfile)
            previous_df_windows = pd.DataFrame(columns=GCcontent_cols)

        else: previous_df_windows = load_object(all_gcontent_outfile)

        # set as index the combination of each chrom, start and end
        previous_df_windows = previous_df_windows.set_index(["chromosome", "start", "end"], drop=False)
        all_previous_windows = set(previous_df_windows.index)

        # resort
        df_windows = df_windows.sort_values(by=["chromosome", "start", "end"]).set_index(["chromosome", "start", "end"], drop=False)

        # get the new windows
        new_windows = list(set(df_windows.index).difference(all_previous_windows))
        df_windows_new = df_windows.loc[new_windows]

        if len(df_windows_new)>0:
            print("adding %i new windows"%len(df_windows_new))

            # get the GC content file for each position
            gc_content_outfile_perPosition = generate_nt_content_file(genome, replace=replace, target_nts="GC")
            gc_df = pd.read_csv(gc_content_outfile_perPosition, sep="\t")[["chromosome", "position", "is_in_GC"]].sort_values(by=["chromosome", "position"])

            # define a df where each position is one row and it has the start_window as an add
            df_windows["length"] = df_windows.end - df_windows.start
            positions = make_flat_listOflists(list(df_windows.apply(lambda r: list(range(r["start"], r["end"])), axis=1)))
            start_windows = make_flat_listOflists(list(df_windows.apply(lambda r: [r["start"]]*r["length"], axis=1)))
            end_windows = make_flat_listOflists(list(df_windows.apply(lambda r: [r["end"]]*r["length"], axis=1)))
            chromosomes = make_flat_listOflists(list(df_windows.apply(lambda r: [r["chromosome"]]*r["length"], axis=1)))
            df_positions = pd.DataFrame({"position":positions, "chromosome":chromosomes, "start_window":start_windows, "end_window":end_windows})

            # add the positions to the gc df
            gc_df = gc_df.merge(df_positions, on=["chromosome", "position"], how="right")        

            # calculate the GC content and add to df
            startWindow_to_gc = gc_df[["chromosome", "start_window", "end_window", "is_in_GC"]].groupby(["chromosome", "start_window", "end_window"]).mean()["is_in_GC"]

        else: startWindow_to_gc = pd.Series()

        # add the previously generated windows
        startWindow_to_gc = startWindow_to_gc.append(previous_df_windows["GCcontent"])

        # get into df_windows
        print(df_windows, startWindow_to_gc)
        df_windows["GCcontent"] = list(startWindow_to_gc.loc[df_windows.index])

        # save the ultimate windows file
        all_df_windows = previous_df_windows.append(df_windows[GCcontent_cols])
        all_gcontent_outfile_tmp = "%s.%s"%(all_gcontent_outfile, id_generator(15))
        save_object(all_df_windows, all_gcontent_outfile_tmp)
        os.rename(all_gcontent_outfile_tmp, all_gcontent_outfile)

        # at the end save the df windows
        df_windows.index = initial_index
        save_object(df_windows, gcontent_outfile)

    else: df_windows = load_object(gcontent_outfile)

    return df_windows




###### get compatible translocations ####


def get_compatible_translocations_df(df, chr_to_len):

    """Takes a df with translocations and returns those that are compatible with each other, so that two arms of a chromosome not have a translocation"""


    # change the ID
    df = df.set_index("ID", drop=False)

    # define the vars that are real or simulated
    real_df = df[df.ID.apply(lambda x: x.endswith("_realSV"))]
    sim_df = df[~df.ID.apply(lambda x: x.endswith("_realSV"))]

    # define all the chromosomes
    all_chromosomes = set(df["ChrA"]).union(set(df["ChrB"]))

    # initalize a bed with the interesting bed regions
    df_bed_allRegions, nSVs = get_affected_region_bed_for_SVdf(real_df, "translocations", all_chromosomes) 

    # initialize the interesting IDs
    interesting_IDs = list(real_df.ID)

    # go through each sv simulated and keep it if it does not overlap any of the regions in df_bed_allRegions
    for ID, sv_series in sim_df.iterrows():

        # define series as df
        sv_series_df = pd.DataFrame({0 : sv_series}).transpose()

        # get the affected regions
        sv_bed, nSVs = get_affected_region_bed_for_SVdf(sv_series_df, "translocations", all_chromosomes)

        # get if they are overlapinmg
        any_regions_overlapping = any(df_bed_allRegions.apply(lambda rprevious: any(sv_bed.apply(lambda rnew: get_is_overlapping_query_vs_target_region(rprevious, rnew), axis=1)), axis=1))

        if not any_regions_overlapping: interesting_IDs.append(ID)

    # get the final df
    df = df.loc[interesting_IDs]
    #df = real_df
    #df = sim_df


    print(df[svtype_to_fieldsDict["translocations"]["all_fields"]])

    # change the positions so that they do not exceed chr boundaries
    posF_to_chrF = svtype_to_fieldsDict["translocations"]["positionField_to_chromosome"]

    for f in svtype_to_fieldsDict["translocations"]["position_fields"]: df[f] = df.apply(lambda r: set_position_to_max(r[f], chr_to_len[r[posF_to_chrF[f]]]), axis=1)

    return df 






def rearrange_genomes_simulateSV(reference_genome, outdir, replace=False, nvars=50, mitochondrial_chromosome="mito_C_glabrata_CBS138", simulated_svtype_to_svfile={}, svtypes={"insertions", "deletions", "inversions", "translocations", "tandemDuplications"}):

    """Runs a simulation of nvars SVs of each type into the reference genome. It will be sepparated by gDNA and mtDNA. mtDNA will only include 5% of the gDNA vars. Everything is written to outdir. simulated_svtype_to_svfile is a dictionary that maps each svtype to a file with it. This function will insert these SVs plus the remaining ones up to nvars (which will be placed randomly in the remaining spots on the genome). Note that only balanced translocations will be simulated, as unbalanced translocations are hard to bechmark based on coverage. 

    Keep in mind that all RSVSim are 1-based coordinates"""


    # change the simulated simulated_svtype_to_svfile to not include translocations
    #simulated_svtype_to_svfile = {svtype : svfile for svtype, svfile in simulated_svtype_to_svfile.items() if svtype!="translocations"} # debug    

    # only random var
    #simulated_svtype_to_svfile = {}

    # map each chrom to a len
    chr_to_len = get_chr_to_len(reference_genome)

    # check that the vars are consistent
    check_consistency_of_svtype_to_svDF(simulated_svtype_to_svfile, set(chr_to_len))


    sakjhakahd

    # define the final outdirs
    final_simulated_SVs_dir = "%s/final_simulated_SVs"%(outdir); 
    final_rearranged_genome = "%s/rearranged_genome.fasta"%final_simulated_SVs_dir
    final_rearranged_genome_finalFile = "%s.performed"%(final_rearranged_genome)


    if file_is_empty(final_rearranged_genome_finalFile) or replace is True:

        # make the folder again
        #delete_folder(outdir) # debug
        make_folder(outdir)
        make_folder(final_simulated_SVs_dir)

        # define the different types of chromosomes. Note that the mtDNA chromosomes will be simulated appart
        all_chromosomes = {s.id for s in SeqIO.parse(reference_genome, "fasta")}
        if mitochondrial_chromosome!="no_mitochondria": mtDNA_chromosomes = set(mitochondrial_chromosome.split(","))
        else: mtDNA_chromosomes = set()
        gDNA_chromosomes = all_chromosomes.difference(mtDNA_chromosomes)

        # map the chromosome to the length
        chrom_to_len = {s.id : len(s.seq) for s in SeqIO.parse(reference_genome, "fasta")}

        # initialize a df where each svtype is mapped against a 
        final_svtype_to_svDF = {}
        for svtype in svtypes:
            if svtype in simulated_svtype_to_svfile: 

                # get the df and change the names
                svDF = pd.read_csv(simulated_svtype_to_svfile[svtype], sep="\t")
                svDF["ID"] = svDF.ID + "_realSV"
                svDF["Name"] = svDF.ID

                # keep all vals but the non real ones
                final_svtype_to_svDF[svtype] = svDF[[c for c in svDF.keys() if "BpSeq" not in c]]

            else: final_svtype_to_svDF[svtype] = pd.DataFrame()


        ###### GENERATE ALL THE RANDOM SIMULATIONS THAT ARE NECESSARY TO ADD ON simulated_svtype_to_svfile ########
        print("generating random simulations")

        # go through each of the mtDNA and gDNA
        for type_genome, chroms in [("mtDNA", mtDNA_chromosomes), ("gDNA", gDNA_chromosomes)]:
            print(type_genome)

            # if there are chroms just continue
            if len(chroms)==0: continue

            # if the genome is mtDNA you shoudl simulate less vars
            if type_genome=="gDNA": vars_to_simulate = nvars
            else: vars_to_simulate = int(nvars*0.05) + 1

            # define the outdir
            genome_outdir = "%s/simulation_%s"%(outdir, type_genome); make_folder(genome_outdir)

            # get the genome 
            genome_file = "%s/genome.fasta"%genome_outdir
            SeqIO.write([c for c in SeqIO.parse(reference_genome, "fasta") if c.id in chroms], genome_file, "fasta")

            # define a bed file with all the data
            all_regions_bed_df = pd.DataFrame({chrom: {"start":1, "end":chrom_to_len[chrom]} for chrom in chroms}).transpose()
            all_regions_bed_df["chromosome"] = all_regions_bed_df.index
            all_regions_bed_df = all_regions_bed_df[["chromosome", "start", "end"]]

            # get the regions without SV where simulations should be placed
            bed_regions_prefix = "%s/bed_regions"%genome_outdir
            regions_without_SV_bed, svtype_to_nSVs = get_bed_df_not_overlapping_with_SVs(all_regions_bed_df, svtypes, simulated_svtype_to_svfile, bed_regions_prefix)

            # simulate random SVs into regions without previous SVs 
            random_sim_dir = "%s/random_SVs"%genome_outdir

            #### GET THE RANDOM INS,INV,DEL,TRA ####

            #if any([file_is_empty("%s/%s.tab"%(random_sim_dir, svtype)) for svtype in {"insertions", "deletions", "translocations", "inversions", "tandemDuplications"}]) or replace is True:
            if True:

                print("generating random SVs")

                # make and delete the folder
                delete_folder(random_sim_dir); make_folder(random_sim_dir)

                # get the cmd of the simulation
                randomSV_cmd = "%s --input_genome %s --outdir %s --regions_bed %s"%(create_random_simulatedSVgenome_R, genome_file, random_sim_dir, regions_without_SV_bed)

                # add the number of each SV that should be added
                svtype_to_arg = {"insertions":"number_Ins", "deletions":"number_Del", "inversions":"number_Inv", "translocations":"number_Tra", "tandemDuplications":"number_Dup"}
                #svtype_to_arg = {"insertions":"number_Ins", "deletions":"number_Del", "inversions":"number_Inv", "translocations":"number_Tra"}
            
                for svtype, number_alreadyGeneratedSVs in svtype_to_nSVs.items(): 
                    if svtype not in svtype_to_arg: continue

                    # define the number of vars to simulate depending on the type
                    if svtype=="translocations": real_vars_to_simulate = len(chroms)-1
                    else: real_vars_to_simulate = vars_to_simulate

                    randomSV_cmd += " --%s %i"%(svtype_to_arg[svtype], max([0, (real_vars_to_simulate-svtype_to_nSVs[svtype])]))

                # define the regions where to simulate translocations, as these are not 
                if "translocations" in simulated_svtype_to_svfile:

                    regions_without_translocations_or_otherSV_bed = get_bed_df_not_overlapping_with_translocations_allChromARM(regions_without_SV_bed, simulated_svtype_to_svfile["translocations"], genome_outdir, chr_to_len)

                else: regions_without_translocations_or_otherSV_bed = regions_without_SV_bed

                randomSV_cmd += " --regions_tra_bed %s"%regions_without_translocations_or_otherSV_bed

                # run the random simulation
                #std_rearranging_genome = "%s/simulation_std.txt"%random_sim_dir
                std_rearranging_genome = "stdout"
                if std_rearranging_genome!="stdout": run_cmd("%s > %s 2>&1"%(randomSV_cmd, std_rearranging_genome))
                else: run_cmd(randomSV_cmd)

                # edit the translocations so that the balanced ones are sorted
                translocations_file = "%s/translocations.tab"%random_sim_dir
                if file_is_empty(translocations_file): open(translocations_file, "w").write("\t".join(["Name", "ChrA", "StartA", "EndA", "SizeA", "ChrB", "StartB", "EndB", "SizeB", "Balanced", "BpSeqA", "BpSeqB"])) # this needs to be 

                # edit the insertions 
                insertions_file = "%s/insertions.tab"%random_sim_dir
                rewrite_insertions_uniformizedFormat_simulateSV(insertions_file)

            ########################################

            # add the simulations into simulated_svtype_to_svDF
            for svtype in final_svtype_to_svDF.keys():
                svDF = final_svtype_to_svDF[svtype]

                # get the new sv
                new_svDF = pd.read_csv("%s/%s.tab"%(random_sim_dir, svtype), sep="\t")
                new_svDF = new_svDF[[c for c in new_svDF.keys() if "BpSeq" not in c]]

                # add the name
                new_svDF["ID"] = new_svDF.Name + "_sim_%s"%type_genome

                # append 
                final_svtype_to_svDF[svtype] = svDF.append(new_svDF, sort=True)

        ###############################################################################################################

        # debug to check that everything but translocations works
        #final_svtype_to_svDF = {svtype : svDF for svtype, svDF in final_svtype_to_svDF.items() if svtype!="translocations"}

        # check that the final_svtype_to_svDF is self consistent

        adkhghafgd


        ####### generate a rearranged genome with all the simulations in final_svtype_to_svDF #########
        print("inserting these random simulations")
        if file_is_empty(final_rearranged_genome) or replace is True:

            # initialize a cmd to create the simulated genome
            targetSV_cmd = "%s --input_genome %s --output_genome %s"%(create_targeted_simulatedSVgenome_R, reference_genome, final_rearranged_genome)

            # write the SVs into files and add to the cmd
            for svtype, svDF in final_svtype_to_svDF.items(): 

                # shift the insertions by 15 bp so that they are not at the beginning of the chrom
                if svtype=="insertions": svDF["StartA"] = svDF["StartA"] + 15

                # keep only the interesting svs
                svDF = svDF[svtype_to_fieldsDict[svtype]["all_fields"]]

                # write file
                svfile = "%s/%s.tab"%(final_simulated_SVs_dir, svtype)
                svDF.to_csv(svfile, sep="\t", header=True, index=False)

                # get cmd
                targetSV_cmd += " --%s_file %s"%(svtype, svfile)

            # run the cmd
            #std_rearranging_genome = "%s/simulation_std.txt"%final_simulated_SVs_dir
            std_rearranging_genome = "stdout"

            if std_rearranging_genome!="stdout": run_cmd("%s > %s 2>&1"%(targetSV_cmd, std_rearranging_genome))
            else: run_cmd(targetSV_cmd)

        jladnjkdjkdha

        # transform the cut-and-paste insertions to copy-and-paste, whenever necessary
        insertions_file = "%s/insertions.tab"%final_simulated_SVs_dir
        transform_cut_and_paste_to_copy_and_paste_insertions(reference_genome, final_rearranged_genome, insertions_file, final_svtype_to_svDF)

        # edit the insertions
        insertions_file = "%s/insertions.tab"%final_simulated_SVs_dir
        rewrite_insertions_uniformizedFormat_simulateSV(insertions_file)

        # rewrite the variants so that they are optimal for comparison 
        translocations_file = "%s/translocations.tab"%final_simulated_SVs_dir
        rewrite_translocations_uniformizedFormat_simulateSV(translocations_file, genome_file)

        # write a file that indicates that this has finsihed
        open(final_rearranged_genome_finalFile, "w").write("finsihed")

    ###############################################################################################

    # return the genome and the set of SV dict
    final_svtype_to_svfile = {svtype : "%s/%s.tab"%(final_simulated_SVs_dir, svtype) for svtype in svtypes}
    print("simulations correctly generated")

    print(final_svtype_to_svfile)

    ljbadjkadjbad

    return final_svtype_to_svfile, final_rearranged_genome




######## random generation of balanced translocatipns #####




            # get the translocations randomly placed
            get_translocations_randomly_placed_in_target_regions(noInsInvDelTan_bed, translocations_file, chrom_to_len, nvars=nvars)


def get_translocations_randomly_placed_in_target_regions(target_regions_bed, translocations_file, chr_to_len, nvars=100):

    """Writes nvars randomly placed translocations in target_regions_bed, and writes them to translocations_file. It will draw as maximum number of translocations as possbile. Half of them will be inverted and half in the same orientation. All of them are balanced."""


    thisdoesnotwork

    print("getting randomly inserted translocations")

    # get the bed into a df
    target_regions_df = pd.read_csv(target_regions_bed, sep="\t", names=["chromosome", "start", "end"], header=None).drop_duplicates()
    target_regions_df.index = list(range(len(target_regions_df)))

    # add the breakpoint region in the middle
    target_regions_df["bp_pos"] = (target_regions_df.start + (target_regions_df.end-target_regions_df.start)/2).apply(int)

    # initialize a dict that will be used for the tra df
    varID_to_colName_to_value = {}

    # initialize a dict that will take each chromosome and simulate it
    chrom_to_nTRA = {chrom:0 for chrom in chr_to_len}

    # keep simulating translocations until you have nvars
    nvars_simulated = 0

    while nvars_simulated<nvars:

        # define the available chromosomes and their target regions
        available_chroms = {chrom for chrom, nTRA in chrom_to_nTRA.items() if nTRA<2}
        target_regions_df = target_regions_df[target_regions_df.chromosome.isin(available_chroms)]

        # if the target df has less than 2 vars with a different chromosome, drop
        if len(set(target_regions_df.chromosome))<2: break

        # pick a regionA
        all_regions = list(target_regions_df.index)
        regionA = target_regions_df.loc[random.choice(all_regions)]

        # get the regions from different chromosomes
        target_regions_df_B = target_regions_df[target_regions_df.chromosome!=regionA["chromosome"]]
        all_regions_B = list(target_regions_df_B.index)
        regionB = target_regions_df_B.loc[random.choice(all_regions_B)]

        # get the dict for this tra
        tra_dict = {"ChrA":regionA["chromosome"], "StartA":1, "EndA":regionA["bp_pos"], "ChrB":regionB["chromosome"], "Balanced":True}

        # define if inverted or not, which defines the orientation of chrB
        is_inverted = bool(random.randrange(0, 2))
        #is_inverted = False

        if is_inverted is True: 
            tra_dict["StartB"] = regionB["bp_pos"]
            tra_dict["EndB"] = chr_to_len[regionB["chromosome"]]

        else:
            tra_dict["StartB"] = 1
            tra_dict["EndB"] = regionB["bp_pos"]

        # add the 
        varID_to_colName_to_value[nvars_simulated] = tra_dict

        # delete both regions from the possibilities
        target_regions_df = target_regions_df.drop(regionA.name)
        target_regions_df = target_regions_df.drop(regionB.name)

        # update the number of times the chromosome is affected
        for chrom in [tra_dict["ChrA"], tra_dict["ChrB"]]: chrom_to_nTRA[chrom] += 1

        # update the number of simulated
        nvars_simulated+=1

    # get df
    tra_df = pd.DataFrame(varID_to_colName_to_value).transpose()[["ChrA", "StartA", "EndA", "ChrB", "StartB", "EndB", "Balanced"]]
    tra_df["Name"] = ["translocation_%i"%(I+1) for I in range(len(tra_df))]
    tra_df["ID"] = tra_df["Name"]

    print(tra_df)


    # write a subset of the vars (with 5 it works)
    #tra_df = tra_df.iloc[0:1] 




    tra_df.to_csv(translocations_file, sep="\t")

    print(chr_to_len)


def transform_cut_and_paste_to_copy_and_paste_insertions(reference_genome, rearranged_genome, insertions_file, svtype_to_svDF):

    """ This function takes a rearranged genome and reinserts the copy-and-paste insertions where they should be """

    print("reinserting-copy-and-paste insertions into %s"%insertions_file)

    # load df and keep the copy-and-paste insertions
    df = pd.read_csv(insertions_file, sep="\t")
    df = df[df.Copied]

    if len(df)>0:

        # define an unmodified genome
        rearranged_genome_unmodified = "%s.unmodified.fasta"%rearranged_genome
        rearranged_genome_unmodified_tmp = "%s.tmp"%rearranged_genome_unmodified

        if file_is_empty(rearranged_genome_unmodified):

            # if the unmodified tmps is writen, replace the rearranged_genome with it
            if not file_is_empty(rearranged_genome_unmodified_tmp): os.rename(rearranged_genome_unmodified_tmp, rearranged_genome)

            # get the rearranged genome seq
            chr_to_rearrangedSeq = {seq.id: str(seq.seq) for seq in SeqIO.parse(rearranged_genome, "fasta")}
            all_rearranged_chromosomes_together = "".join(chr_to_rearrangedSeq.values())

            # get the seq
            chr_to_refSeq = {seq.id: str(seq.seq) for seq in SeqIO.parse(reference_genome, "fasta")}

            # define the length of each chrom
            chr_to_lenSeq = {chrom : len(seq) for chrom, seq in chr_to_refSeq.items()}

            # define all the positions with breakpoints
            df_positions = pd.concat([get_breakpoint_positions_df_in_svDF(svDF) for svtype, svDF in svtype_to_svDF.items()])
            chr_to_bpPositions = dict(df_positions.groupby("Chr").apply(lambda df_c: set(df_c["Pos"])))

            # add the ends of the chromosome, and convert to np array
            for chrom, lenSeq in chr_to_lenSeq.items(): 

                chr_to_bpPositions[chrom].update({1, lenSeq})
                chr_to_bpPositions[chrom] = np.array(sorted(chr_to_bpPositions[chrom]))

            # add the closest breakpoint position of ChrA in the reference
            df["closest_5'breakpoint_position"] = df.apply(lambda r: find_nearest(chr_to_bpPositions[r["ChrA"]][chr_to_bpPositions[r["ChrA"]]<(r["StartA"])], r["StartA"]), axis=1)

            df["closest_3'breakpoint_position"] = df.apply(lambda r: find_nearest(chr_to_bpPositions[r["ChrA"]][chr_to_bpPositions[r["ChrA"]]>(r["EndA"])], r["EndA"]), axis=1)

            # get the 5' sequence (from one position after the closest breakpoint to the position before the breakpoint)
            df["5'sequence"] = df.apply(lambda r: chr_to_refSeq[r["ChrA"]][r["closest_5'breakpoint_position"]:r["StartA"]-1], axis=1)

            # get the 3' sequence (from the position after End to the position before the closest breakpoint)
            df["3'sequence"] = df.apply(lambda r: chr_to_refSeq[r["ChrA"]][r["EndA"]:r["closest_3'breakpoint_position"]-1], axis=1)

            # get the deleted sequence (from the start to the end)
            df["deleted_sequence"] = df.apply(lambda r: chr_to_refSeq[r["ChrA"]][r["StartA"]-1:r["EndA"]], axis=1)

            # change the chromosome seq in the sequence 
            for I, (chrA, seq5, seq3, del_seq) in enumerate(df[["ChrA", "5'sequence", "3'sequence", "deleted_sequence"]].values):
                print("copy-paste-insertion %i.."%I)

                # all seq
                ref_seq = seq5+del_seq+seq3

                # conformation in the rearranged chromosome
                rearranged_seq = seq5+seq3

                # check that the rearranged seq appears once in the genome and the ref seq in the ref genome. And they do not cross.
                chrA_refSeq = chr_to_refSeq[chrA]
                if not(chrA_refSeq.count(ref_seq)==1 and chrA_refSeq.count(rearranged_seq)==0 and all_rearranged_chromosomes_together.count(rearranged_seq)==1 and all_rearranged_chromosomes_together.count(ref_seq)==0): raise ValueError("The sequence is not unique")

                # go through each chrom of the rearranged seqs
                for chrom in chr_to_rearrangedSeq.keys():

                    # get the rearranged sequence
                    seq = cp.deepcopy(chr_to_rearrangedSeq[chrom])

                    # if the rearrangement sequence is in this chromosome, change it
                    if rearranged_seq in seq: 

                        # update the chr_to_rearrangedSeq so that it contains the reference sequence (copied)
                        chr_to_rearrangedSeq[chrom] = seq.replace(rearranged_seq, ref_seq)
                        break

            # get the rearranged genome into the file
            seq_records_list = [SeqRecord(Seq(seq), id=chrom, name=chrom, description=chrom) for chrom, seq in chr_to_rearrangedSeq.items()]

            # write the unmodified one
            print("writing")
            run_cmd("cp %s %s.tmp"%(rearranged_genome, rearranged_genome_unmodified_tmp))
            os.rename("%s.tmp"%rearranged_genome_unmodified_tmp, rearranged_genome_unmodified_tmp)

            # write the modified genome
            SeqIO.write(seq_records_list, rearranged_genome, "fasta")

            # write the modified genome
            os.rename(rearranged_genome_unmodified_tmp, rearranged_genome_unmodified)

        else: print("the insertions have already been modified")


   #### get the correct translocations together with all the simulations ####
        print("inserting final list of translocations...")

        # initialize a cmd to create the simulated genome
        #targetSV_cmd = "%s --input_genome %s --output_genome %s"%(create_targeted_simulatedSVgenome_R, reference_genome, rearranged_genome)

        # add all the positions of the different CMDs
        #for svtype in svtype_to_svDF.keys(): targetSV_cmd += " --%s_file %s/%s.tab"%(svtype, outdir, svtype)

        # run
        #run_cmd(targetSV_cmd)

        # not working

        ## #########################################################################


            # get the variants from simulating reads from an assembly. Always ploidy 1 to get homozygous SVs
            if type_data=="assembly":
                print("getting SVs from assemblies")

                predicted_svtype_to_svfile, df_gridss = generate_tables_of_SV_between_genomes_gridssClove(rearranged_genome, reference_genome, replace=replace, threads=threads)


# old way of considering assemblies

    """
    # OLD WAY
    # get the assembly
    assembly_name = "%s/%s.renamed.fasta"%(assemblies_dir, lrPrefix)
    copied_assembly_name = "%s/%s.nanopore_assembly.fasta"%(outdir, lrPrefix)

    # copy
    if file_is_empty(copied_assembly_name): run_cmd("cp %s %s"%(assembly_name , copied_assembly_name))

    # generate table
    dict_for_df[lrPrefix] = {"assembly":copied_assembly_name, "short_reads1":R1, "short_reads2":R2, "ID":lrPrefix, "short_reads_real1":realR1, "short_reads_real2":realR2}
    """


### OLD get_ID_to_svtype_to_svDF_for_setOfGenomes_highConfidence


  # get the real vars on a different way depending on the type of 
            if realSV_calling_on=="assembly":
                print("getting real variants based on the genome assemblies")

                # softlink the genome
                dest_genomeFile = "%s/genome_%s.fasta"%(all_realVars_dir, ID)
                if file_is_empty(dest_genomeFile): run_cmd("ln -s %s %s"%(row["assembly"], dest_genomeFile))

                # find the real vars
                svtype_to_svfile, df_gridss = generate_tables_of_SV_between_genomes_gridssClove(dest_genomeFile, reference_genome, replace=replace, threads=threads)



# if you stated auto in the reads, generate a 30x coverage bam file
if any([x=="auto" for x in {opt.fastq1, opt.fastq2}]):

    # define the number of reads as a function of the coverage
    read_length = 150
    total_nread_pairs = int((genome_length*30)/read_length)
    print("Simulating %.2fM reads"%(total_nread_pairs/1000000))

    sorted_bam, index_bam = fun.get_simulated_bamFile(opt.outdir, opt.ref, replace=opt.replace, threads=opt.threads, total_nread_pairs=total_nread_pairs, read_length=read_length)
    print("using simulated bam file from %s"%sorted_bam)



   #SNPthreshold_sameSample = get_fractionGenome_different_samplings_from_sorted_bam(sorted_bam, reference_genome, outdir_resamplingBam, replace=replace, threads=threads, coverage_subset_reads=coverage_subset_reads)

    print("We will say that if two samples differ by less than %.4f pct of the genome they are from the same sample. This has been calculated by resampling the input sorted bam with %ix coverage many times. We take twice the value of maxium divergence observed from these value."%(SNPthreshold_sameSample*100, coverage_subset_reads))



    # download the reference genome from GenBank given the taxID and also the gff annotation
    if opt.ref=="auto": opt.ref, opt.gff = fun.get_reference_genome_from_GenBank(opt.target_taxID, new_reference_genome_file, replace=opt.replace)

    # get by GenBank annotation
    elif opt.ref.startswith("GCA_"): opt.ref, opt.gff = fun.get_reference_genome_from_GenBank(opt.ref, new_reference_genome_file, replace=opt.replace)

    # just move the ref genome in the outdir
    else: