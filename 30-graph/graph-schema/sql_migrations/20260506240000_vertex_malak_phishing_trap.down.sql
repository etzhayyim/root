DROP INDEX IF EXISTS idx_malak_trap_message_sender_time;

DROP INDEX IF EXISTS idx_malak_trap_message_recipient_time;

DROP INDEX IF EXISTS idx_malak_trap_message_evidence;

DROP INDEX IF EXISTS idx_malak_phishing_trap_address;

DROP TABLE IF EXISTS vertex_malak_trap_message;

DROP TABLE IF EXISTS vertex_malak_phishing_trap;

FLUSH;
