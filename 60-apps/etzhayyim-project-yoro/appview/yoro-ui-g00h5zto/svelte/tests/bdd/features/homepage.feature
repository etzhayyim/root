Feature: Homepage
  As a visitor
  I want the yoro pages to be reachable
  So that I can access the messenger

  Scenario: gftd.ai health endpoint is reachable
    When I fetch "https://gftd.ai/health"
    Then the fetch status should be 200

  Scenario: yoro.gftd.ai health endpoint is reachable
    When I fetch "https://yoro.gftd.ai/health"
    Then the fetch status should be 200

  Scenario: www.gftd.ai redirects to yoro.gftd.ai
    When I fetch "https://www.gftd.ai/" without following redirects
    Then the fetch status should be 301
