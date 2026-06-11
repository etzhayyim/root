package com.etzhayyim.yoro;

import android.app.Notification;
import android.content.ComponentName;
import android.content.Context;
import android.os.Bundle;
import android.provider.Settings;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import androidx.annotation.Nullable;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Deque;
import java.util.List;

/**
 * Listens for LINE app notifications and keeps an in-memory ring buffer that
 * the {@link LineNotificationPlugin} drains on demand.
 *
 * Privacy note: this captures ONLY notifications already delivered to the
 * device by LINE's own push pipeline. The user must explicitly grant the
 * "Notification access" special permission via Settings; the OS shows a clear
 * consent screen listing every app the service can read.
 */
public class LineNotificationListener extends NotificationListenerService {
    public static final String LINE_PACKAGE = "jp.naver.line.android";
    private static final int BUFFER_CAPACITY = 200;

    private static final Deque<Captured> sBuffer = new ArrayDeque<>();
    private static volatile boolean sConnected = false;

    public static boolean isAccessGranted(Context ctx) {
        String enabled = Settings.Secure.getString(
            ctx.getContentResolver(),
            "enabled_notification_listeners"
        );
        if (enabled == null) {
            return false;
        }
        ComponentName self = new ComponentName(ctx, LineNotificationListener.class);
        String flat = self.flattenToString();
        return enabled.contains(flat);
    }

    public static boolean isConnected() {
        return sConnected;
    }

    public static List<Captured> drain() {
        synchronized (sBuffer) {
            List<Captured> out = new ArrayList<>(sBuffer);
            sBuffer.clear();
            Collections.reverse(out); // newest last → chronological order
            return out;
        }
    }

    public static List<Captured> snapshot() {
        synchronized (sBuffer) {
            List<Captured> out = new ArrayList<>(sBuffer);
            Collections.reverse(out);
            return out;
        }
    }

    @Override
    public void onListenerConnected() {
        super.onListenerConnected();
        sConnected = true;
    }

    @Override
    public void onListenerDisconnected() {
        super.onListenerDisconnected();
        sConnected = false;
    }

    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        if (sbn == null) return;
        if (!LINE_PACKAGE.equals(sbn.getPackageName())) return;

        Captured c = capture(sbn);
        if (c == null) return;
        synchronized (sBuffer) {
            sBuffer.addFirst(c);
            while (sBuffer.size() > BUFFER_CAPACITY) {
                sBuffer.removeLast();
            }
        }
    }

    @Nullable
    private Captured capture(StatusBarNotification sbn) {
        Notification n = sbn.getNotification();
        if (n == null) return null;
        Bundle extras = n.extras;
        if (extras == null) return null;

        CharSequence title = extras.getCharSequence(Notification.EXTRA_TITLE);
        CharSequence text = extras.getCharSequence(Notification.EXTRA_TEXT);
        CharSequence bigText = extras.getCharSequence(Notification.EXTRA_BIG_TEXT);
        CharSequence subText = extras.getCharSequence(Notification.EXTRA_SUB_TEXT);

        Captured c = new Captured();
        c.id = sbn.getId();
        c.postTimeMs = sbn.getPostTime();
        c.key = sbn.getKey();
        c.tag = sbn.getTag();
        c.title = title != null ? title.toString() : "";
        c.text = text != null ? text.toString() : "";
        c.bigText = bigText != null ? bigText.toString() : "";
        c.subText = subText != null ? subText.toString() : "";
        c.category = n.category != null ? n.category : "";
        return c;
    }

    public static class Captured {
        public int id;
        public long postTimeMs;
        public String key;
        public String tag;
        public String title;
        public String text;
        public String bigText;
        public String subText;
        public String category;
    }
}
