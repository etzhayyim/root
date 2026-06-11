import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.etzhayyim.yoro',
  appName: 'YORO',
  webDir: 'build',
  server: {
    androidScheme: 'https',
    iosScheme: 'capacitor',
    cleartext: false,
  },
  plugins: {
    Keyboard: {
      resize: 'body',
      resizeOnFullScreen: true,
    },
    StatusBar: {
      style: 'dark',
      backgroundColor: '#0a0a0a',
    },
    SplashScreen: {
      launchAutoHide: true,
      backgroundColor: '#0a0a0a',
    },
  },
};

export default config;
