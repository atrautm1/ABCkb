#!/bin/bash

BASEDIR="/import"

NODES=(
	"nih.nlm.ncbi.gene.nodes.csv"
	"nodes.psv"
)

RELATIONSHIPS=(
	"CTD_chem_gene_ixns.edges.csv"
	"CTD_chem_go_enriched.edges.csv"
	"CTD_chemicals_diseases.edges.csv"
#	"CTD_diseases.xref.edges.csv"
	"CTD_genes_diseases.edges.csv"
	"disease.ontology.do.edges.csv"
	"disease.ontology.do.xref.edges.csv"
	"ebi.chebi.edges.csv"
	"gene.ontology.go.edges.csv"
	"gene.ontology.go.xref.edges.csv"
	"human.phenotype.hpo.edges.csv"
	"human.phenotype.hpo.xref.edges.csv"
	"mondo.edges.csv"
	"mondo.xref.edges.csv"
	"nih.nlm.mesh.edges.csv"
	"nih.nlm.ncbi.gene.edges.csv"
	"nih.nlm.ncbi.gene.xref.edges.csv"
	"nih.nlm.ncbi.taxonomy.edges.csv"
	#"omim.disease.edges.csv"
	#"omim.disease.xref.edges.csv"
	"usda.nal.thesaurus.edges.csv"
)

TEXT_MINED_RELATIONSHIPS=(
	"p2c__collapsed_edges.psv"
	"c2g__collapsed_edges.psv"
	"g2p__collapsed_edges.psv"
	"p2d__collapsed_edges.psv"
)

if [[ ! -e "/data/databases/graph.db" ]]; then
	while [[ ! -f "/import/FINISHED_IMPORT" ]]; do
		sleep 60
	done
	if [[ -f "/import/p2c__collapsed_edges.psv" ]]; then
		CHECK_FILES=(
			"ls"
			"${NODES[@]}"
			"${RELATIONSHIPS[@]}"
			"${TEXT_MINED_RELATIONSHIPS[@]}"
			"> /dev/null"
		)
		CMD=(
			"neo4j-admin"
			"import"
			"--database=graph.db"
			"--delimiter=|"
			"--array-delimiter=;"
			"--quote=\""
			"--ignore-missing-nodes=true"
			$(printf -- "--nodes=%s\n" "${NODES[@]}")
			$(printf -- "--relationships=%s\n" "${RELATIONSHIPS[@]}")
			$(printf -- "--relationships:text_mined=%s\n" "${TEXT_MINED_RELATIONSHIPS[@]}")
		)
	else
		CHECK_FILES=(
			"ls"
			"${NODES[@]}"
			"${RELATIONSHIPS[@]}"
			"> /dev/null"
		)
		CMD=(
			"neo4j-admin"
			"import"
			"--database=graph.db"
			"--delimiter=|"
			"--array-delimiter=;"
			"--quote=\""
			"--ignore-missing-nodes=true"
			$(printf -- "--nodes=%s\n" "${NODES[@]}")
			$(printf -- "--relationships=%s\n" "${RELATIONSHIPS[@]}")
		)
	fi
	(IFS=$'\n'; cd "${BASEDIR}"; "${CHECK_FILES}" ; "${CMD[@]}")
fi
