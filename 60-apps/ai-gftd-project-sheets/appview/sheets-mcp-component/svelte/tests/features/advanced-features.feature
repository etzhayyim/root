Feature: Advanced Spreadsheet Features
  As a power user or AI agent
  I want to use advanced spreadsheet capabilities
  So that I can perform complex data analysis and visualization

  Background:
    Given I have a workbook named "Analysis Workbook"
    And the workbook has a sheet named "Sales Data"

  Scenario: Formatting cells with rich styles
    When I update cell "A1" with value "Total Revenue" and format:
      | bold | textColor | backgroundColor | horizontalAlign |
      | true | #FFFFFF   | #4A90E2         | center          |
    Then cell "A1" should have computed value "Total Revenue"
    And cell "A1" should have bold set to true

  Scenario: Creating and managing charts
    Given I have sales data in range "A1:B10"
    When I create a "bar" chart with title "Sales by Region" for range "A1:B10"
    Then I should see a chart with title "Sales by Region"
    And the chart should be of type "bar"

  Scenario: Using templates for consistency
    When I list available templates in category "Financial"
    And I create a new workbook from template "Budget Planner" named "2026 Budget"
    Then I should have a workbook named "2026 Budget"
    And it should contain the standard budget sheets

  Scenario: Real-time collaboration presence
    When I join the sheet "Sales Data"
    Then I should see other active users in the presence list
    And I should see their cursor positions

  Scenario: Using named ranges for readable formulas
    Given I have a workbook named "Finance Workbook"
    When I create a named range "Revenue" for "Sheet1!B2:B10"
    And I use the formula "=SUM(Revenue)" in cell "C1"
    Then cell "C1" should show the sum of the range "B2:B10"

  Scenario: Applying conditional formatting
    When I create a conditional format for range "A1:A10" with rule "number_greater_than" value "100"
    And the format should have backgroundColor "#FF0000"
    Then cells in range "A1:A10" with value > 100 should be highlighted red

  Scenario: Setting up data validation dropdowns
    When I create a data validation for range "B1:B10" with type "list" values "High,Medium,Low"
    Then cell "B1" should show a dropdown with "High, Medium, Low" options
    And entering "Extreme" into "B1" should show an error message

  Scenario: Creating a pivot table for data analysis
    Given I have a sales data sheet with columns "Region", "Sales", "Month"
    When I create a pivot table from "A1:C100" at "E1"
    And I add "Region" to rows
    And I add "Sales" to values with function "SUM"
    Then I should see summarized sales data by region at "E1"

  Scenario: Collaborative cell commenting
    When I add a comment "Please check this value" to cell "C5"
    Then user "AI Agent" should see the comment at "C5"
    And user "AI Agent" should be able to reply "Confirmed, it looks correct"
    When I resolve the comment thread at "C5"
    Then the thread should be marked as resolved

  Scenario: Using developer metadata for AI context
    When I attach developer metadata "id_type" value "invoice_number" to cell "A1"
    Then AI agents should be able to retrieve "id_type" for cell "A1"
    And the metadata should be hidden from normal users

  Scenario: Protecting critical cell ranges
    When I protect range "A1:Z1" with description "Header row"
    And I restrict editing to "Admin"
    Then user "Guest" should receive an error when trying to edit "A1"

  Scenario: Dynamic expansion with ARRAYFORMULA
    When I enter formula "=ARRAYFORMULA(A1:A3 * 2)" into cell "B1"
    Then cells "B1", "B2", "B3" should be automatically populated with values from "A1:A3" multiplied by 2

  Scenario: Referencing external workbooks with IMPORTRANGE
    Given another workbook "Finance-2025" with ID "wb-123" exists
    And "Finance-2025" has "Revenue" value "5000" at "A1"
    When I enter formula "=IMPORTRANGE(\"wb-123\", \"Sheet1!A1\")" into cell "C1"
    Then cell "C1" should eventually show "5000"

  Scenario: Rich text formatting within a cell
    When I set rich text value "Hello World" to cell "A1" with:
      | text  | bold | textColor |
      | Hello | true | #FF0000   |
      | World | false| #0000FF   |
    Then cell "A1" should show "Hello" in bold red and "World" in blue

  Scenario: Mentioning users in comments
    When I add a comment "Please check this @AI Agent" to cell "D5" mentioning user "AI Agent"
    Then user "AI Agent" should receive a notification
    And the comment at "D5" should highlight the mention "@AI Agent"
