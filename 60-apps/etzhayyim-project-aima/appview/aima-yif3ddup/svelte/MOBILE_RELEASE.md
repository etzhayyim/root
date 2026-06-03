# AIMA mobile release

`aima.etzhayyim.com` is packaged as a Capacitor app in this directory. Native shells live in `ios/` and `android/`. Store publishing is driven by Fastlane.

## Setup

1. Install Ruby gems with `bundle install`.
2. Copy `fastlane/.env.default` to `fastlane/.env` and fill in the App Store Connect / Play Console credentials.
3. For Android signing, either:
   - set `ANDROID_KEYSTORE_*` env vars, or
   - create `keystore.properties` with `storeFile`, `storePassword`, `keyAlias`, `keyPassword`.

## Commands

- iOS TestFlight: `pnpm fastlane:ios:beta`
- iOS App Store: `pnpm fastlane:ios:release`
- Android Internal testing: `pnpm fastlane:android:beta`
- Android Production: `pnpm fastlane:android:release`

Each lane rebuilds the Svelte app, syncs the Capacitor shell, then produces the native artifact and uploads it.
