Feature: Signal Protocol Device Management
  As a yoro user with E2E encryption
  I want to register and manage Signal Protocol devices
  So that my messages can be end-to-end encrypted

  Scenario: Register a Signal device with key bundle
    Given I register a device with identityKey "IK-test-bdd-001" and signedPreKey "SPK-test-bdd-001"
    Then the response status should be 200
    And the response should contain a deviceId

  Scenario: List registered devices
    Given I register a device with identityKey "IK-list-test" and signedPreKey "SPK-list-test"
    When I list my devices
    Then the response status should be 200
    And the device list should contain at least 1 device

  Scenario: Send an E2E encrypted message
    Given I create a channel named "E2E Encrypted Channel"
    When I send an encrypted message to the created channel with body "plaintext" and encryptedBody "cipher-aes256gcm-test"
    Then the response status should be 200
    And the response should contain a messageId
    And the response should contain a rkey
