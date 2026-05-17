package main

import (
	"context"
	"testing"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

func TestReadActorSocialStatsFromLiveMV(t *testing.T) {
	oldRawQuery := rawQuery
	t.Cleanup(func() { rawQuery = oldRawQuery })

	rawQuery = func(_ context.Context, sql string, args ...any) (*db.RawResult, error) {
		if len(args) != 1 || args[0] != "did:web:sample.etzhayyim.com" {
			t.Fatalf("unexpected args: %#v", args)
		}
		return &db.RawResult{
			Rows: []map[string]any{{
				"follower_count":  "10",
				"following_count": "5",
				"post_count":      3,
			}},
		}, nil
	}

	got := readActorSocialStats("did:web:sample.etzhayyim.com")
	if got.Followers != 10 || got.Following != 5 || got.Posts != 3 {
		t.Fatalf("unexpected stats: %+v", got)
	}
}
