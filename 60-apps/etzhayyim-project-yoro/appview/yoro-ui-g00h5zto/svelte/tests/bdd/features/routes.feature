Feature: Bluesky-Compatible Route Coverage
  As a visitor
  I want all Bluesky-compatible routes to be reachable
  So that the platform provides full AT Protocol social functionality

  Scenario: Home feed is accessible
    When I fetch "https://yoro.etzhayyim.com/"
    Then the fetch status should be 200

  Scenario: Search page is accessible
    When I fetch "https://yoro.etzhayyim.com/search"
    Then the fetch status should be 200

  Scenario: Notifications page is accessible
    When I fetch "https://yoro.etzhayyim.com/notifications"
    Then the fetch status should be 200

  Scenario: My Feeds page is accessible
    When I fetch "https://yoro.etzhayyim.com/feeds"
    Then the fetch status should be 200

  Scenario: My Lists page is accessible
    When I fetch "https://yoro.etzhayyim.com/lists"
    Then the fetch status should be 200

  Scenario: Messages page is accessible
    When I fetch "https://yoro.etzhayyim.com/messages"
    Then the fetch status should be 200

  Scenario: Profile page is accessible
    When I fetch "https://yoro.etzhayyim.com/profile/testuser"
    Then the fetch status should be 200

  Scenario: Post thread page is accessible
    When I fetch "https://yoro.etzhayyim.com/profile/testuser/post/abc123"
    Then the fetch status should be 200

  Scenario: Privacy page is accessible
    When I fetch "https://yoro.etzhayyim.com/privacy"
    Then the fetch status should be 200

  Scenario: Terms page is accessible
    When I fetch "https://yoro.etzhayyim.com/terms"
    Then the fetch status should be 200

  Scenario: Welcome page is accessible
    When I fetch "https://yoro.etzhayyim.com/welcome"
    Then the fetch status should be 200

  Scenario: Hashtag feed is accessible
    When I fetch "https://yoro.etzhayyim.com/hashtag/test"
    Then the fetch status should be 200

  Scenario: Settings page is accessible
    When I fetch "https://yoro.etzhayyim.com/settings"
    Then the fetch status should be 200

  Scenario: Moderation page is accessible
    When I fetch "https://yoro.etzhayyim.com/moderation"
    Then the fetch status should be 200

  Scenario: Sitemap returns XML
    When I fetch "https://yoro.etzhayyim.com/sitemap.xml"
    Then the fetch status should be 200
