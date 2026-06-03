# deai Mobile — Capacitor + Fastlane

App ID: `com.etzhayyim.deai`
Apple Team: `3A5CBTEBFP`
ASC Key: `62BW4Q57AB`

## Prerequisites

```bash
# Ruby / Bundler
gem install bundler

# Node / pnpm
node -v   # >= 20
pnpm -v   # >= 9

# Xcode CLI tools
xcode-select --install
```

## First-Time Setup

### 1. Create the certificates repo

Create a **private** GitHub repo: `com-junkawasaki/deai-certificates`

```bash
cd mobile/ios
bundle install
bundle exec fastlane create_certs   # generates certs → pushes to deai-certificates repo
```

### 2. Initialize Capacitor iOS project

```bash
# From mobile/
pnpm install                   # installs @capacitor/* packages

# Build SvelteKit first
cd ../svelte && pnpm build && cd ../mobile

npx cap add ios                # creates mobile/ios/App/
npx cap sync ios               # copies web assets + syncs plugins
```

### 3. Open in Xcode and verify

```bash
npx cap open ios
```

Check: Bundle ID = `com.etzhayyim.deai`, Signing = Manual, Provisioning Profile = match AppStore com.etzhayyim.deai

## Regular Deploy Flow

```bash
# 1. Build SvelteKit
cd svelte && pnpm build && cd ../mobile

# 2. Sync Capacitor
npx cap sync ios

# 3a. TestFlight (beta)
cd ios && bundle exec fastlane beta

# 3b. App Store (full release)
cd ios && bundle exec fastlane full_release
```

## Individual Lanes

| Lane | Description |
|---|---|
| `sync_certs` | Download existing certs (read-only) |
| `create_certs` | Create / rotate certs |
| `beta` | Build + upload to TestFlight |
| `release` | Build + upload binary + metadata (no review submission) |
| `upload_metadata` | Upload metadata only |
| `upload_screenshots` | Upload screenshots only |
| `submit_for_review` | Submit latest build for review |
| `full_release` | Build + upload everything + submit for review |

## Metadata

Japanese App Store metadata lives in `ios/fastlane/metadata/ja/`:

| File | Content |
|---|---|
| `name.txt` | App name (≤30 chars) |
| `subtitle.txt` | Subtitle (≤30 chars) |
| `description.txt` | Full description (≤4000 chars) |
| `keywords.txt` | Comma-separated keywords (≤100 chars) |
| `privacy_url.txt` | Privacy policy URL |
| `release_notes.txt` | What's new (≤4000 chars) |

## Screenshots

Place device screenshots in `ios/fastlane/screenshots/ja/`:

```
screenshots/ja/
├── iPhone-6.7-01_home.png
├── iPhone-6.7-02_assessment.png
├── iPhone-6.7-03_result.png
├── iPhone-6.7-04_matches.png
├── iPhone-6.7-05_message.png
└── iPad-13-01_home.png
```

Required sizes: iPhone 6.7" (1290×2796), iPad 13" (2064×2752).

## ASC API Key

Key file must be present at:
```
~/.appstoreconnect/private_keys/AuthKey_62BW4Q57AB.p8
```

This is the same key used for `com-junkawasaki/spirit-in-physics`. No new key needed.

## Android

```bash
cd mobile
npx cap add android
npx cap sync android
npx cap open android   # Android Studio
```

Google Play deployment: add `android/` Fastlane setup (supply lane) when ready.
