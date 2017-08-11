package main

import (
	"sort"
	"strings"
)

func joinMap(m map[string][]string, sep string) string {
	var keys []string

	for v := range m {
		keys = append(keys, v)
	}
	sort.Strings(keys)
	return strings.Join(keys, sep)
}
