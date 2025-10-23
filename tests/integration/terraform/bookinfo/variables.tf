variable "model" {
  description = "The Juju model to deploy to"
  type        = string
}

variable "channel" {
  description = "Channel to deploy the charms from"
  type        = string
  default     = "latest/stable"
}

variable "service_mesh" {
  description = "Enable service mesh integration"
  type        = bool
  default     = false
}
