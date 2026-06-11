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

### ios sync

```sh
[bundle exec] fastlane ios sync
```

Build native web assets and sync the iOS Capacitor shell

### ios beta

```sh
[bundle exec] fastlane ios beta
```

Build an IPA and upload to TestFlight

### ios release

```sh
[bundle exec] fastlane ios release
```

Build an IPA and upload to App Store Connect

----


## Android

### android sync

```sh
[bundle exec] fastlane android sync
```

Build native web assets and sync the Android Capacitor shell

### android beta

```sh
[bundle exec] fastlane android beta
```

Build an Android App Bundle and upload to Internal testing

### android release

```sh
[bundle exec] fastlane android release
```

Build an Android App Bundle and upload to Production

----

This README.md is auto-generated and will be re-generated every time [_fastlane_](https://fastlane.tools) is run.

More information about _fastlane_ can be found on [fastlane.tools](https://fastlane.tools).

The documentation of _fastlane_ can be found on [docs.fastlane.tools](https://docs.fastlane.tools).
