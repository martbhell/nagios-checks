curl -k -s -XGET 'https://HOSTNAME:PORT/ALIAS/_search?pretty' -d '{
  "facets": {
    "terms": {
      "terms": {
        "field": "audit_uid.raw",
        "size": 10,
        "order": "count",
        "exclude": []
      },
      "facet_filter": {
        "fquery": {
          "query": {
            "filtered": {
              "query": {
                "bool": {
                  "should": [
                    {
                      "query_string": {
                        "query": "audit_a0:*shred*"
                      }
                    },
                    {
                      "query_string": {
                        "query": "audit_exe:*shred*"
                      }
                    }
                  ]
                }
              },
              "filter": {
                "bool": {
                  "must": [
                    {
                      "range": {
                        "@timestamp": {
			  "gt" : "now-1h"
                        }
                      }
                    }
                  ]
                }
              }
            }
          }
        }
      }
    }
  },
  "size": 0
}'
    
