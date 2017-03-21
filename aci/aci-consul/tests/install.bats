#!/dgr/bin/bats

@test "consul is well installed" {
  [ -x /usr/bin/consul ]
}

