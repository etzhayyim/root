Feature: Homepage
  As a visitor
  I want the yoro pages to be reachable
  So that I can access the messenger

  Scenario: etzhayyim.ai health endpoint is reachable
    When I fetch "https://etzhayyim.ai/health"
    Then the fetch status should be 200

  Scenario: yoro.etzhayyim.com health endpoint is reachable
    When I fetch "https://yoro.etzhayyim.com/health"
    Then the fetch status should be 200

  Scenario: www.etzhayyim.com redirects to yoro.etzhayyim.com
    When I fetch "https://www.etzhayyim.com/" without following redirects
    Then the fetch status should be 301
