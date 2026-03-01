# Proxmox Bootstrapping (PVE1)

This directory contains Ansible automation to create an API key on the first Proxmox node (PVE1) in the homelab environment, to be used by Terraform for provisioning Proxmox resources using the pbg/proxmox provider.

The playbook connects to the Proxmox host, creates a dedicated `terraform@pve` user, assigns it the Administrator role, generates an API token, and outputs the credentials into a `.auto.tfvars` file for Terraform to consume automatically.

## Prerequisites

1. **Ansible**: Ensure Ansible is installed on your local machine.
2. **Create a vars.yaml file**:  Use the existant `vars.yaml.example` file, copy it to just `vars.yaml`, and change the configs to match your environment.
3. **Ensure you have a way to authenticate to the Proxmox node**: This can be done via either an SSH key (recommended), or a username and password - see bottom section for dedicated command to authenticated with password.


## Files Overview

* `inventory.yaml`: Defines the Proxmox host using variables (`vars.yaml`)

* `vars.yaml.example`: Contains the specific IP address (`pve_host_ip`) and SSH user (`pve_ssh_user`) variable for the PVE node - copy this file as an example to `vars.yaml` and change the example configuration to match your environment.

* `bootstrap.yaml`: The main playbook that configures Proxmox and extracts the API token.

## Usage

### If you authenticate to the PVE node via an SSH key:

Run the following command directly from this directory:

```bash
ansible-playbook -i inventory.yaml bootstrap.yaml -e @vars.yaml
```

### If you use password authentication:

Run the following command directly from this directory:
```bash
ansible-playbook -i inventory.yaml bootstrap.yaml -e @vars.yaml -k
```

The -k flag tells Ansible to ask you for the password during the run.

After successfully running the Ansible playbook - the API token will be saved in `../../terraform/pve1/terraform.auto.tfvars`