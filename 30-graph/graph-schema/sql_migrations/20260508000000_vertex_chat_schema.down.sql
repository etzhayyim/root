DROP MATERIALIZED VIEW IF EXISTS mv_chat_active_24h;

DROP MATERIALIZED VIEW IF EXISTS mv_chat_artifact_size_per_owner;

DROP MATERIALIZED VIEW IF EXISTS mv_chat_recent_conversations;

DROP TABLE IF EXISTS edge_chat_invocation_from_message;

DROP TABLE IF EXISTS edge_chat_artifact_from_message;

DROP TABLE IF EXISTS edge_chat_message_replies_to;

DROP TABLE IF EXISTS edge_chat_message_in_conversation;

DROP TABLE IF EXISTS vertex_chat_session;

DROP TABLE IF EXISTS vertex_chat_memory;

DROP TABLE IF EXISTS vertex_chat_checkpoint;

DROP TABLE IF EXISTS vertex_chat_artifact;

DROP TABLE IF EXISTS vertex_chat_tool_invocation;

DROP TABLE IF EXISTS vertex_chat_message;

DROP TABLE IF EXISTS vertex_chat_conversation;
