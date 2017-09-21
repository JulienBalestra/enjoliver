#!/dgr/bin/bats

@test "rktlet is well installed" {
  [ -x /usr/bin/rktlet ]
}


@test "run" {
  run /usr/bin/rktlet -h
  [ "$status" -eq 2 ]
}
