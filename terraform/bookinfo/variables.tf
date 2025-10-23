# We use constraints to set AntiAffinity in K8s
# https://discourse.charmhub.io/t/pod-priority-and-affinity-in-juju-charms/4091/13?u=jose

# FIXME: Passing an empty constraints value to the Juju Terraform provider currently
# causes the operation to fail due to https://github.com/juju/terraform-provider-juju/issues/344
# Therefore, we set a default value of "arch=amd64" for all applications.

variable "channel" {
  description = "Channel that the applications are deployed from"
  type        = string
}

variable "model" {
  description = "Reference to an existing model resource or data source for the model to deploy to"
  type        = string
}

variable "enable_reviews" {
  description = "Enable the reviews and ratings services"
  type        = bool
  default     = true
}

variable "service_mesh" {
  description = "Enable service mesh integration using istio-beacon"
  type        = bool
  default     = false
}

# -------------- # Application configurations --------------

variable "productpage" {
  type = object({
    app_name           = optional(string, "productpage")
    config             = optional(map(string), {})
    constraints        = optional(string, "arch=amd64")
    revision           = optional(number, null)
    storage_directives = optional(map(string), {})
    units              = optional(number, 1)
  })
  default     = {}
  description = "Application configuration for Productpage. For more details: https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application"
}

variable "details" {
  type = object({
    app_name           = optional(string, "details")
    config             = optional(map(string), {})
    constraints        = optional(string, "arch=amd64")
    revision           = optional(number, null)
    storage_directives = optional(map(string), {})
    units              = optional(number, 1)
  })
  default     = {}
  description = "Application configuration for Details. For more details: https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application"
}

variable "reviews" {
  type = object({
    app_name           = optional(string, "reviews")
    config             = optional(map(string), {})
    constraints        = optional(string, "arch=amd64")
    revision           = optional(number, null)
    storage_directives = optional(map(string), {})
    units              = optional(number, 1)
  })
  default     = {}
  description = "Application configuration for Reviews. For more details: https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application"
}

variable "ratings" {
  type = object({
    app_name           = optional(string, "ratings")
    config             = optional(map(string), {})
    constraints        = optional(string, "arch=amd64")
    revision           = optional(number, null)
    storage_directives = optional(map(string), {})
    units              = optional(number, 1)
  })
  default     = {}
  description = "Application configuration for Ratings. For more details: https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application"
}

variable "istio_beacon" {
  type = object({
    app_name           = optional(string, "istio-beacon")
    channel            = optional(string, "2/edge")
    config             = optional(map(string), {})
    constraints        = optional(string, "arch=amd64")
    revision           = optional(number, null)
    storage_directives = optional(map(string), {})
    units              = optional(number, 1)
  })
  default     = {}
  description = "Application configuration for Istio Beacon. For more details: https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application"
}
