# Bookinfo Terraform Modules

This directory contains Terraform modules for deploying the Bookinfo application using Juju.

## Available Modules

### Solution Stack

- **[bookinfo](./bookinfo/)** - Complete Bookinfo application stack with all microservices and integrations

### Individual Charm Modules

Individual charm modules are located in each charm's directory:

- **[bookinfo-productpage-k8s](../charms/bookinfo-productpage-k8s/terraform/)** - Productpage service
- **[bookinfo-details-k8s](../charms/bookinfo-details-k8s/terraform/)** - Details service
- **[bookinfo-reviews-k8s](../charms/bookinfo-reviews-k8s/terraform/)** - Reviews service
- **[bookinfo-ratings-k8s](../charms/bookinfo-ratings-k8s/terraform/)** - Ratings service

## Quick Start

Deploy the complete Bookinfo stack:

```hcl
module "bookinfo" {
  source  = "git::https://github.com/adhityaravi/bookinfo-operators//terraform/bookinfo"
  model   = juju_model.k8s.name
  channel = "edge"
}
```

Or deploy individual charms:

```hcl
module "productpage" {
  source  = "git::https://github.com/adhityaravi/bookinfo-operators//charms/bookinfo-productpage-k8s/terraform"
  model   = juju_model.k8s.name
  channel = "edge"
}

module "details" {
  source  = "git::https://github.com/adhityaravi/bookinfo-operators//charms/bookinfo-details-k8s/terraform"
  model   = juju_model.k8s.name
  channel = "edge"
}
```

## Documentation

See individual module READMEs for detailed configuration options and usage examples.
