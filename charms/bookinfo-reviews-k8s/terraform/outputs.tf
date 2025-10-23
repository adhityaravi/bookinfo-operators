output "app_name" {
  value = juju_application.reviews.name
}

output "endpoints" {
  value = {
    # Provides
    reviews          = "reviews"
    provide_cmr_mesh = "provide-cmr-mesh"

    # Requires
    ratings          = "ratings"
    service_mesh     = "service-mesh"
    require_cmr_mesh = "require-cmr-mesh"
  }
}
