package main

import (
	"context"
	"time"
)

type actorRepoStats struct {
	DescendantFollowers int
	DescendantFollowing int
	DescendantSubDIDs   int
	RepoRecords         int
}

func readActorRepoStats(did string) actorRepoStats {
	if did == "" {
		return actorRepoStats{}
	}
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	res, err := rawQuery(ctx, `
SELECT
  descendant_follower_count,
  descendant_following_count,
  descendant_subdid_count,
  repo_record_count
FROM mv_actor_repo_stats
WHERE actor_did = $1
LIMIT 1
`, did)
	if err != nil || len(res.Rows) == 0 {
		return actorRepoStats{}
	}
	row := res.Rows[0]
	return actorRepoStats{
		DescendantFollowers: parseIntLike(row["descendant_follower_count"]),
		DescendantFollowing: parseIntLike(row["descendant_following_count"]),
		DescendantSubDIDs:   parseIntLike(row["descendant_subdid_count"]),
		RepoRecords:         parseIntLike(row["repo_record_count"]),
	}
}
