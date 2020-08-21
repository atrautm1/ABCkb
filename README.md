
# Aliment to Bodily Condition Knowledgebase

Utilizes docker-compose, which should be installed on your machine

## Important! 
- Please ensure your terms of service either individidually or with your institution permits you to utilize the source data. Contact each source listed below to find out more.
- Additionally, this database is intended for nutrition research and is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your health care provider with any medical or health-related questions. Don't disregard medical advice or delay seeking treatment because of anything you find in this database. 

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
|[NCBI MedGen](https://www.ncbi.nlm.nih.gov/books/NBK159970/)|Co|
| Text-mined data from MEDLINE Abstracts|Co|

All sources from their respective URL with the extracted abbreviated node labels -- Plant (Pl), Chemical (C), Gene (G), Pathway (Pa), Phenotype (D), Organism (O), Connectivity (Co) -- are shown here.


## Instructions for Building the Knowledgebase
Step 1: Clone/fork this project
`git clone github.com/atrautm1/ABCkb`

Step 2: Prepare for data
- Insert the OMIM key recieved via email into a secrets.json file within the scripts folder following the example_secrets.json format
    - The key is in the url you recieve from them: "data.omim.org/downloads/\<secret-key\>/filename.txt"
- Ensure proper permissions for data usage are acquired 
- Allocate at least 8gb ram and 2gb swap for docker
- Storage requirements
    - 20gb total
    - 16gb purgeable data (docker/data;docker/neo4j/import)
    - 4gb Database size

Step 4: Download the NLP results place them into the docker/data folder
- [NLP results](https://figshare.com/s/f237538984b7e271f071)
- uncompress the archive, but leave the individual tsv files compressed
    - `tar -xzvf linguamatics.tar.gz` 

Step 3: Start docker container

- `docker-compose -f docker-compose.yml up`
-  Make some coffee; this takes about 45 minutes on the first run

Credits:
Dr. Richard Linchangco, Aaron Trautman, Steven Blanchard, Dr. Jeremy Jay, Dr. Cory Brouwer, and the interns that have contributed many features of this program

## How to use the knowledgebase

neo4j can be used either in browser or via the terminal once the ABCkb finishes building
- After the Knowledgebase is built, you should see that an instance is running on localhost:7474/
- In the terminal, you can run cypher-shell "<your-query>;"

[Cypher reference guide](https://neo4j.com/docs/pdf/cypher-refcard-3.5.pdf)

Here are some example queries to get you started..

1. Does the node exist?
- `MATCH (n) WHERE n.name = "Avena sativa" 	OR "Avena sativa" in n.synonyms RETURN n`

2. Open discovery with Avena sativa...
- `MATCH p=(:Plant {name:"Avena sativa"})-[:text_mined]->(:Chemical)-[:text_mined]->(:Gene) RETURN p`

3. Closed discovery with Avena sativa...
- `MATCH p=(:Plant {name:"Avena sativa"})-[:text_mined]->(:Chemical)-[:text_mined]->(:Gene {name:"HSD11B1"}) RETURN p`

4. Show schema
- There is not really a "schema" for graph databases but the following command works pretty well to show connectivity
- `call db.schema.visualization()`

## Troubleshooting

Downloading data failed...
- I have written a script which should automatically extract pieces from sources in the sources.json file but this may not always work. Some sources prevent programmatic access to their data in which case you will need to manually download the files.

I want to add my own data...
- There are a couple options depending on how you want to proceed
1. Add it to the already generated database using neo4j
    - [Neo4j IMPORT CSV documentation](https://neo4j.com/docs/cypher-manual/3.5/clauses/load-csv/)

2. Add it when building the KB
<!-- Add the source to docker/data
- Create a parser in scripts/parsers and add it to bareSourceParser.py
- Add the appropriate line in extractTransform.sh
- Add the relevant files to build_kb.sh
- Remove the old database instance in docker/neo4j/databases
- Remove the IMPORT_FINISHED flag in docker/neo4j/import
- Run kb -->



