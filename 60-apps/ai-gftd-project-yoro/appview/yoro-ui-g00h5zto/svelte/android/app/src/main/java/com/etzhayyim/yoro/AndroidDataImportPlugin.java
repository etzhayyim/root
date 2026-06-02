package com.etzhayyim.yoro;

import android.Manifest;
import android.database.Cursor;
import android.net.Uri;
import android.provider.ContactsContract;
import android.provider.Telephony;
import androidx.annotation.NonNull;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@CapacitorPlugin(
    name = "AndroidDataImport",
    permissions = {
        @Permission(alias = "contacts", strings = { Manifest.permission.READ_CONTACTS }),
        @Permission(alias = "sms", strings = { Manifest.permission.READ_SMS })
    }
)
public class AndroidDataImportPlugin extends Plugin {

    @PluginMethod
    public void getPermissionStatus(PluginCall call) {
        call.resolve(buildPermissionStatus());
    }

    @PluginMethod
    public void requestImportPermissions(PluginCall call) {
        List<String> aliases = new ArrayList<>();
        if (call.getBoolean("contacts", false)) {
            aliases.add("contacts");
        }
        if (call.getBoolean("sms", false)) {
            aliases.add("sms");
        }
        if (aliases.isEmpty()) {
            aliases.add("contacts");
            aliases.add("sms");
        }
        requestPermissionForAliases(aliases.toArray(new String[0]), call, "permissionsCallback");
    }

    @PermissionCallback
    private void permissionsCallback(PluginCall call) {
        call.resolve(buildPermissionStatus());
    }

    @PluginMethod
    public void getContacts(PluginCall call) {
        if (getPermissionState("contacts") != PermissionState.GRANTED) {
            call.reject("Contacts permission is not granted");
            return;
        }

        try {
            Map<String, List<String>> phoneNumbersByContactId = loadContactFieldMap(
                ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
                ContactsContract.CommonDataKinds.Phone.CONTACT_ID,
                ContactsContract.CommonDataKinds.Phone.NUMBER,
                ContactsContract.CommonDataKinds.Phone.NUMBER + " IS NOT NULL"
            );
            Map<String, List<String>> emailsByContactId = loadContactFieldMap(
                ContactsContract.CommonDataKinds.Email.CONTENT_URI,
                ContactsContract.CommonDataKinds.Email.CONTACT_ID,
                ContactsContract.CommonDataKinds.Email.ADDRESS,
                ContactsContract.CommonDataKinds.Email.ADDRESS + " IS NOT NULL"
            );

            JSArray contacts = new JSArray();
            Cursor cursor = getContext()
                .getContentResolver()
                .query(
                    ContactsContract.Contacts.CONTENT_URI,
                    new String[] {
                        ContactsContract.Contacts._ID,
                        ContactsContract.Contacts.DISPLAY_NAME_PRIMARY
                    },
                    null,
                    null,
                    ContactsContract.Contacts.DISPLAY_NAME_PRIMARY + " COLLATE NOCASE ASC"
                );

            if (cursor != null) {
                try {
                    int idIndex = cursor.getColumnIndexOrThrow(ContactsContract.Contacts._ID);
                    int displayNameIndex = cursor.getColumnIndexOrThrow(ContactsContract.Contacts.DISPLAY_NAME_PRIMARY);
                    while (cursor.moveToNext()) {
                        String contactId = cursor.getString(idIndex);
                        String displayName = cursor.getString(displayNameIndex);
                        JSObject contact = new JSObject();
                        contact.put("id", contactId != null ? contactId : "");
                        contact.put("displayName", displayName != null ? displayName : "");
                        contact.put("phoneNumbers", toJSArray(phoneNumbersByContactId.get(contactId)));
                        contact.put("emails", toJSArray(emailsByContactId.get(contactId)));
                        contacts.put(contact);
                    }
                } finally {
                    cursor.close();
                }
            }

            JSObject result = new JSObject();
            result.put("contacts", contacts);
            call.resolve(result);
        } catch (Exception ex) {
            call.reject("Failed to read contacts", ex);
        }
    }

