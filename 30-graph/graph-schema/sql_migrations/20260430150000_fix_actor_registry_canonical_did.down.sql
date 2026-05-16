DELETE FROM actor_registry WHERE handle = 'yukkuri.gftd.ai';

INSERT INTO actor_registry (did, handle, tier, created_at)
    VALUES ('did:plc:yukkuri', 'yukkuri.gftd.ai', 'T3', NOW());
