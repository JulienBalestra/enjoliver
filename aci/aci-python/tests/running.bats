#!/dgr/bin/bats


@test "Python is here" {
  /usr/bin/python3.5 --version
  [ $? -eq 0 ]
}

@test "Sqlite3 is here" {
  /usr/bin/python3.5 -c 'import sqlite3'
  [ $? -eq 0 ]
}
