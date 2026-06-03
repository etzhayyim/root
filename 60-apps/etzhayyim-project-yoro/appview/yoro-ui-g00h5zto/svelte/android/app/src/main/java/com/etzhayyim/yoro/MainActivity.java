package com.etzhayyim.yoro;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import androidx.core.view.WindowCompat;
import com.getcapacitor.BridgeActivity;
import java.util.Set;

public class MainActivity extends BridgeActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        registerPlugin(AndroidDataImportPlugin.class);
        registerPlugin(LineNotificationPlugin.class);
        super.onCreate(savedInstanceState);
        // Enable edge-to-edge after Capacitor initializes WebView
        // so env(safe-area-inset-bottom) is correctly reported to the WebView
        WindowCompat.setDecorFitsSystemWindows(getWindow(), false);
        handleAuthCallback(getIntent());
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        handleAuthCallback(intent);
    }

    private void handleAuthCallback(Intent intent) {
        if (intent == null) {
            return;
        }
        Uri data = intent.getData();
        if (data == null || !"com.etzhayyim.yoro".equals(data.getScheme())) {
            return;
        }

        String host = data.getHost();
        boolean isDefaultCallback = "callback".equals(host);
        boolean isLegacyCallback = "auth".equals(host) && "/callback".equals(data.getPath());
        if (!isDefaultCallback && !isLegacyCallback) {
            return;
        }

        String target = data.getQueryParameter("target");
        String normalizedTarget = (target == null || target.isEmpty()) ? "/" : target;
        if (!normalizedTarget.startsWith("/")) {
            normalizedTarget = "/" + normalizedTarget;
        }

        Uri targetUri = Uri.parse("https://yoro.etzhayyim.com" + normalizedTarget);
        Uri.Builder builder = targetUri.buildUpon().clearQuery();
        appendQueryParameters(builder, targetUri, null);
        appendQueryParameters(builder, data, "target");
        builder.appendQueryParameter("__native_clerk_callback", "1");
        // Pass the fragment from the deep link (contains #auth={session_json})
        String callbackFragment = data.getEncodedFragment();
        builder.encodedFragment(callbackFragment != null && !callbackFragment.isEmpty()
                ? callbackFragment : targetUri.getEncodedFragment());
        final String loadUrl = builder.build().toString();

        if (bridge != null && bridge.getWebView() != null) {
            bridge.getWebView().post(() -> bridge.getWebView().loadUrl(loadUrl));
        }
    }

    private void appendQueryParameters(Uri.Builder builder, Uri source, String excludedKey) {
        Set<String> queryNames = source.getQueryParameterNames();
        for (String key : queryNames) {
            if (excludedKey != null && excludedKey.equals(key)) {
                continue;
            }
            for (String value : source.getQueryParameters(key)) {
                builder.appendQueryParameter(key, value);
            }
        }
    }
}
