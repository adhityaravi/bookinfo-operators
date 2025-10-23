terraform {
  required_version = ">= 1.5"
  required_providers {
    juju = {
      source  = "juju/juju"
      version = ">= 0.14.0"
    }
  }
}

module "bookinfo" {
  source = "../../../../terraform"

  model        = var.model
  channel      = var.channel
  service_mesh = var.service_mesh
}