    @PluginMethod
    public void getSms(PluginCall call) {
        if (getPermissionState("sms") != PermissionState.GRANTED) {
            call.reject("SMS permission is not granted");
            return;
        }

        int requestedLimit = call.getInt("limit", -1);
        boolean unlimited = requestedLimit <= 0;
        int effectiveLimit = unlimited ? Integer.MAX_VALUE : requestedLimit;

        try {
            JSArray messages = new JSArray();
            Cursor cursor = getContext()
                .getContentResolver()
                .query(
                    Uri.parse("content://sms"),
                    new String[] {
                        "_id",
                        Telephony.TextBasedSmsColumns.ADDRESS,
                        Telephony.TextBasedSmsColumns.BODY,
                        Telephony.TextBasedSmsColumns.DATE,
                        Telephony.TextBasedSmsColumns.TYPE
                    },
                    null,
                    null,
                    Telephony.TextBasedSmsColumns.DATE + " DESC"
                );

            if (cursor != null) {
                try {
                    int idIndex = cursor.getColumnIndexOrThrow("_id");
                    int addressIndex = cursor.getColumnIndexOrThrow(Telephony.TextBasedSmsColumns.ADDRESS);
                    int bodyIndex = cursor.getColumnIndexOrThrow(Telephony.TextBasedSmsColumns.BODY);
                    int dateIndex = cursor.getColumnIndexOrThrow(Telephony.TextBasedSmsColumns.DATE);
                    int typeIndex = cursor.getColumnIndexOrThrow(Telephony.TextBasedSmsColumns.TYPE);
                    int count = 0;
                    while (cursor.moveToNext() && count < effectiveLimit) {
                        JSObject sms = new JSObject();
                        sms.put("id", cursor.getString(idIndex));
                        sms.put("address", safeString(cursor.getString(addressIndex)));
                        sms.put("body", safeString(cursor.getString(bodyIndex)));
                        sms.put("timestamp", cursor.getLong(dateIndex));
                        sms.put("type", smsTypeLabel(cursor.getInt(typeIndex)));
                        messages.put(sms);
                        count++;
                    }
                } finally {
                    cursor.close();
                }
            }

            JSObject result = new JSObject();
            result.put("messages", messages);
            result.put("limit", requestedLimit);
            call.resolve(result);
        } catch (Exception ex) {
            call.reject("Failed to read SMS messages", ex);
        }
    }

    @NonNull
    private JSObject buildPermissionStatus() {
        JSObject status = new JSObject();
        status.put("contacts", permissionStateLabel(getPermissionState("contacts")));
        status.put("sms", permissionStateLabel(getPermissionState("sms")));
        return status;
    }

    @NonNull
    private String permissionStateLabel(PermissionState state) {
        if (state == PermissionState.GRANTED) {
            return "granted";
        }
        if (state == PermissionState.DENIED) {
            return "denied";
        }
        return "prompt";
    }

    @NonNull
    private Map<String, List<String>> loadContactFieldMap(Uri uri, String contactIdColumn, String valueColumn, String selection) {
        Map<String, List<String>> result = new LinkedHashMap<>();
        Cursor cursor = getContext()
            .getContentResolver()
            .query(uri, new String[] { contactIdColumn, valueColumn }, selection, null, null);
        if (cursor == null) {
            return result;
        }
        try {
            int contactIdIndex = cursor.getColumnIndexOrThrow(contactIdColumn);
            int valueIndex = cursor.getColumnIndexOrThrow(valueColumn);
            while (cursor.moveToNext()) {
                String contactId = cursor.getString(contactIdIndex);
                String value = cursor.getString(valueIndex);
                if (contactId == null || value == null || value.trim().isEmpty()) {
                    continue;
                }
                List<String> values = result.get(contactId);
                if (values == null) {
                    values = new ArrayList<>();
                    result.put(contactId, values);
                }
                if (!values.contains(value)) {
                    values.add(value);
                }
            }
        } finally {
            cursor.close();
        }
        return result;
    }

    @NonNull
    private JSArray toJSArray(List<String> values) {
        JSArray array = new JSArray();
        if (values == null) {
            return array;
        }
        for (String value : values) {
            array.put(value);
        }
        return array;
    }

    @NonNull
    private String safeString(String value) {
        return value != null ? value : "";
    }

    @NonNull
    private String smsTypeLabel(int type) {
        switch (type) {
            case Telephony.TextBasedSmsColumns.MESSAGE_TYPE_INBOX:
                return "inbox";
            case Telephony.TextBasedSmsColumns.MESSAGE_TYPE_SENT:
                return "sent";
            case Telephony.TextBasedSmsColumns.MESSAGE_TYPE_DRAFT:
                return "draft";
            case Telephony.TextBasedSmsColumns.MESSAGE_TYPE_OUTBOX:
                return "outbox";
            case Telephony.TextBasedSmsColumns.MESSAGE_TYPE_FAILED:
                return "failed";
            case Telephony.TextBasedSmsColumns.MESSAGE_TYPE_QUEUED:
                return "queued";
            default:
                return "unknown:" + type;
        }
    }
}
