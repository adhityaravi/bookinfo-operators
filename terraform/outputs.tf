# -------------- # Submodules -------------- #

output "components" {
  value = {
    productpage  = module.productpage
    details      = module.details
    reviews      = var.enable_reviews ? module.reviews[0] : null
    ratings      = var.enable_reviews ? module.ratings[0] : null
    istio_beacon = var.service_mesh ? module.istio_beacon[0] : null
  }
  description = "All Terraform charm modules which make up this bookinfo stack"
}
