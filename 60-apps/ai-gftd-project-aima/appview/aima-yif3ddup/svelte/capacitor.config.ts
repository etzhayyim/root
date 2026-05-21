import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'ai.gftd.aima',
  appName: 'AIMA',
  webDir: 'build',
  server: {
    androidScheme: 'https',
    iosScheme: 'capacitor',
  },
  plugins: {
    Keyboard: {
      resize: 'body',
      resizeOnFullScreen: true,
    },
    StatusBar: {
      style: 'dark',
      backgroundColor: '#09090b',
    },
  },
};

export default config;
