output "app_name" {
  value = juju_application.ratings.name
}

output "endpoints" {
  value = {
    # Provides
    ratings          = "ratings"
    provide_cmr_mesh = "provide-cmr-mesh"

    # Requires
    service_mesh     = "service-mesh"
    require_cmr_mesh = "require-cmr-mesh"
  }
}
