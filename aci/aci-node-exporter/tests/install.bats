#!/dgr/bin/bats

@test "prometheus is well installed" {
  [ -x /usr/bin/node_exporter ]
}

@test "run" {
  run /usr/bin/node_exporter --version
  [ "$status" -eq 0 ]
}