package com.etzhayyim.yoro;

import android.content.Intent;
import android.provider.Settings;
import androidx.annotation.NonNull;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.util.List;

/**
 * Bridge for the Svelte side to read LINE notifications captured by
 * {@link LineNotificationListener}.
 *
 * The user must grant the "Notification access" special permission first via
 * the system Settings screen, which we surface through {@link #openSettings}.
 */
@CapacitorPlugin(name = "LineNotification")
public class LineNotificationPlugin extends Plugin {

    @PluginMethod
    public void getStatus(PluginCall call) {
        JSObject status = new JSObject();
        status.put("accessGranted", LineNotificationListener.isAccessGranted(getContext()));
        status.put("connected", LineNotificationListener.isConnected());
        status.put("bufferSize", LineNotificationListener.snapshot().size());
        call.resolve(status);
    }

    @PluginMethod
    public void openSettings(PluginCall call) {
        try {
            Intent intent = new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(intent);
            call.resolve();
        } catch (Exception ex) {
            call.reject("Failed to open notification access settings", ex);
        }
    }

    @PluginMethod
    public void drain(PluginCall call) {
        List<LineNotificationListener.Captured> drained = LineNotificationListener.drain();
        JSObject result = new JSObject();
        result.put("notifications", toJsArray(drained));
        result.put("count", drained.size());
        call.resolve(result);
    }

    @PluginMethod
    public void snapshot(PluginCall call) {
        List<LineNotificationListener.Captured> rows = LineNotificationListener.snapshot();
        JSObject result = new JSObject();
        result.put("notifications", toJsArray(rows));
        result.put("count", rows.size());
        call.resolve(result);
    }

    @NonNull
    private JSArray toJsArray(List<LineNotificationListener.Captured> rows) {
        JSArray arr = new JSArray();
        for (LineNotificationListener.Captured c : rows) {
            JSObject o = new JSObject();
            o.put("id", c.id);
            o.put("postTimeMs", c.postTimeMs);
            o.put("key", safe(c.key));
            o.put("tag", safe(c.tag));
            o.put("title", safe(c.title));
            o.put("text", safe(c.text));
            o.put("bigText", safe(c.bigText));
            o.put("subText", safe(c.subText));
            o.put("category", safe(c.category));
            arr.put(o);
        }
        return arr;
    }

    @NonNull
    private String safe(String s) {
        return s != null ? s : "";
    }
}
