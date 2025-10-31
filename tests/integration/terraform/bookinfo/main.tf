terraform {
  required_version = ">= 1.5"
  required_providers {
    juju = {
      source  = "juju/juju"
      version = "~> 1.0"
    }
  }
}

data "juju_model" "bookinfo_model" {
  name  = var.model
  owner = "admin"
}

module "bookinfo" {
  source = "git::https://github.com/adhityaravi/bookinfo-operators//terraform"

  model_uuid   = data.juju_model.bookinfo_model.uuid
  channel      = var.channel
  service_mesh = var.service_mesh
}
