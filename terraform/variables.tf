variable "channel" {
  description = "Channel that the applications are deployed from"
  type        = string
}

variable "model_uuid" {
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
