#!/dgr/bin/bats

@test "discoveryC is a regular executable file" {
  [ -f "/usr/bin/discoveryC" ]
  [ -x "/usr/bin/discoveryC" ]
}
