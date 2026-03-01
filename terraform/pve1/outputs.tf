output "claude_code_root_password" {
  value       = random_password.claude_root_password.result
  description = "The randomly generated root password for the Claude Code LXC"
  sensitive   = true
}

output "claude_code_ip_addresses" {
  value       = proxmox_virtual_environment_container.claude_code.ipv4
  description = "The IPv4 addresses assigned to the Claude Code LXC"
}