package main

import (
	"context"
	"testing"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

func TestReadActorRepoStatsFromLiveMV(t *testing.T) {
	oldRawQuery := rawQuery
	t.Cleanup(func() { rawQuery = oldRawQuery })

	rawQuery = func(_ context.Context, sql string, args ...any) (*db.RawResult, error) {
		if len(args) != 1 || args[0] != "did:web:sample.etzhayyim.com" {
			t.Fatalf("unexpected args: %#v", args)
		}
		return &db.RawResult{
			Rows: []map[string]any{{
				"descendant_follower_count":  "7",
				"descendant_following_count": "4",
				"descendant_subdid_count":    "2",
				"repo_record_count":          11,
			}},
		}, nil
	}

	got := readActorRepoStats("did:web:sample.etzhayyim.com")
	if got.DescendantFollowers != 7 || got.DescendantFollowing != 4 || got.DescendantSubDIDs != 2 || got.RepoRecords != 11 {
		t.Fatalf("unexpected stats: %+v", got)
	}
}
