DROP MATERIALIZED VIEW IF EXISTS mv_gworkspace_account_health;

DROP TABLE IF EXISTS edge_gmeet_recording_drive_file;

DROP TABLE IF EXISTS edge_gmeet_conference_calendar_event;

DROP TABLE IF EXISTS edge_gmeet_conference_participant;

DROP TABLE IF EXISTS vertex_gmeet_recording;

DROP TABLE IF EXISTS vertex_gmeet_participant;

DROP TABLE IF EXISTS vertex_gmeet_conference;

DROP TABLE IF EXISTS vertex_gmeet_account;

DROP TABLE IF EXISTS edge_gslides_slide_in_presentation;

DROP TABLE IF EXISTS vertex_gslides_slide;

DROP TABLE IF EXISTS vertex_gslides_presentation;

DROP TABLE IF EXISTS vertex_gslides_account;

DROP TABLE IF EXISTS edge_gsheets_sheet_in_spreadsheet;

DROP TABLE IF EXISTS vertex_gsheets_sheet;

DROP TABLE IF EXISTS vertex_gsheets_spreadsheet;

DROP TABLE IF EXISTS vertex_gsheets_account;

DROP TABLE IF EXISTS vertex_gdocs_revision;

DROP TABLE IF EXISTS vertex_gdocs_document;

DROP TABLE IF EXISTS vertex_gdocs_account;

DROP TABLE IF EXISTS edge_gtasks_task_parent;

DROP TABLE IF EXISTS edge_gtasks_task_in_list;

DROP TABLE IF EXISTS vertex_gtasks_task;

DROP TABLE IF EXISTS vertex_gtasks_list;

DROP TABLE IF EXISTS vertex_gtasks_account;

DROP TABLE IF EXISTS edge_gcontacts_contact_group;

DROP TABLE IF EXISTS vertex_gcontacts_group;

DROP TABLE IF EXISTS vertex_gcontacts_contact;

DROP TABLE IF EXISTS vertex_gcontacts_account;

DROP TABLE IF EXISTS edge_gdrive_file_permission;

DROP TABLE IF EXISTS edge_gdrive_file_parent;

DROP TABLE IF EXISTS vertex_gdrive_watch_channel;

DROP TABLE IF EXISTS vertex_gdrive_revision;

DROP TABLE IF EXISTS vertex_gdrive_permission;

DROP TABLE IF EXISTS vertex_gdrive_file;

DROP TABLE IF EXISTS vertex_gdrive_account;

DROP TABLE IF EXISTS edge_gcal_event_attendee;

DROP TABLE IF EXISTS edge_gcal_event_in_calendar;

DROP TABLE IF EXISTS vertex_gcal_watch_channel;

DROP TABLE IF EXISTS vertex_gcal_attendee;

DROP TABLE IF EXISTS vertex_gcal_event;

DROP TABLE IF EXISTS vertex_gcal_calendar;

DROP TABLE IF EXISTS vertex_gcal_account;
