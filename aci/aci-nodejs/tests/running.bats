#!/dgr/bin/bats


@test "Node" {
  /usr/bin/node --version
  [ $? -eq 0 ]
}

@test "npm" {
  /usr/bin/npm --version
  [ $? -eq 0 ]
}
