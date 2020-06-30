
# Aliment to Bodily Condition Knowledgebase

Utilizes docker-compose, which should be installed on your machine

## Important! 
- Please ensure your terms of service either individidually or with your institution permits you to utilize the source data. Contact each source listed below to find out more.

## Data Sources
|Name| Data|
|---|---|
|[Chemical Entities of Biological Interest (ChEBI)](https://www.ebi.ac.uk/chebi/)|C|
|[Comparative Toxicogenomics Database](https://www.ctdbase.org)|Co|
|[Disease Ontology](https://www.disease-ontology.org)|D|
|[Gene Ontology](http://www.geneontology.org)|Pa|
|[Human Phenotype Ontology](https://www.hpo.jax.org/app/)|D|
|[Medical Subject Headings](https://www.meshb.nlm.nih.gov/search)|O,Pl,C,Pa,D|
|[MONDO](https://www.mondo.monarchinitiative.org)|D|
|[Nal Thesaurus](https://www.agclass.nal.usda.gov)|Pl,C,D|
|[NCBI Gene](https://www.ncbi.nlm.nih.gov/gene)|G|
|[NCBI Taxonomy](https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi)|O,Pl|
|*[Online Mendelian Inheritance in Man](https://www.omim.org)|G,D|
| Text-mined data from MEDLINE Abstracts|Co|

All sources from their respective URL with the extracted abbreviated node labels -- Plant (Pl), Chemical (C), Gene (G), Pathway (Pa), Phenotype (D), Organism (O), Connectivity (Co) -- are shown here.

\*You must request access to OMIM which you can do here: https://www.omim.org/downloads/


## Instructions for Building the Knowledgebase

Step 1: Prepare for data
- Insert the OMIM key recieved via email into a secrets.json file within the scripts folder following the example_secrets.json format
- Ensure proper permissions for data usage are acquired 
- Allocate at least 8gb ram and 2gb swap for docker
- Storage requirements
    - 20gb total 
    - 16gb purgeable data (docker/data;docker/neo4j/import)
    - 4gb Database size

Step 2: Start docker container

- `docker-compose -f docker-compose.yml up`
-  Make some coffee; this takes about 45 minutes on the first run

Credits:
Dr. Richard Linchangco, Aaron Trautman, Steven Blanchard, Dr. Jeremy Jay, Dr. Cory Brouwer, and the interns that have contributed many features of this program

## Troubleshooting

Downloading data failed...
- I have written a script which should automatically extract pieces from sources in the sources.json file but this may not always work. Some sources prevent programmatic access to their data in which case you will need to manually download the files.
