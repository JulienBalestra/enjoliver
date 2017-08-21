#!/dgr/bin/bats

@test "tiller is a regular executable file" {
  [ -x "/usr/bin/tiller" ]
}

@test "run" {
  run /usr/bin/tiller -h
  [ "$status" -eq 2 ]
}