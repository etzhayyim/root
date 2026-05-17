package main

import (
	"context"
	"time"
)

type actorSocialStats struct {
	Followers int
	Following int
	Posts     int
}

func readActorSocialStats(did string) actorSocialStats {
	if did == "" {
		return actorSocialStats{}
	}
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	res, err := rawQuery(ctx, `
SELECT follower_count, following_count, post_count
FROM mv_actor_social_stats
WHERE actor_did = $1
LIMIT 1
`, did)
	if err != nil || len(res.Rows) == 0 {
		return actorSocialStats{}
	}
	row := res.Rows[0]
	return actorSocialStats{
		Followers: parseIntLike(row["follower_count"]),
		Following: parseIntLike(row["following_count"]),
		Posts:     parseIntLike(row["post_count"]),
	}
}
