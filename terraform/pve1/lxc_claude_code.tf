resource "random_password" "claude_root_password" {
  length  = 16
  special = true
  override_special = "!#$%&*()-_=+[]{}<>:?" # Exclude special characters that might cause issues with bash syntax
}

# Download the Ubuntu 24 LXC template if it doesn't exist.
resource "proxmox_virtual_environment_download_file" "ubuntu_24_template" {
  content_type = "vztmpl"
  datastore_id = "local"
  node_name    = var.node_name
  url = "http://download.proxmox.com/images/system/ubuntu-24.04-standard_24.04-2_amd64.tar.zst"
  overwrite_unmanaged = true
  upload_timeout      = 10000
}

resource "proxmox_virtual_environment_container" "claude_code" {
  description   = "LXC running Claude Code for remote automation purposes"
  node_name     = var.node_name
  start_on_boot = true
  unprivileged  = true

  initialization {
    hostname = "claude-code"
    
    ip_config {
      ipv4 {
        address = "dhcp"
      }
    }
    
    user_account {
      password = random_password.claude_root_password.result
      keys     = var.public_key != "" ? [trimspace(var.public_key)] : [] # (optional) Inject public key into LXC - only if variable exists.
    }
  }
  
  network_interface {
    name = "eth0"
  }
  
  operating_system {
    template_file_id = proxmox_virtual_environment_download_file.ubuntu_24_template.id
    type             = "ubuntu"
  }

  disk {
    datastore_id = var.datastore_id
    size         = 20
  }

  cpu {
    cores = 2
  }

  memory {
    dedicated = 2048
  }
}