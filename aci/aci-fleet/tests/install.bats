#!/dgr/bin/bats

@test "fleet is well installed" {
  [ -x /usr/bin/fleetd ]
  [ -x /usr/bin/fleetctl ]
}

