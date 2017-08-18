#!/dgr/bin/bats

@test "repo is well installed" {
  [ -x /usr/bin/repo ]
}

