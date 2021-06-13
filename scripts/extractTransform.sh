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
BROWSER="abckb-browser"
BROWSABLE="false"
export NEO4J_URI="bolt://neo4j:7687"

if [[ ! -f "${PROG}/docker/neo4j/import/FINISHED_IMPORT" ]]; then
    
    time python3 $PROG/scripts/download_sources.py -o "${DATA}"

    if [[ ! -e "${RESULT}" ]]; then
        mkdir -p $PROG/docker/neo4j/{logs,plugins,import,databases}
    fi

    echo "Parsing Structured Vocabularies..."
    echo " "

    time python3 "${PROG}${BARE}" -i "${DATA}/nal/NAL_Thesaurus_2020_XML.zip" -o "${RESULT}" -n usda.nal.thesaurus
    time python3 "${PROG}${BARE}" -i "${DATA}/hpo/hp.obo" -o "${RESULT}" -n human.phenotype.hpo
    time python3 "${PROG}${BARE}" -i "${DATA}/go/go.obo" -o "${RESULT}" -n gene.ontology.go
    time python3 "${PROG}${BARE}" -i "${DATA}/chebi/chebi.obo.gz" -o "${RESULT}" -n ebi.chebi
    time python3 "${PROG}${BARE}" -i "${DATA}/do/doid.obo" -o "${RESULT}" -n disease.ontology.do
    time python3 "${PROG}${BARE}" -i "${DATA}/ncbi_taxonomy/names.dmp" "${DATA}/ncbi_taxonomy/nodes.dmp" -o "${RESULT}" -n nih.nlm.ncbi.taxonomy
    time python3 "${PROG}${BARE}" -i "${DATA}/ncbi_gene/gene_info.gz" "${DATA}/ncbi_gene/gene2go.gz" "${DATA}/ncbi_gene/mim2gene_medgen" "${DATA}/mondo/mondo.obo" -o "${RESULT}" -n nih.nlm.ncbi.gene
    time python3 "${PROG}${BARE}" -i "${DATA}/mesh/d2019.bin" "${DATA}/mesh/c2019.bin" -o "${RESULT}" -n nih.nlm.mesh
    time python3 "${PROG}${BARE}" -i "${DATA}/mondo/mondo.obo" -o "${RESULT}" -n mondo
    echo "Parsing CTD Associations..."
    echo " "

    time python3 "${PROG}${BARE}" -i "${DATA}/ctd/CTD_chem_go_enriched.tsv.gz" \
    "${DATA}/ctd/CTD_chemicals_diseases.tsv.gz" "${DATA}/ctd/CTD_genes_diseases.tsv.gz" \
    "${DATA}/ctd/CTD_chem_gene_ixns.tsv.gz" -o "${RESULT}" -n ctd

    if [[ -e "${DATA}/linguamatics" ]]; then
        # pip3 install nltk
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

while [[ $BROWSABLE = "false" ]]; do
    curl -s "neo4j:7474" >/dev/null && export BROWSABLE="true"
	sleep 5
done

if [[ ! $BROWSABLE = "false" ]]; then

    cd $PROG/$BROWSER
    # This should only run on the first load...
    if [[ ! "$(grep 'SECRET_KEY' ${BROWSER}/.env)" ]]; then
        echo "Generating secret key for django app"
        echo "SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')" >> "${BROWSER}/.env"
    fi
    echo "Starting server"
    # python manage.py migrate
    python manage.py runserver 0.0.0.0:8000
fi