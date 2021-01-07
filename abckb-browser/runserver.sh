#!/bin/bash

PORT="7474"
echo "neo4j bolt is on port ${PORT}"

if [[ -z ${PORT} ]]
  then
     echo "Is ${CONTAINER} running neo4j?  I don't see it..."
     echo 
     echo "Usage:"
     echo "  wait4bolt_outside docker_container"
     echo "  e.g. wait4bolt_outside neo_ag"
     exit 1
fi

echo "wait for neo4j bolt to respond at port ${PORT}"

# this returns before server is ready
#    curl -i http://127.0.0.1:${PORT} 2>&1 | grep -c -e '200 OK' || break 

# try an actual query as test?
docker exec -e NEO4J_USERNAME -e NEO4J_PASSWORD -t ${CONTAINER} \
  bash -c "until echo 'match (n) return count(n);' | bin/cypher-shell -a bolt://localhost:${PORT
}; do echo $? ; sleep 1; done"


echo 'neo4j online!'