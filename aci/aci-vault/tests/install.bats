#!/dgr/bin/bats

@test "vault is well installed" {
  [ -x /usr/bin/vault ]
}

@test "run" {
  run /usr/bin/vault --version
  [ "$status" -eq 0 ]
}