#!/dgr/bin/bats

@test "prometheus is well installed" {
  [ -x /usr/bin/prometheus ]
}

