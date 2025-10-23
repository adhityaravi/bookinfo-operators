# Bookinfo Application Stack Terraform Module

This is a Terraform module for deploying the complete Bookinfo application stack using the [Terraform juju provider](https://github.com/juju/terraform-provider-juju/). For more information, refer to the provider [documentation](https://registry.terraform.io/providers/juju/juju/latest/docs).

The Bookinfo application is a sample microservices application composed of four separate services:
- **productpage**: The main web page that displays book information
- **details**: Contains book details information
- **reviews**: Contains book reviews (with configurable versions v1, v2, v3)
- **ratings**: Contains book rating information

## Usage

Create `main.tf`:

```hcl
module "bookinfo" {
  source  = "git::https://github.com/adhityaravi/bookinfo-operators//terraform/bookinfo"
  model   = juju_model.k8s.name
  channel = "edge"
}
```

With custom configuration:

```hcl
module "bookinfo" {
  source  = "git::https://github.com/adhityaravi/bookinfo-operators//terraform/bookinfo"
  model   = juju_model.k8s.name
  channel = "edge"

  productpage = {
    units = 2
    config = {
      log-level = "debug"
    }
  }

  reviews = {
    config = {
      version = "v2"  # Use black star ratings
    }
  }
}
```

Apply the configuration:

```sh
$ terraform apply
```

With service mesh enabled:

```hcl
module "bookinfo" {
  source  = "git::https://github.com/adhityaravi/bookinfo-operators//terraform/bookinfo"
  model   = juju_model.k8s.name
  channel = "edge"

  service_mesh = true  # Enable istio-beacon and service mesh integrations
}
```

## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.5 |
| <a name="requirement_juju"></a> [juju](#requirement\_juju) | >= 0.14.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_juju"></a> [juju](#provider\_juju) | >= 0.14.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_details"></a> [details](#module\_details) | git::https://github.com/adhityaravi/bookinfo-operators//charms/bookinfo-details-k8s/terraform | n/a |
| <a name="module_productpage"></a> [productpage](#module\_productpage) | git::https://github.com/adhityaravi/bookinfo-operators//charms/bookinfo-productpage-k8s/terraform | n/a |
| <a name="module_ratings"></a> [ratings](#module\_ratings) | git::https://github.com/adhityaravi/bookinfo-operators//charms/bookinfo-ratings-k8s/terraform | n/a |
| <a name="module_reviews"></a> [reviews](#module\_reviews) | git::https://github.com/adhityaravi/bookinfo-operators//charms/bookinfo-reviews-k8s/terraform | n/a |

## Resources

| Name | Type |
|------|------|
| [juju_integration.productpage_details](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.productpage_reviews](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.reviews_ratings](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_channel"></a> [channel](#input\_channel) | Channel that the applications are deployed from | `string` | n/a | yes |
| <a name="input_details"></a> [details](#input\_details) | Application configuration for Details. For more details: https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application | <pre>object({<br/>    app_name           = optional(string, "details")<br/>    config             = optional(map(string), {})<br/>    constraints        = optional(string, "arch=amd64")<br/>    revision           = optional(number, null)<br/>    storage_directives = optional(map(string), {})<br/>    units              = optional(number, 1)<br/>  })</pre> | `{}` | no |
| <a name="input_model"></a> [model](#input\_model) | Reference to an existing model resource or data source for the model to deploy to | `string` | n/a | yes |
| <a name="input_productpage"></a> [productpage](#input\_productpage) | Application configuration for Productpage. For more details: https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application | <pre>object({<br/>    app_name           = optional(string, "productpage")<br/>    config             = optional(map(string), {})<br/>    constraints        = optional(string, "arch=amd64")<br/>    revision           = optional(number, null)<br/>    storage_directives = optional(map(string), {})<br/>    units              = optional(number, 1)<br/>  })</pre> | `{}` | no |
| <a name="input_ratings"></a> [ratings](#input\_ratings) | Application configuration for Ratings. For more details: https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application | <pre>object({<br/>    app_name           = optional(string, "ratings")<br/>    config             = optional(map(string), {})<br/>    constraints        = optional(string, "arch=amd64")<br/>    revision           = optional(number, null)<br/>    storage_directives = optional(map(string), {})<br/>    units              = optional(number, 1)<br/>  })</pre> | `{}` | no |
| <a name="input_reviews"></a> [reviews](#input\_reviews) | Application configuration for Reviews. For more details: https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application | <pre>object({<br/>    app_name           = optional(string, "reviews")<br/>    config             = optional(map(string), {})<br/>    constraints        = optional(string, "arch=amd64")<br/>    revision           = optional(number, null)<br/>    storage_directives = optional(map(string), {})<br/>    units              = optional(number, 1)<br/>  })</pre> | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_components"></a> [components](#output\_components) | All Terraform charm modules which make up this bookinfo stack |
