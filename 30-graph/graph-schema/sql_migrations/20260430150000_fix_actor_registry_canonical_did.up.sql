DELETE FROM actor_registry WHERE handle = 'yukkuri.gftd.ai';

INSERT INTO actor_registry (did, handle, tier, created_at)
    VALUES ('did:web:y5kk5r1x.gftd.ai', 'yukkuri.gftd.ai', 'T3', NOW());
