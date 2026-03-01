terraform {
  cloud {
    organization = "firilov"
    workspaces {
      name = "homelab"
    }
  }
}