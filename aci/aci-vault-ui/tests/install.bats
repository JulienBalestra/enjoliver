#!/dgr/bin/bats

@test "vault ui is here" {
  [ -d "/opt/vault-ui" ]
}