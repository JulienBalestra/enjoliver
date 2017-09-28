#!/dgr/bin/bats

@test "traefik is well installed" {
  [ -x /usr/bin/traefik ]
}

@test "run" {
  run /usr/bin/traefik version
  [ "$status" -eq 0 ]
}