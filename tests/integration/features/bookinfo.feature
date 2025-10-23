Feature: Bookinfo deployment and connectivity

  Background:
    Given a k8s model for bookinfo
    And an istio-system model with istio-k8s deployed

  Scenario Outline: Bookinfo can be deployed successfully
    When you deploy the bookinfo stack <mesh_enabled>
    Then all charms are active

    Examples:
      | mesh_enabled        |
      | without service mesh|
      | with service mesh   |

  Scenario Outline: Productpage can reach details
    Given the bookinfo stack is deployed <mesh_enabled>
    When productpage calls the details service
    Then the request succeeds
    And details returns valid book information

    Examples:
      | mesh_enabled        |
      | without service mesh|
      | with service mesh   |

  Scenario Outline: Productpage can reach reviews
    Given the bookinfo stack is deployed <mesh_enabled>
    When productpage calls the reviews service
    Then the request succeeds
    And reviews returns book reviews

    Examples:
      | mesh_enabled        |
      | without service mesh|
      | with service mesh   |

  Scenario Outline: Reviews can reach ratings
    Given the bookinfo stack is deployed <mesh_enabled>
    When reviews calls the ratings service
    Then the request succeeds

    Examples:
      | mesh_enabled        |
      | without service mesh|
      | with service mesh   |
