#!/bin/bash

# Start / Stop the infra needed to do tests
case "$1" in
    "start") 
        # Call ourselves to stop any running containers and reset the test environment
        $0 stop

        echo "****** Sleeping to allow containers to stop ******"
        sleep 10

        echo "****** Creating Elastic TLS Certs ******"
        rm -rf support/certs
        mkdir support/certs
        docker run -it --name create_elastic_certs -e CERTS_DIR=/usr/share/elasticsearch/config/certificates -v `pwd`/support/certs:/certs -v `pwd`/support/certificates:/usr/share/elasticsearch/config/certificates docker.elastic.co/elasticsearch/elasticsearch:7.17.0 bash -c "yum install -y -q -e 0 unzip; ls -la /certs ; ls -la /usr/share/elasticsearch/config/certificates ;if [[ ! -f /certs/bundle.zip ]]; then bin/elasticsearch-certutil cert --silent --pem --in config/certificates/instances.yml -out /certs/bundle.zip ; unzip /certs/bundle.zip -d /certs; fi; chown -R 1000:0 /certs"

        echo "****** Starting Splunk Enterprise via Docker ******"
        docker run -it -d --name splunk_test -e SPLUNK_START_ARGS=--accept-license -e SPLUNK_LICENSE_URI=/tmp/splunk.lic -e SPLUNK_PASSWORD=testpass -p 8000:8000 -p 8089:8089 -v `pwd`/support/Splunk.License:/tmp/splunk.lic -v `pwd`/support/test-data.json:/tmp/test-data.json -v `pwd`/support/test-data-large.json:/tmp/test-data-large.json splunk/splunk:latest
        sleep 5

        echo "****** Starting Elastic via Docker ******"
        docker run -d -it --name elastic_test -e node.store.allow_mmap=false -e node.name=es01 -e cluster.initial_master_nodes=es01 -e xpack.license.self_generated.type=trial -e xpack.security.enabled=true -e xpack.security.http.ssl.enabled=true -e xpack.security.http.ssl.key=/usr/share/elasticsearch/config/certificates/elastic_test/elastic_test.key -e xpack.security.http.ssl.certificate_authorities=/usr/share/elasticsearch/config/certificates/ca/ca.crt -e xpack.security.http.ssl.certificate=/usr/share/elasticsearch/config/certificates/elastic_test/elastic_test.crt -v `pwd`/support/certs:/usr/share/elasticsearch/config/certificates -p 9200:9200 docker.elastic.co/elasticsearch/elasticsearch:7.17.0
        sleep 5

        echo "****** Starting OpenSearch via Docker ******"
        docker run -d -it --name opensearch_test -e discovery.type=single-node -p 9201:9200 opensearchproject/opensearch:1.2.3
        sleep 5

        echo "****** Sleeping to allow containers to start ******"
        sleep 120

        echo "****** Loading Splunk data ******"
        docker exec -it splunk_test sudo /opt/splunk/bin/splunk list user -auth admin:testpass
        docker exec -it splunk_test sudo /opt/splunk/bin/splunk add index bigdata
        docker exec -it splunk_test sudo /opt/splunk/bin/splunk add oneshot /tmp/test-data.json -index main
        docker exec -it splunk_test sudo /opt/splunk/bin/splunk add oneshot /tmp/test-data-large.json -index bigdata

        echo "****** Loading Elastic data ******"
        docker exec elastic_test bin/elasticsearch-setup-passwords auto --batch --url https://localhost:9200 | grep "PASSWORD elastic" | cut -d" " -f 4 > /tmp/elastic_pass.txt
        echo \{\"password\": \"testpass\"\} | curl -u elastic:`cat /tmp/elastic_pass.txt` --cacert support/certs/ca/ca.crt -H "Content-Type: application/json" -XPOST https://localhost:9200/_security/user/elastic/_password  --data-binary @-
        curl -u elastic:testpass --cacert support/certs/ca/ca.crt -H "Content-Type: application/json" -XPOST "https://localhost:9200/_bulk" --data-binary @support/test-data-elastic.json > /dev/null
        curl -u elastic:testpass --cacert support/certs/ca/ca.crt -H "Content-Type: application/json" -XPOST "https://localhost:9200/_bulk" --data-binary @support/test-data-large-elastic.json > /dev/null

        echo "****** Loading OpenSearch data ******"
        curl --insecure -u admin:admin -H "Content-Type: application/json" -XPOST "https://localhost:9201/_bulk" --data-binary @support/test-data-elastic.json > /dev/null
        curl --insecure -u admin:admin -H "Content-Type: application/json" -XPOST "https://localhost:9201/_bulk" --data-binary @support/test-data-large-elastic.json > /dev/null

    ;;
    "stop") 
        echo "****** Stopping any previous Splunk container ******"
        docker kill splunk_test
        docker stop splunk_test
        docker rm splunk_test
        echo "****** Stopping any previous Elastic containers ******"
        docker kill create_elastic_certs
        docker stop create_elastic_certs
        docker rm create_elastic_certs
        docker kill elastic_test
        docker stop elastic_test
        docker rm elastic_test
        echo "****** Stopping any previous OpenSearch containers ******"
        docker kill opensearch_test
        docker stop opensearch_test 
        docker rm opensearch_test
        echo "****** Cleaning up artifacts ******"
        rm -rf support/certs
        rm -f /tmp/elastic_pass.txt    
     ;;
    *) 
        echo "Unknown command: $1"
        exit -1
    ;;
esac

