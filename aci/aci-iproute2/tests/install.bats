#!/dgr/bin/bats

@test "ip is well installed" {
  [ -f /usr/bin/ip ]
}

