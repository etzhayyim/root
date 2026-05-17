DELETE FROM actor_registry WHERE handle = 'yukkuri.etzhayyim.com';

INSERT INTO actor_registry (did, handle, tier, created_at)
    VALUES ('did:plc:yukkuri', 'yukkuri.etzhayyim.com', 'T3', NOW());
