module "istio_beacon" {
  count              = var.service_mesh ? 1 : 0
  source             = "git::https://github.com/canonical/istio-beacon-k8s-operator//terraform"
  app_name           = var.istio_beacon.app_name
  channel            = var.istio_beacon.channel
  config             = var.istio_beacon.config
  constraints        = var.istio_beacon.constraints
  model              = var.model
  revision           = var.istio_beacon.revision
  storage_directives = var.istio_beacon.storage_directives
  units              = var.istio_beacon.units
}

module "productpage" {
  source             = "git::https://github.com/adhityaravi/bookinfo-operators//charms/bookinfo-productpage-k8s/terraform"
  app_name           = var.productpage.app_name
  channel            = var.channel
  config             = var.productpage.config
  constraints        = var.productpage.constraints
  model              = var.model
  revision           = var.productpage.revision
  storage_directives = var.productpage.storage_directives
  units              = var.productpage.units
}

module "details" {
  source             = "git::https://github.com/adhityaravi/bookinfo-operators//charms/bookinfo-details-k8s/terraform"
  app_name           = var.details.app_name
  channel            = var.channel
  config             = var.details.config
  constraints        = var.details.constraints
  model              = var.model
  revision           = var.details.revision
  storage_directives = var.details.storage_directives
  units              = var.details.units
}

module "reviews" {
  count              = var.enable_reviews ? 1 : 0
  source             = "git::https://github.com/adhityaravi/bookinfo-operators//charms/bookinfo-reviews-k8s/terraform"
  app_name           = var.reviews.app_name
  channel            = var.channel
  config             = var.reviews.config
  constraints        = var.reviews.constraints
  model              = var.model
  revision           = var.reviews.revision
  storage_directives = var.reviews.storage_directives
  units              = var.reviews.units
}

module "ratings" {
  count              = var.enable_reviews ? 1 : 0
  source             = "git::https://github.com/adhityaravi/bookinfo-operators//charms/bookinfo-ratings-k8s/terraform"
  app_name           = var.ratings.app_name
  channel            = var.channel
  config             = var.ratings.config
  constraints        = var.ratings.constraints
  model              = var.model
  revision           = var.ratings.revision
  storage_directives = var.ratings.storage_directives
  units              = var.ratings.units
}
