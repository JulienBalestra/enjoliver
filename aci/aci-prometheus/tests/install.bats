#!/dgr/bin/bats

@test "prometheus is well installed" {
  [ -x /usr/bin/prometheus ]
}

@test "run" {
  run /usr/bin/prometheus --version
  [ "$status" -eq 0 ]
}
