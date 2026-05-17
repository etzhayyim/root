DELETE FROM actor_registry WHERE handle = 'yukkuri.etzhayyim.com';

INSERT INTO actor_registry (did, handle, tier, created_at)
    VALUES ('did:web:y5kk5r1x.etzhayyim.com', 'yukkuri.etzhayyim.com', 'T3', NOW());
