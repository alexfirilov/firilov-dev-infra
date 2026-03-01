variable "node_name" {
    description = "The hostname of the Proxmox PVE node."
    default = "pve"
}

variable "datastore_id" {
  description = "The datastore to deploy the LXC disk to (e.g., local-lvm or local-zfs)"
  default     = "local-lvm"
}

variable "public_key" {
  description = "(Optional) Public SSH key to inject into the LXC for authentication with SSH private key to the LXC."
  default     = ""
}

variable "proxmox_endpoint" {
  type        = string
  description = "The endpoint for the Proxmox API"
}

variable "proxmox_api_token" {
  description = "The API token for Proxmox"
  sensitive   = true
}