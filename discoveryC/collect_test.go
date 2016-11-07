package main

import (
	"testing"
)

func TestCollectData(t *testing.T) {
	data := CollectData()
	if len(data.Interfaces) < 1 {
		t.Error("len(data.Interfaces) < 1")
	}
}
