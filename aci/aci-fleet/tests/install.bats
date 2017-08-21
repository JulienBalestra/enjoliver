#!/dgr/bin/bats

@test "fleet is well installed" {
  [ -x /usr/bin/fleetd ]
  [ -x /usr/bin/fleetctl ]
}


@test "run" {
  run /usr/bin/fleetctl --version
  [ "$status" -eq 0 ]

  run /usr/bin/fleetd --version
  [ "$status" -eq 0 ]
}