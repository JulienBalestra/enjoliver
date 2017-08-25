#!/dgr/bin/bats

@test "dashboard is a regular executable file" {
  [ -x "/usr/bin/dashboard" ]
}

@test "run" {
  run /usr/bin/dashboard -h
  [ "$status" -eq 2 ]
}