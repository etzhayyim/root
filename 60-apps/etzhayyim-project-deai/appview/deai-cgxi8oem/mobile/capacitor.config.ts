import { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.etzhayyim.deai",
  appName: "deai — Spirit Match",
  webDir: "../svelte/build",
  server: {
    androidScheme: "https",
    iosScheme: "https",
    hostname: "decom.etzhayyim.ai",
    allowNavigation: [
      "decom.etzhayyim.ai",
      "*.etzhayyim.com",
      // Spirit-in-Physics research API (SSoT for research data)
      "spirit-in-physics.com",
      "*.spirit-in-physics.com",
      "sip.junkawasaki.com",
      // Hume AI emotion analysis
      "api.hume.ai",
      "*.hume.ai",
      "localhost",
      "127.0.0.1",
    ],
  },
  ios: {
    contentInset: "always",
    allowsLinkPreview: false,
    minVersion: "14.0",
  },
  android: {
    // Health Connect for HRV (optional)
  },
  plugins: {
    CapacitorHttp: { enabled: true },
    Camera: {
      // Hume face analysis: camera access for emotion capture
      // Raw images processed on-device; only scores transmitted
    },
  },
};

export default config;
