#!/dgr/bin/bats

@test "dashboard is a regular executable file" {
  [ -x "/usr/bin/dashboard" ]
}