#!/dgr/bin/bats

@test "ip is well installed" {
  [ -f /usr/bin/ip ]
}

@test "is able to run" {
  run /usr/bin/ip -V
  [ "$status" -eq 0 ]
}
