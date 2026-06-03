Feature: Bluesky-Compatible Social Graph
  As a yoro user
  I want Bluesky-compatible social features
  So that I can interact with posts like on Bluesky

  Scenario: atproto.etzhayyim.com health check
    When I fetch "https://atproto.etzhayyim.com/health"
    Then the fetch status should be 200

  Scenario: Get timeline via Connect gRPC
    When I call GetTimeline on atproto.etzhayyim.com with limit 10
    Then the response status should be 200
    And the response should contain a feed array

  Scenario: List public channels as feed source
    When I call listPublicConvos on atproto.etzhayyim.com with limit 20
    Then the response status should be 200

  Scenario: Search posts
    When I call SearchPosts on atproto.etzhayyim.com with query "test"
    Then the response status should be 200

  Scenario: Get profile by DID
    When I call GetProfile on atproto.etzhayyim.com
    Then the response status should be 200
    And the response should contain a did field

  Scenario: XRPC DescribeServer endpoint
    When I fetch "https://atproto.etzhayyim.com/xrpc/com.atproto.server.describeServer"
    Then the fetch status should be 200

  Scenario: Create channel and send message round-trip
    Given I create a channel named "E2E Bluesky Test" via atproto.etzhayyim.com
    Then the response status should be 200
    And the response should contain a convoId
    When I send a message "Hello from E2E Bluesky test" to the created channel via atproto.etzhayyim.com
    Then the response status should be 200
    And the response should contain a rkey
    When I list envelopes in the created channel via atproto.etzhayyim.com
    Then the response status should be 200

  Scenario: Create post and get thread
    Given I create a channel named "E2E Thread Test" via atproto.etzhayyim.com
    And I send a message "Thread root post" to the created channel via atproto.etzhayyim.com
    And I send a reply "Thread reply 1" to the root message via atproto.etzhayyim.com
    When I get the thread for the root message via atproto.etzhayyim.com
    Then the response status should be 200

  Scenario: React to a message
    Given I create a channel named "E2E React Test" via atproto.etzhayyim.com
    And I send a message "React to this" to the created channel via atproto.etzhayyim.com
    When I react with "like" to the last message via atproto.etzhayyim.com
    Then the response status should be 200

  Scenario: Like endpoint is reachable
    When I like a timeline post via atproto.etzhayyim.com
    Then the response status should be 200 or 401

  Scenario: Repost endpoint is reachable
    When I repost a timeline post via atproto.etzhayyim.com
    Then the response status should be 200 or 401

  Scenario: Reply endpoint is reachable
    When I reply to a timeline post via atproto.etzhayyim.com
    Then the response status should be 200 or 401

  Scenario: Bookmark endpoint is reachable
    When I bookmark a timeline post via atproto.etzhayyim.com
    Then the response status should be 200 or 401

  Scenario: Get notification count
    When I call GetNotificationCount on atproto.etzhayyim.com
    Then the response status should be 200
