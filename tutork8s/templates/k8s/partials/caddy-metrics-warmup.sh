{# Included inside a YAML block scalar; preserve its indentation. #}
                  # Never follow redirects or use an outbound proxy. For native TLS,
                  # --resolve supplies SNI while keeping the connection on loopback.
                  # Certificate trust is irrelevant for this local metrics warm-up.
                  {% for host in warmup.hosts | unique %}
                  host='{{ host | replace("'", "'\"'\"'") }}'
                  curl --silent --show-error --noproxy '*' --max-time 3 --header "Host: $host" --output /dev/null {% if ENABLE_HTTPS and ENABLE_WEB_PROXY %}--insecure --resolve "$host:443:127.0.0.1" "https://$host/robots.txt"{% else %}http://127.0.0.1:80/robots.txt{% endif %}
                  {% endfor %}
                  # Even a 404/502 initializes the route gauge: upstream availability
                  # is not Caddy readiness. A redirect alone is NOT proof of success.
                  metrics=$(curl --fail --silent --show-error --noproxy '*' --max-time 3 \
                    http://127.0.0.1:{{ K8S_CADDY_METRICS_PORT }}/metrics)
                  {% for host in warmup.hosts | unique %}
                  host='{{ host | replace("'", "'\"'\"'") }}'
                  printf '%s\n' "$metrics" | awk -v host="$host" '
                    /^caddy_http_requests_in_flight\{/ {
                      labels = $1
                      gsub(/[{}]/, ",", labels)
                      if (index(labels, ",host=\"" host "\",") &&
                          index(labels, ",handler=\"subroute\",") &&
                          $2 ~ /^[0-9]+([.][0-9]+)?([eE][+-]?[0-9]+)?$/) found = 1
                    }
                    END { exit !found }
                  ' || { echo "Missing Caddy subroute gauge for $host" >&2; exit 1; }
                  {% endfor %}
