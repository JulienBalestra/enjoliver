#!/dgr/bin/bats -x

@test "ES should be running" {
  run wget -qO- http://localhost:9200
  [ "$status" -eq 0 ]
  [ "${lines[0]}" = "{" ]
  [ "${lines[1]}" = "  \"status\" : 200," ]
}
