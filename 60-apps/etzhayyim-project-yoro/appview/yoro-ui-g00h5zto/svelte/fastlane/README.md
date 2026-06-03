fastlane documentation
----

# Installation

Make sure you have the latest version of the Xcode command line tools installed:

```sh
xcode-select --install
```

For _fastlane_ installation instructions, see [Installing _fastlane_](https://docs.fastlane.tools/#installing-fastlane)

# Available Actions

## iOS

### ios create_app

```sh
[bundle exec] fastlane ios create_app
```

Create App ID and App Store Connect entry

### ios certs

```sh
[bundle exec] fastlane ios certs
```

Sync certificates and provisioning profiles

### ios build

```sh
[bundle exec] fastlane ios build
```

Build iOS app from Capacitor project

### ios beta

```sh
[bundle exec] fastlane ios beta
```

Build and upload to TestFlight

### ios release

```sh
[bundle exec] fastlane ios release
```

Build and submit to App Store review

### ios submit

```sh
[bundle exec] fastlane ios submit
```

Submit latest build for App Store review (no rebuild, metadata must be set in ASC)

### ios metadata

```sh
[bundle exec] fastlane ios metadata
```

Update App Store metadata only

### ios metadata_no_name

```sh
[bundle exec] fastlane ios metadata_no_name
```

Update metadata without name (when name is taken)

----


## Android

### android build

```sh
[bundle exec] fastlane android build
```

Build Android app (APK)

### android build_aab

```sh
[bundle exec] fastlane android build_aab
```

Build Android app (AAB)

### android device

```sh
[bundle exec] fastlane android device
```

Build and install on connected device

### android beta

```sh
[bundle exec] fastlane android beta
```

Build AAB and upload to Play Console (internal track)

### android release

```sh
[bundle exec] fastlane android release
```

Build AAB and upload to Play Console (production)

### android promote

```sh
[bundle exec] fastlane android promote
```

Promote internal track to production

----

This README.md is auto-generated and will be re-generated every time [_fastlane_](https://fastlane.tools) is run.

More information about _fastlane_ can be found on [fastlane.tools](https://fastlane.tools).

The documentation of _fastlane_ can be found on [docs.fastlane.tools](https://docs.fastlane.tools).
