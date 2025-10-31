# -------------- # Bookinfo microservice integrations --------------

resource "juju_integration" "productpage_details" {
  model_uuid = var.model_uuid

  application {
    name     = module.productpage.app_name
    endpoint = module.productpage.endpoints.details
  }

  application {
    name     = module.details.app_name
    endpoint = module.details.endpoints.details
  }
}

resource "juju_integration" "productpage_reviews" {
  count      = var.enable_reviews ? 1 : 0
  model_uuid = var.model_uuid

  application {
    name     = module.productpage.app_name
    endpoint = module.productpage.endpoints.reviews
  }

  application {
    name     = module.reviews[0].app_name
    endpoint = module.reviews[0].endpoints.reviews
  }
}

resource "juju_integration" "reviews_ratings" {
  count      = var.enable_reviews ? 1 : 0
  model_uuid = var.model_uuid

  application {
    name     = module.reviews[0].app_name
    endpoint = module.reviews[0].endpoints.ratings
  }

  application {
    name     = module.ratings[0].app_name
    endpoint = module.ratings[0].endpoints.ratings
  }
}

# -------------- # Service Mesh integrations (conditional) --------------

resource "juju_integration" "productpage_service_mesh" {
  count      = var.service_mesh ? 1 : 0
  model_uuid = var.model_uuid

  application {
    name     = module.productpage.app_name
    endpoint = module.productpage.endpoints.service_mesh
  }

  application {
    name     = module.istio_beacon[0].app_name
    endpoint = module.istio_beacon[0].endpoints.service_mesh
  }
}

resource "juju_integration" "details_service_mesh" {
  count      = var.service_mesh ? 1 : 0
  model_uuid = var.model_uuid

  application {
    name     = module.details.app_name
    endpoint = module.details.endpoints.service_mesh
  }

  application {
    name     = module.istio_beacon[0].app_name
    endpoint = module.istio_beacon[0].endpoints.service_mesh
  }
}

resource "juju_integration" "reviews_service_mesh" {
  count      = var.service_mesh && var.enable_reviews ? 1 : 0
  model_uuid = var.model_uuid

  application {
    name     = module.reviews[0].app_name
    endpoint = module.reviews[0].endpoints.service_mesh
  }

  application {
    name     = module.istio_beacon[0].app_name
    endpoint = module.istio_beacon[0].endpoints.service_mesh
  }
}

resource "juju_integration" "ratings_service_mesh" {
  count      = var.service_mesh && var.enable_reviews ? 1 : 0
  model_uuid = var.model_uuid

  application {
    name     = module.ratings[0].app_name
    endpoint = module.ratings[0].endpoints.service_mesh
  }

  application {
    name     = module.istio_beacon[0].app_name
    endpoint = module.istio_beacon[0].endpoints.service_mesh
  }
}
