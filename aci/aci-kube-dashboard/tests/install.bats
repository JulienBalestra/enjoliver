#!/dgr/bin/bats

@test "dashboard is a regular executable file" {
  [ -x "/usr/bin/dashboard" ]
}

@test "run" {
  run /usr/bin/dashboard --version
  [ "$status" -eq 0 ]
}