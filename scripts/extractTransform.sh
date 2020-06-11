#!/bin/bash

umask 007
set -eu

if [[ -e "/app" ]]; then
    cd /app
fi

PROG="$(pwd)"
BARE="/scripts/parsers/bareSourceParser.py"
CTD="/parseCTD.py"
LINGUAMATICS_SCRIPT="/scripts/parsers/linguamatics.py"
DATA="${PROG}/docker/data"
RESULT="${PROG}/docker/neo4j/import/"

if [[ ! -f "${PROG}/docker/neo4j/import/FINISHED_IMPORT" ]]; then

    pip install requests
    
    time python3 $PROG/scripts/download_sources.py -o "${DATA}"
    
    pip install treelib

    if [[ ! -e "${RESULT}" ]]; then
        mkdir -p $PROG/docker/neo4j/{logs,plugins,import,databases}
    fi

    echo "Parsing Structured Vocabularies..."
    echo " "

    time python3 "${PROG}${BARE}" -i "${DATA}/nal/NAL_Thesaurus_2019_XML.zip" -o "${RESULT}" -n usda.nal.thesaurus
    time python3 "${PROG}${BARE}" -i "${DATA}/hpo/hp.obo" -o "${RESULT}" -n human.phenotype.hpo
    time python3 "${PROG}${BARE}" -i "${DATA}/go/go.obo" -o "${RESULT}" -n gene.ontology.go
    time python3 "${PROG}${BARE}" -i "${DATA}/chebi/chebi.obo.gz" -o "${RESULT}" -n ebi.chebi
    time python3 "${PROG}${BARE}" -i "${DATA}/do/doid.obo" -o "${RESULT}" -n disease.ontology.do
    time python3 "${PROG}${BARE}" -i "${DATA}/omim/genemap2.txt" "${DATA}/omim/mim2gene.txt" -o "${RESULT}" -n omim.disease
    time python3 "${PROG}${BARE}" -i "${DATA}/ncbi_taxonomy/names.dmp" "${DATA}/ncbi_taxonomy/nodes.dmp" -o "${RESULT}" -n nih.nlm.ncbi.taxonomy
    time python3 "${PROG}${BARE}" -i "${DATA}/ncbi_gene/gene_info.gz" "${DATA}/ncbi_gene/gene2go.gz" -o "${RESULT}" -n nih.nlm.ncbi.gene
    time python3 "${PROG}${BARE}" -i "${DATA}/mesh/d2019.bin" "${DATA}/mesh/c2019.bin" -o "${RESULT}" -n nih.nlm.mesh
    time python3 "${PROG}${BARE}" -i "${DATA}/mondo/mondo.obo" -o "${RESULT}" -n mondo
    echo "Parsing CTD Associations..."
    echo " "

    time python3 "${PROG}${BARE}" -i "${DATA}/ctd/CTD_chem_go_enriched.tsv.gz" \
    "${DATA}/ctd/CTD_chemicals_diseases.tsv.gz" "${DATA}/ctd/CTD_genes_diseases.tsv.gz" \
    "${DATA}/ctd/CTD_chem_gene_ixns.tsv.gz" -o "${RESULT}" -n ctd

    if [[ -e "${DATA}/linguamatics" ]]; then
        pip3 install nltk
        python3 $PROG/scripts/nltk_downloader.py
        echo "Parsing Text Mined Associations..."
        echo " "
        time python3 "${PROG}${LINGUAMATICS_SCRIPT}" -i "${DATA}/linguamatics/1p2c/" -o "${RESULT}/p2c_"
        time python3 "${PROG}${LINGUAMATICS_SCRIPT}" -i "${DATA}/linguamatics/2c3g/" -o "${RESULT}/c2g_"
        time python3 "${PROG}${LINGUAMATICS_SCRIPT}" -i "${DATA}/linguamatics/3g4p/" -o "${RESULT}/g2p_"
        time python3 "${PROG}${LINGUAMATICS_SCRIPT}" -i "${DATA}/linguamatics/4p5d/" -o "${RESULT}/p2d_"
    fi
    # Deduplicate nodes
    time python3 "${PROG}/scripts/de_duplicate.py" "$RESULT"
    # Communicate with other process to begin building KB
    exec touch $RESULT/FINISHED_IMPORT
fi