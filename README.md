
# Aliment to Bodily Condition Knowledgebase

Utilizes docker-compose, which should be installed on your machine

## Important! 
- Please ensure your terms of service either individidually or with your institution permits you to utilize the source data. Contact each source listed below to find out more.

## Data sources:
- Chemical Entities of Biological Interest (ChEBI)
    - https://www.ebi.ac.uk/chebi/
- Comparative Toxicogenomics Database
    - https://www.ctdbase.org
- Disease Ontology
    - https://www.disease-ontology.org
- Gene Ontology
    - http://www.geneontology.org
- Human Phenotype Ontology
    - https://www.hpo.jax.org/app/
- Medical Subject Headings
    - https://www.meshb.nlm.nih.gov/search
- MONDO
    - https://www.mondo.monarchinitiative.org
- Nal Thesaurus
    - https://www.agclass.nal.usda.gov
- NCBI Gene
    - https://www.ncbi.nlm.nih.gov/gene
- NCBI Taxonomy
    - https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi
- Online Mendelian Inheritance in Man 
    - https://www.omim.org
    - You must request access which you can do here: https://www.omim.org/downloads/
- Text-mined data from MEDLINE Abstracts (optional)

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
