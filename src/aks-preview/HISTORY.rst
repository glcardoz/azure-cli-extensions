.. :changelog:

Release History
===============

Guidance
++++++++
If there is no rush to release a new version, please just add a description of the modification under the *Pending* section.

To release a new version, please select a new version number (usually plus 1 to last patch version, X.Y.Z -> Major.Minor.Patch, more details in `\doc <https://semver.org/>`_), and then add a new section named as the new version number in this file, the content should include the new modifications and everything from the *Pending* section. Finally, update the `VERSION` variable in `setup.py` with this new version number.

Pending
+++++++

18.0.0b22
+++++++
* Vendor new SDK and bump API version to 2025-06-02-preview.

18.0.0b21
+++++++
* Add command `az aks bastion` to enable connections to managed Kubernetes clusters via Azure Bastion.

18.0.0b20
+++++++
* Fix the bug affecting VMAS to VMS migration in the `az aks update` command using the `--migrate-vmas-to-vms` option.

18.0.0b19
+++++++
* Add support for `ManagedSystem` Agent Pool Mode.
* Add `--localdns-config` to `az aks nodepool add` and to `az aks nodepool update` to support configuring a local DNS profile for agent pools.

18.0.0b18
+++++++
* Add validation error when neither --location or --cluster and --resource-group-name are specified for az extension type list or az extension type version list

18.0.0b17
+++++++
* Remove `__import__('pkg_resources').declare_namespace(__name__)` from `vendored_sdks/__init__.py` to fix the namespace package issue.

18.0.0b16
+++++++
* Vendor new SDK and bump API version to 2025-05-02-preview.

18.0.0b15
+++++++
* Fixed NPE issue for `--acns-transit-encryption-type`.

18.0.0b14
+++++++
* Add preview flag for `az aks namespace`.
* Add `--node-provisioning-default-pools` to the `az aks update` command.
* Add `--node-provisioning-default-pools` to the `az aks create` command.

18.0.0b13
+++++++
* Add option `--enable-http-proxy` to `az aks update`.

18.0.0b12
+++++++
* Add option `--acns-transit-encryption-type <None|WireGuard>` to `az aks create/update`

18.0.0b11
+++++++
* Vendor new SDK and bump API version to 2025-04-02-preview.

18.0.0b10
+++++++
* Wrap the ARG call in the managed namespace list command

18.0.0b9
+++++++
* Add `--max-blocked-nodes` to the `az aks nodepool add/update/upgrade` commands.

18.0.0b8
+++++++
* Populate location of managed namespaces using managed cluster's location

18.0.0b7
+++++++
* Add option `--disable-http-proxy` to `az aks update`.

18.0.0b6
+++++++
* Quality improvements for `az aks extension` and `az aks extension type` command groups

18.0.0b5
+++++++
* Add option `Ubuntu2204` and `Ubuntu2404` to `--os-sku` for `az aks nodepool add` and `az aks nodepool update`.

18.0.0b4
+++++++
* Add managed namespace commands `az aks namespace add/update/show/list/delete/get-credentials`

18.0.0b3
+++++++
* Add basic lb sku migration support `az aks update --load-balancer-sku standard`

18.0.0b2
+++++++
* Vendor new SDK and bump API version to 2025-03-02-preview.

18.0.0b1
+++++++
* [BREAKING CHANGE] Remove `--enable-pod-security-policy` and `--disable-pod-security-policy` as it's deprecated.

17.0.0b4
++++++++
* Reset vm_size and count to None for `az aks update --migrate-vmas-to-vms`

17.0.0b3
++++++++
* Add default value of option `--vm-sizes` for `az aks create` and `az aks nodepool add`.

17.0.0b2
++++++++
* Add option `--migrate-vmas-to-vms` to `az aks update`

17.0.0b1
+++++++
* [BREAKING CHANGE]: `az aks create`: Change default value of option `--node-vm-size` to ""
* [BREAKING CHANGE]: `az aks nodepool add`: Change default value of option `--node-vm-size` to ""

16.0.0b1
+++++++
* [BREAKING CHANGE] Remove flux extension from the list of supported core extensions

15.0.0b2
+++++++
* Add aks extension and aks extension-type command groups
* Remove TrustedAccess commands from aks-preview extension as it is GA and exists in azure-cli for long time.

15.0.0b1
++++++++
* [BREAKING CHANGE] Change `--vm-sizes` for VirtualMachines manual profile to awalys support single SKU size.

14.0.0b7
++++++++
* Add `az aks create/update --enable-retina-flow-logs` and `az aks update --disable-retina-flow-logs` commands.

14.0.0b6
+++++++
* Add option `--acns-advanced-networkpolicies <None|FQDN|L7>` to `az aks create/update`

14.0.0b5
++++++++
* Re-generate the SDK for API version 2025-02-02-preview with @autorest/python@6.32.3 to fix `\#31345 <https://github.com/Azure/azure-cli/issues/31345>`_.

14.0.0b4
++++++++
* Vendor new SDK and bump API version to 2025-02-02-preview.

14.0.0b3
+++++++
* Support `az aks loadbalancer show/list/add/update/delete/rebalance` commands.

14.0.0b2
+++++++
* Update the `disable-egress-gateway` subcommand to fix `--help` output for the `az aks mesh` command.
* Modify behavior for `--nodepool-initialization-taints` to ignore taints with hard effects on node pools with system mode when creating or updating a cluster.

14.0.0b1
+++++++
* Vendor new SDK and bump API version to 2025-01-02-preview.
* [BREAKING CHANGE] Rename `--enable-addon-autoscaling` to `--enable-optimized-addon-scaling` to `az aks create` commands.
* [BREAKING CHANGE] Rename `--enable-addon-autoscaling` to `--enable-optimized-addon-scaling` and `--disable-addon-autoscaling` to `--disable-optimized-addon-scaling` to `az aks update` commands.

13.0.0b9
+++++++
* Vendor new SDK and bump API version to 2024-10-02-preview.
* Add `enable-egress-gateway` and `disable-egress-gateway` subcommands to the `az aks mesh` command.

13.0.0b8
+++++++
* `az aks create/update``: Update recording rule group create logic for managed prometheus addon

13.0.0b7
+++++++
* Add `--max-unavailable` to the `az aks nodepool add/update/upgrade` commands.

13.0.0b6
+++++++
* `az aks create/update`: Update parameter description of `--custom-ca-certificates`.

13.0.0b5
+++++++
* `az aks create/az aks nodepool add`: Emit error message when using `--asg-ids` alone without `--allowed-host-ports`.

13.0.0b4
+++++++
* `az aks nodepool upgrade`: Fix `--node-soak-duration` cannot be specified as 0

13.0.0b3
+++++++
* `az aks create`: Update outbound type selection logic for automatic cluster when customer brings BYO Vnet.

13.0.0b2
+++++++
* `az aks create/update`: Update advanced container networking service (acns) with 2024-09-02-preview API version enablement.
* Vendor new SDK and bump API version to 2024-09-02-preview.

13.0.0b1
+++++++
* [BREAKING CHANGE]: `az aks trustedaccess rolebinding create`: Remove deprecated `-r` and `-s` options.

12.0.0b2
++++++++
* `az aks create/update`: Fix storage pool name validation for Azure Container Storage.

12.0.0b1
+++++++
* [BREAKING CHANGE]: Remove advanced container networking service (acns) enablement preview parameters `--enable-advanced-network-observability`, `--disable-advanced-network-observability`, `--enable-fqdn-policy`, `--disable-fqdn-policy`, and `--advanced-networking-observability-tls-management` from `az aks create/update` command.
* Add advanced container networking service (acns) enablement GA parameters `--disable-acns-observability` and `--disable-acns-security` to `az aks create/update` command.

11.0.0b1
+++++++
* [BREAKING CHANGE]: `az aks create`: Remove AAD-legacy properties `--aad-client-app-id`, `--aad-server-app-id` and `--aad-server-app-secret` when creating cluster.

10.0.0b1
++++++++
* [BREAKING CHANGE]: `az aks create/update`: Remove `--uptime-sla` and `--no-uptime-sla` options.

9.0.0b8
+++++++
* Update VM SKU validations to get values from backend API for Azure Container Storage.

9.0.0b7
+++++++
* Fix bug related to updating the monitoring addon DCR when the non monitoring addon enabled through `az aks enable-addons`.

9.0.0b6
+++++++
* Print warning message when new node pool is created with SSH enabled, suggest to create SSH disabled node pool.

9.0.0b5
+++++++
* Add `--driver-type` to the `az aks nodepool add` command.

9.0.0b4
+++++++
* Set the --node-vm-size to empty string when the cluster sku name is automatic. The node vm size will pick from the candidate toggle based on the logic in automatic vm selection.
* Removed some features preview flag that automatic depends on in the test_aks_commands.py

9.0.0b3
+++++++
* Add `--undrainable-node-behavior` to the `az aks nodepool add/update/upgrade` commands.

9.0.0b2
+++++++
* Add block to supported outbound type
* Vendor new SDK and bump API version to 2024-07-02-preview.

9.0.0b1
+++++++
* [BREAKING CHANGE]: Remove support for `az aks update --ssh-access` command to avoid misleading. To update existing cluster's SSH access, please use `az aks nodepool update --ssh-access` to update node pool's SSH access one by one.
* Remove dependency on `msrestazure.azure_exceptions` and `msrestazure.tools`.

8.0.0b1
+++++++
* [BREAKING CHANGE]: Remove enable/disable node restriction feature, since it is always enabled and not changeable since k8s version 1.24.0
* new supportPlan column on `az aks get-versions -o table`, to tell if the version is supported by KubernetesOfficial or AKSLongTermSupport.

7.0.0b8
+++++++
* Update validations to enable Azure Container Storage to install on a larger set of nodepool skus.

7.0.0b7
+++++++
* [AKS] `az aks create/update`: Support UserAssigned Managed Identity for grafana linking in managed prometheus

7.0.0b6
+++++++
* Add `--advanced-networking-observability-tls-management` to `az aks create/update` command.

7.0.0b5
+++++++
* Add option `--enable-acns`, `--disable-acns` to `az aks create/update`
* Add option `--enable-fqdn-policy`, `--disable-fqdn-policy` to `az aks create/update`
* Add support for default nginx ingress controller config for app routing add-on
* `az aks create/update`: Support in place param updates for managed prom

7.0.0b4
++++++++
* Fix bug related to the --ampls-resource-id option in the `az aks enable-addons` command.
* Vendor new SDK and bump API version to 2024-06-02-preview.

7.0.0b3
++++++++
* Add option `--enable-high-log-scale-mode` to `az aks create --enable-addons monitoring` and `az aks enable-addons -a monitoring`.
* Add option `--ampls-resource-id` to `az aks create --enable-addons monitoring` and `az aks enable-addons -a monitoring`.
* Vendor new SDK and bump API version to 2024-05-02-preview.

7.0.0b2
++++++++
* Update the minimum required cli core version to `2.61.0`.
* Add option `--enable-imds-restriction --disable-imds-restriction` to `az aks create` and `az aks update`.
* Introduce valdations to `az aks create` and `az aks update` while using PremiumV2 disk during enabling Azure Container Storage.
* Delete the Azure Container Storage installation after failure to prevent retries.

7.0.0b1
++++++++
* [BREAKING CHANGE]: Remove support for `az aks get-os-options` command.

6.0.0b1
++++++++
* [BREAKING CHANGE]: Remove support for `az aks mesh` egress gateway commands.
* Add validation to `az aks create` and `az aks update` while modifying the `--ephemeral-disk-volume-type` and `--ephemeral-disk-nvme-perf-tier` values.

5.0.0b4
++++++++
* Add additional unit test cases for mutable fips flags in agentpool update.

5.0.0b3
++++++++
* Add support for mutable fips in agentpool update. (enable/disable flags)

5.0.0b2
++++++++
* Add option `--ephemeral-disk-volume-type` to `az aks create` and `az aks update` for Azure Container Storage operations.
* Add option `--azure-container-storage-perf-tier` to `az aks create` and `az aks update` to define resource tiers for Azure Container Storage performance.
* Vendor new SDK and bump API version to 2024-04-02-preview.

5.0.0b1
++++++++
* [BREAKING CHANGE]: Remove --enable-network-observability and --disable-network-observability from aks create and update commands.
* Update --enable-advanced-network-observability description to note additional costs and add missing flag to create command.
* Change default value of `--vm-set-type` to VirtualMachines when `--vm-sizes` is set.


4.0.0b5
++++++++
* Add warnings to `az aks mesh` commands for out of support asm revision in use.
* Add etag support (--if-match, --if-none-match) to some aks commands for optimistic concurrency control.

4.0.0b4
++++++++
* Add `--vm-sizes` to `az aks create` and `az aks nodepool add`.
* Add `az aks nodepool manual-scale add/update/delete` commands.

4.0.0b3
+++++++
* Leave only one role assignment for automatic sku clusters.
    * "Azure Kubernetes Service RBAC Cluster Admin"

4.0.0b2
+++++++
* Improve Windows OutboundNat test case by removing Windows OSSKU limitation
* `az aks create/update`: add support for new outbound type none
* Add `az operation show` command to show the details of a specific operation.
* Add `az operation show-latest` command to show the details of the latest operation.

4.0.0b1
+++++++
* [BREAKING CHANGE]: `az aks create`: Specifying `--enable-managed-identity` and `--service-principal`/`--client-secret` at the same time will cause a `MutuallyExclusiveArgumentError`
* [BREAKING CHANGE]: `az aks create`: Change the default value of option `--enable-managed-identity` from `True` to `False`
* `az aks create`: When options `--service-principal` and `--client-secret` are not specified at the same time, CLI will backfill the value of `--enable-managed-identity` to `True` to maintain the same behavior as before (that is, create an cluster with managed system assigned identity by default)

3.0.0b13
++++++++
* Set disable local accounts to true when creating an automatic cluster
* Add option `--enable-advanced-network-observability`, `--disable-advanced-network-observability` to `az aks create/update`

3.0.0b12
++++++++
* Create three default role assignments for automatic sku clusters.
    * "Azure Kubernetes Service RBAC Cluster Admin"
    * "Azure Kubernetes Service RBAC Admin"
    * "Azure Kubernetes Service Cluster User Role"

3.0.0b11
++++++++
* Add `--enable-static-egress-gateway` to `az aks create` and `az aks update`.
* Add `--disable-static-egress-gateway` to `az aks update` command.
* Add `--gateway-prefix-size` to `az aks nodepool create` command.
* Add `Gateway` mode to agentpool mode enum.

3.0.0b10
++++++++
* Support to enable azure monitor profile when the sku name is automatic.
* Vendor new SDK and bump API version to 2024-03-02-preview.
* Add option `WindowsAnnual` to `--os-sku` for `az aks nodepool add`.
* Add option `--enable-force-upgrade`, `--disable-force-upgrade` and `--upgrade-override-until` to `az aks upgrade`.

3.0.0b9
+++++++
* Support to enable azure container insight monitoring when the sku name is automatic.
* Add AKSHTTPCustomFeatures=Microsoft.ContainerService/AKS-PrometheusAddonPreview to test_aks_automatic_sku.

3.0.0b8
+++++++
* Ignore invalid ip error for `--api-server-authorized-ip-ranges`.

3.0.0b7
+++++++
* Support `--yes` for `az aks mesh upgrade rollback` and `az aks mesh upgrade complete` commands.
* Correct the property disable_outbound_nat in windows_profile and add UT.
* Minimise the roles needed to introduce for Elastic SAN for enabling Azure Container Storage with elasticSan storagepool type.

3.0.0b6
+++++++
* Add `--enable-azure-monitor-app-monitoring` to the `az aks create` command.
* Add `--enable-azure-monitor-app-monitoring` and `--disable-azure-monitor-app-monitoring` to the `az aks update` command.

3.0.0b5
+++++++
* Add `--bootstrap-artifact-source` and `--bootstrap-container-registry-resource-id` to `az aks update`.

3.0.0b4
+++++++
* Fix the issue that option `--uptime-sla` is ignored in command `az aks create`.
* Fix the issue that option `--uptime-sla` and `--no-uptime-sla` are ignored in command `az aks update`.

3.0.0b3
+++++++
* Add `--nodepool-initialization-taints` to `az aks create` and `az aks update`.
* Add `--bootstrap-artifact-source` and `--bootstrap-container-registry-resource-id` to `az aks create`.

3.0.0b2
+++++++
* Add `--sku` to the `az aks create` command.
* Add `--sku` to the `az aks update` command.
* Support cluster service health probe mode by `--cluster-service-load-balancer-health-probe-mode {Shared, Servicenodeport}`


3.0.0b1
+++++++
* [BREAKING CHANGE] Remove support for nodeSelector for egress gateway for `az aks mesh` command.

2.0.0b8
+++++++
* Add `az aks check-network outbound` command to check outbound network from nodes.
* Update the minimum required cli core version to `2.56.0` (actually since `2.0.0b7`).

2.0.0b7
+++++++
* Support reset default value for loadbalancer profile and natgateway profile
* Vendor new SDK and bump API version to 2024-02-02-preview.

2.0.0b6
+++++++
* Fix the resource allocated after disabling ephemeralDisk storagepool type for option `all` in azure container storage.

2.0.0b5
+++++++
* Add support to enable and disable a single type of storagepool using `--enable-azure-container-storage` and `--disable-azure-container-storage` respectively.
* Add support to define the resource allocation to Azure Container Storage applications based on the type of node pools used and storagepools enabled.

2.0.0b4
+++++++
* Add `--enable-vtpm` to `az aks create`, `az aks nodepool add` and `az aks nodepool update`.
* Add `--disable-vtpm` to the `az aks nodepool update` command.
* Add `--enable-secure-boot` to `az aks create`, `az aks nodepool add` and `az aks nodepool update`.
* Add `--disable-secure-boot` to the `az aks nodepool update` command.

2.0.0b3
+++++++
* Add parameter to set revision `--revision` for the Azure Service Mesh addon while creating AKS cluster.
* Fix for `az aks mesh get-upgrades` command panic response when ASM addon is not enabled.

2.0.0b2
+++++++
* Add `--pod-ip-allocation-mode` to `az aks create` and `az aks nodepool` commands.

2.0.0b1
+++++++
* [BREAKING CHANGE] Replace `guardrails` parameters with `safeguards`.
* Implicitly enable istio when ingress or egress gateway is enabled for Azure Service Mesh.
* Add `az aks nodepool delete-machines` command.
* Update `az aks approuting zone` command to support private dns zones.
* Vendor new SDK and bump API version to 2024-01-02-preview.

1.0.0b6
+++++++
* Vendor new SDK and bump API version to 2023-11-02-preview.
* Add `--ssh-access` to the `az aks create` command.
* Add `--ssh-access` to the `az aks update` command.
* Add `--ssh-access` to the `az aks nodepool add` command.
* Add `--ssh-access` to the `az aks nodepool update` command.
* Implicitly enable istio when ingress or egress gateway is enabled for Azure Service Mesh.
* Add `az aks nodepool delete-machines` command.

1.0.0b5
+++++++
* Add `--enable-ai-toolchain-operator` to `az aks create` and `az aks update`.
* Add `--disable-ai-toolchain-operator` to the `az aks update` command.
* Refactor azure service mesh related code to meet cli style requirements.

1.0.0b4
+++++++
* Fix for `az aks approuting update` command not working when `monitoring` addon is enabled.

1.0.0b3
+++++++
* Change the format for az aks machine commands to separate the ipv4, ipv6 columns
* Deprecate the alias "-r" of parameter --source-resource-id in `az aks trustedaccess rolebinding create`

1.0.0b2
+++++++
* Add --skip-gpu-driver-install option to node pool property in `az aks nodepool add`.

1.0.0b1
+++++++
* Add `--enable-addon-autoscaling` and `--disable-addon-autoscaling` to the `az aks update` command.
* Add `--enable-addon-autoscaling` to the `az aks create` command.
* Add `--ip-families` to the `az aks update` command.

0.5.174
+++++++
* Fix the response format for `az aks mesh get-revisions` and `az aks mesh get-upgrades`.
* Fix for `az aks approuting update` command failing on granting keyvault permissions to managed identity.
* Replace Workload Identity related functions with stable version.

0.5.173
+++++++
* Add warning when stopping a private link cluster.

0.5.172
+++++++
* Fix for regression issue with `az aks create --enable-addon` command for enabling App Routing
* Vendor new SDK and bump API version to 2023-10-02-preview.
* Update the enum for `--os-sku` in command `az aks nodepool update` to only accept the expected Ubuntu and AzureLinux OSSKUs.
* Update description `az aks update` and remove description about outbound ip limit.

0.5.171
+++++++
* Fix the issue that the value passed by option `--os-sku` in command `az aks nodepool update` is not processed.

0.5.170
+++++++
* Add `az aks approuting` and `az aks approuting zone` commands for managing App Routing.
* Add `--os-sku` to the `az aks nodepool update` command.
* Add `--node-provisioning-mode` to the `az aks update` command.
* Add `--node-provisioning-mode` to the `az aks create` command.
* Add Artifact Streaming enablement option to node pool property in `az aks nodepool add` and `az aks nodepool update`.
* fix a bug in --support-plan handling when doing `az aks update`

0.5.169
+++++++
* Add `--network-plugin` to the `az aks update` command.
* Add the KataCcIsolation option to --workload-runtime.
* Update "VirtualMachines" agent pool type as Public Preview feature.
* Add --disable-network-observability to `az aks update` cluster command.
* Add `--node-soak-duration` to the `az aks nodepool add/update/upgrade` commands.
* Add `--drain-timeout` to the `az aks nodepool add/update/upgrade` commands (already in [azure-cli](https://github.com/Azure/azure-cli/pull/27475)).


0.5.168
+++++++
* Add `--enable-image-integrity` to the `az aks update` command.

0.5.167
+++++++
* Vendor new SDK and bump API version to 2023-09-02-preview.
* Fix the default storagepool name value created for Azure Container Storage.
* Ensure the correct nodepool name is picked and labelled by Azure Container Storage while installing with `az aks create`.

0.5.166
+++++++
* Add `--network-policy` to the `az aks update` command.

0.5.165
+++++++
* Rearrange the storagepool SKU related helm values set for Azure Container Storage.

0.5.164
+++++++
* Add option `--enable-azure-container-storage` and supporting options `--storage-pool-name`, `--storage-pool-type`, `--storage-pool-sku`, `--storage-pool-size` for `az aks create` and `az aks update`. `az aks update` also supports `--azure-container-storage-nodepools` option.
* Add option `--disable-azure-container-storage` to `az aks create` and `az aks update`.

0.5.163
+++++++
* Add `get-upgrades` and `get-revisions` to the `az aks mesh` command.
* Add `az aks mesh upgrade` commands to manage upgrades for Azure Service Mesh.

0.5.162
+++++++
* Replace Image Cleaner related functions with stable version.
* Vendor new SDK and bump API version to 2023-08-02-preview.
* Update the operation/method used in following commands as the put/delete operations have been changed to long running operations
    * `az aks trustedaccess rolebinding create`
    * `az aks trustedaccess rolebinding update`
    * `az aks trustedaccess rolebinding delete`

0.5.161
+++++++
* Support `premium` cluster sku tier in `az aks create` and `az aks update` commands
* Add option `--k8s-support-plan` to `az aks create` and `az aks update` commands
* Add `az aks machine list` command to fetch list of machines in an agentpool.
* Add `az aks machine show` command to fetch information about a specific machine in an agentpool.

0.5.160
+++++++
* Custom ips and managed ips can be assigned to aks cluster outbound resources

0.5.159
+++++++
* Revert `az aks copilot` Command

0.5.158
+++++++
* Add `enable-egress-gateway` and `disable-egress-gateway` to the `az aks mesh` command.

0.5.157
+++++++
* Add `--disable-workload-identity` to the `az aks update` command.

0.5.156
+++++++
* Add `az aks copilot` command to start a chat with the Azure Kubernetes Service expert. API keys for OpenAI or Azure are required.

0.5.155
+++++++
* Add `--enable-cost-analysis` and `--disable-cost-analysis` to the `az aks update` command.
* Add `--enable-cost-analysis` to the `az aks create` command.

0.5.154
+++++++
* Vendor new SDK and bump API version to 2023-07-02-preview.
* [Breaking Change] Remove option `--upgrade-settings` from `az aks update` command, use option `--enable-force-upgrade` and `--disable-force-upgrade` instead.
* [Breaking Change] Deprecate option `--dns-zone-resource-id` from `az aks create`, `az aks addon enable`, `az aks addon update` and `az aks enable-addons` commands, use option `--dns-zone-resource-ids` instead.

0.5.153
++++++
* outbound ip, ipprefix and managed ips in loadbalancerProfile should be mutually exclusive

0.5.152
++++++
* move loadbalancer/natgateway util functions to azure-cli and update reference in aks-preview project.
* Update the minimum required cli core version to `2.49.0`.
* Add plugin CA support for `az aks mesh enable` commands for Azure Service Mesh.

0.5.151
+++++++
* Add `--disable-image-integrity` to the `az aks update` command.

0.5.150
+++++++
* Vendor new SDK and bump API version to 2023-06-02-preview.
* Add `--network-dataplane` to the `az aks update` command.
* Support "VirtualMachines" agent pool type to `az aks create --vm-set-type` and `az aks nodepool add --vm-set-type`. This is internal use only, not for public preview.

0.5.149
+++++++
* `az aks addon update`: Fix unexpected error 'Addon "web_application_routing" is not enabled in this cluster' when trying to update the web app routing addon for an managed cluster that already has it enabled.

0.5.148
+++++++
* Add support for option --nodepool-taints to some aks commands
  * aks create
  * aks update

0.5.147
+++++++
* Extend containerinsights --data-collection-settings with new fields "streams" and containerlogv2

0.5.146
+++++++
* Add support for new snapshot command `az aks nodepool snapshot update`

0.5.145
+++++++
* Add support for option --aks-custom-headers to some aks commands
  * aks get-credentials
  * aks nodepool scale
  * aks nodepool update
  * aks enable-addons
  * aks show
  * aks scale

0.5.144
+++++++
* Fix setup network profile with network observability due to incorrect property

0.5.143
+++++++
* Vendor new SDK and bump API version to 2023-05-02-preview.
* Add `--enable-network-observability` flag to `az aks create` and `az aks update`.

0.5.142
+++++++
* Deprecate option names `--enable-azuremonitormetrics` and `--disable-azuremonitormetrics`, use `--enable-azure-monitor-metrics` and `--disable-azure-monitor-metrics` instead, so as to be consistent with the option names in official azure-cli. Fix issue `\#26600 <https://github.com/Azure/azure-cli/issues/26600>`_.

0.5.141
+++++++
* Fix `az aks get-credentials` not using the value set by environment variable `KUBECONFIG`, see issue `\#26444 <https://github.com/Azure/azure-cli-extensions/issues/26444>`_.
* Allow options for specifying guardrails profile arguments

0.5.140
+++++++
* Vendor new SDK and bump API version to 2023-04-02-preview.
* `az aks create` and `az aks enable-addons`: Change the default value of `--enable-msi-auth-for-monitoring` to `true` and add check for airgap clouds for monitoring addon

0.5.139
+++++++
* `az aks create` and `az aks nodepool add`: Add warning message when specifying `--os-sku` to `Mariner` or `CBLMariner`.

0.5.138
+++++++
* Vendor new SDK and bump API version to 2023-03-02-preview.
* fix: don't use current kube_proxy_config on UPDATE
* GA update for Azure Monitor Metrics Addon (managed prometheus metrics) for AKS

0.5.137
+++++++
* Fix role assignment failure caused by the breaking change of default API version bump of the auth SDK

0.5.136
+++++++
* fix: remove uneeded location check for DCR, DCRA in azure monitor metrics addon (aks)
* Refactor: use decorator mode in pod_cidr and network_plugin_mode getters to read from mc only during CREATE

0.5.135
+++++++
* Add `--network-dataplane` flag to `az aks create`.
* Allow updating the pod CIDR and network plugin mode to migrate clusters to Azure CNI Overlay.

0.5.134
+++++++
* Add cluster upgrade settings options `--upgrade-settings`, and `--upgrade-override-until`.

0.5.133
+++++++
* Add `az aks mesh` commands for Azure Service Mesh.
* `az aks create/update`: Replace `--uptime-sla` and `--no-uptime-sla` argument with `--tier` argument.
* Raise a ClientRequestError when creating the same cluster again in command `az aks create`.
* Vendor new SDK and bump API version to 2023-02-02-preview.

0.5.132
+++++++
* Change the short name of option `--source-resource-id` in command `az aks trustedaccess rolebinding create` from `-s` to `-r`.
* Add parameter to enable windows recording rules `--enable-windows-recording-rules` for the Azure Monitor Metrics addon

0.5.131
+++++++
* Allow updating the ssh key value if cluster was created without ssh key

0.5.130
+++++++
* Enable outbound migration from/to udr
* Update description after Azure Keyvault Secrets Provider addon is GA

0.5.129
+++++++
* Vendor new SDK and bump API version to 2023-01-02-preview.
* Mark AAD-legacy properties `--aad-client-app-id`, `--aad-server-app-id` and `--aad-server-app-secret` deprecated

0.5.128
+++++++
* Fix option name `--duration` for command group `az aks maintenanceconfiguration`

0.5.127
+++++++
* Add `--node-os-upgrade-channel <node os upgrade channel>` option for specifying the manner in which the OS on your nodes is updated in `aks create` and `aks update`

0.5.126
+++++++
* Add `--nrg-lockdown-restriction-level <restriction level>` option for chosing the node resource group restriction level in `aks create` and `aks update`
* Raise InvalidArgumentValueError for azure cni + pod_cidr without overlay.

0.5.125
+++++++
* Update the minimum required cli core version to `2.44.0`.
* Support for data collection settings to the AKS Monitoring addon
* Add `--data-collection-settings` option in aks create and aks enable-addons

0.5.124
+++++++
* Update command group `az aks maintenanceconfiguration` to support the creation of dedicated maintenance configurations:
  * *aksManagedAutoUpgradeSchedule* for scheduled cluster auto-upgrade
  * *aksManagedNodeOSUpgradeSchedule* for scheduled node os auto-upgrade

0.5.123
+++++++
* Add the KataMshvVmIsolation option to --workload-runtime.

0.5.122
+++++++
* Vendor new SDK and bump API version to 2022-11-02-preview.
* Remove the error prompt about "no argument specified" when `--enable-workload-identity=False` is specified.

0.5.121
+++++++
* Remove defender related code after GA, reuse the implementation in azure-cli/acs.
* Remove check_raw_parameters in update code path, reuse the implementation in azure-cli/acs.
* Remove oidc issuer related code after GA, reuse the implementation in azure-cli/acs.
* Fix monitoring addon option `--enable-syslog` for `aks addon enable`.
* Remove deprecated option `--node-zones`, use `--zones` instead.
* Remove gpu instance profile related code after GA, reuse the implementation in azure-cli/acs.
* Remove http proxy config related code after GA, reuse the implementation in azure-cli/acs.

0.5.120
+++++++

* Remove file, blob csi driver and snapshot controller related CSI driver code after GA, reuse the implementation in azure-cli/acs.
* Remove Azure Dedicated Host related code after GA, reuse the implementation in azure-cli/acs.
* Remove KMS related code after GA, reuse the implementation in azure-cli/acs.

0.5.119
+++++++

* Add `--custom-ca-trust-certificates` option for custom CA in aks create and aks update
* Update the minimum required cli core version to `2.43.0`.

0.5.118
+++++++

* Support enabling syslog collection in monitoring on AKS clusters with msi auth
* Add `--enable-syslog` option in aks create and aks enable-addons

0.5.117
+++++++

* Add custom transform for custom CA
* Support updating kube-proxy configuration with `az aks update --kube-proxy-config file.json`.

0.5.116
+++++++

* Fix `az aks update` command failing on updating the ssh key value if cluster was created without ssh key, see issue `\#5559 <https://github.com/Azure/azure-cli-extensions/issues/5559>`_.
* Mark "--enable-pod-security-policy" deprecated.
* Deny create request if binding existed for command "trustedaccess rolebinding create".
* Support AAD clusters for "az aks kollect".
* Vendor new SDK and bump API version to 2022-10-02-preview.

0.5.115
+++++++

* Support node public IPTags by `az aks create` and `az aks nodepool add`.

0.5.114
+++++++

* Fix `az aks create` and `az aks nodepool add` commands failing on adding nodepool with managed ApplicationSecurityGroups.

0.5.113
+++++++

* Fix workload identity update error after oidc issure GA in azure-cli.
* Fix `az aks update` command failing on SP-based cluster blocked by validation in AzureMonitorMetrics Addon, see issue `\#5488 <https://github.com/Azure/azure-cli-extensions/issues/5488>`_.
* Fix `az aks update` command failing on changes not related to outbound type conversion, see issue `\#24430 https://github.com/Azure/azure-cli/issues/24430>`_.

0.5.112
+++++++

* Add `--outbound-type` to update managed cluster command.

0.5.111
+++++++

* Support updating SSH public key with `az aks update --ssh-key-value`.

0.5.110
+++++++

* Add `--nodepool-asg-ids` and `--nodepool-allowed-host-ports` flags for enabling NSGControl. Related commands:
  * `az aks create`
  * `az aks nodepool add`
  * `az aks nodepool update`

0.5.109
+++++++

* Add --enable-cilium-dataplane flag for creating a cluster that uses Cilium as the networking dataplane.

0.5.108
+++++++

* Vendor new SDK and bump API version to 2022-09-02-preview.

0.5.107
+++++++

* Add `--disable-windows-outbound-nat` for `az aks nodepool add` to add a Windows agent pool which the Windows OutboundNAT is disabled.

0.5.106
+++++++

* Add support for AzureMonitorMetrics Addon (managed prometheus metrics in public preview) for AKS

0.5.105
+++++++

* Add support to create cluster with kube-proxy configuration via `az aks create --kube-proxy-config file.json`
* Update to use 2022-08-03-preview api version.

0.5.104
+++++++

* Add support to upgrade or update cluster with managed cluster snapshot. Command is
    * `az aks upgrade --cluster-snapshot-id <snapshot-id>`
    * `az aks update --cluster-snapshot-id <snapshot-id>`

0.5.103
+++++++

* Add load-balancer-backend-pool-type to create and update api.

0.5.102
+++++++

* Add --enable-vpa/--disable-vpa to enable/disable vertical pod autoscaler feature.

0.5.101
+++++++

* Fix `az aks draft` command crashed on windows during binary check, see issue `\#5336 <https://github.com/Azure/azure-cli-extensions/issues/5336>`_.
* Vendor new SDK and bump API version to 2022-08-02-preview.

0.5.100
+++++++

* Remove unused import to avoid failure in Python3.6, see issue `\#5303 <https://github.com/Azure/azure-cli-extensions/issues/5303>`_.

0.5.99
++++++

* Fix DRAFT CLI to 0.0.22.
* Fix the URL for Download.

0.5.98
++++++

* Fix auto download issue for Draft CLI.
* Remove host and certificates as draft tools update command no longer uses it.

0.5.97
++++++

* Add support for apiserver vnet integration public cluster.

0.5.96
++++++

* Add support for enabling ImageCleaner with `--enable-image-cleaner` flag.
* Add sub-command `operation-abort` for `az aks` and `az aks nodepool` to support canceling the previous operation.

0.5.95
++++++

* Add `--enable-node-restriction`/`--disable-node-restriction` to enable/disable node restriction feature
* Update the minimum required cli core version to `2.38.0` (actually since `0.5.92`).
* Add new value `Mariner` for option `--os-sku` in `az aks create` and `az aks nodepool add`.

0.5.94
++++++

* [BREAKING CHANGE] Since the service no longer supports updating source resource id for role binding, so remove --source-resource-id of `aks trustedaccess rolebinding update` command.
* Change the acceptable values of the `--roles` option to comma-seperated.
    * az aks trustedaccess rolebinding create
    * az aks trustedaccess rolebinding update
* Upgrade `az aks kollect` command to use Periscope version 0.0.10 supporting enhanced Windows log collection.
* Vendor new SDK and bump API version to 2022-07-02-preview.

0.5.93
++++++

* Fix for "'Namespace' object has no attribute 'nodepool_name' error" in command `az aks nodepool wait`, see issue `\#23468 <https://github.com/Azure/azure-cli/issues/23468>`_.

0.5.92
++++++

* Move Azure KeyVault KMS to GA.
* Support disabling Azure KeyVault KMS.
* Vendor new SDK and bump API version to 2022-06-02-preview.

0.5.91
++++++

* Fix compatibility issue when enabling Microsoft Defender via aks-preview.
    * az aks create
    * az aks update

0.5.90 (NOT RELEASED)
+++++++++++++++++++++

* Skip this version due to conflict.

0.5.89
++++++

* Fix for the az aks addon list command to return enable:true, if virtual-node addon is enabled for the AKS cluster.

0.5.88
++++++

* AKS Monitoring MSI Auth related code imported from Azure CLI to reuse the code between aks-preview and Azure CLI.

0.5.87
++++++

* Fix snapshot not resolved according to the subscriptions field in the `--snapshot-id`` option.

0.5.86
++++++

* Support network plugin mode for enabling Azure CNI Overlay preview feature.

0.5.85
++++++

* Add support for Blob csi driver.

0.5.84 (NOT RELEASED)
+++++++++++++++++++++

* Skip this version due to conflict.

0.5.83
++++++

* Update the minimum required cli core version to `2.37.0`.
* Enable v2 decorator pattern.
* Fix container name inconsistency for private clusters in kollect command.
* Temp fix for properties missing in KMS profile in update scenario.

0.5.82
++++++

* Support Key Vault with private link when enabling Azure KeyVault KMS.

0.5.81
++++++

* Add Trusted Access Role Binding commands
    * az aks trustedaccess rolebinding create
    * az aks trustedaccess rolebinding update
    * az aks trustedaccess rolebinding list
    * az aks trustedaccess rolebinding show
    * az aks trustedaccess rolebinding delete
* Fix: Remove permission prompt when saving config file to symlink with `az aks get-credentials`.

0.5.80
++++++

* Fix the value of option --zones not being transmitted correctly for `az aks nodepool add`, see issue `\#4953 <https://github.com/Azure/azure-cli-extensions/issues/4953>`_.

0.5.79
++++++

* Add support for KEDA workload auto-scaler.
* Fix `az aks addon list`, `az aks addon list-available` and `az aks addon show` commands when dealing with the web application routing addon.
* Vendor new SDK and bump API version to 2022-05-02-preview.

0.5.78
++++++

* Prompt when disabling CSI Drivers.

0.5.77
++++++

* Add support to pass csi `disk-driver-version` for `az aks create` and `az aks update`.

0.5.76
++++++

* Add support for Custom CA Trust in `az aks create`, `az aks nodepool add`, `az aks nodepool update`.

0.5.75
++++++

* Add support for web application routing.
* Refactor: Removed redundant `--disable-workload-identity` flag. User can disable the workload identity feature by using `--enable-workload-identity False`.

0.5.74
++++++

* Add command `aks trustedaccess role list`.

0.5.73
++++++

* Fix import issues with command group `az aks draft`

0.5.72 (NOT RELEASED)
+++++++++++++++++++++

* First public release for `az aks draft`

0.5.71
++++++

* Fix: Updated validators for options --min-count and --max-count to support specifying values greater than 100. Related commands are
    * `az aks create`
    * `az aks update`
    * `az aks nodepool add`
    * `az aks nodepool update`

0.5.70
++++++

* Fix: Don't update storageProfile if not set.

0.5.69
++++++

* Fix: Raise error when user provides invalid value for `--os-sku`.

0.5.68
++++++

* Add option `Windows2019`, `Windows2022` to `--os-sku` for `az aks nodepool add`.

0.5.67
+++++++++++++++++++++

* Update the minimum required cli core version to `2.35.0`.
* Vendor new SDK and bump API version to 2022-04-02-preview.
* Add support for csi drivers extensibility.
* Add support for apiserver vnet integration.

0.5.66
++++++

* Prompt when no arguments are given to update and nodepool update to see if the customer wants to try goal seek to current settings.

0.5.65
++++++

* Add `--ignore-pod-disruption-budget` flag for `az aks nodepool delete` for ignoring PodDisruptionBudget.

0.5.64
++++++

* Add support for updating kubelet identity. Command is
    * `az aks update --assign-kubelet-identity <kubelelt-identity-resource-id>`

0.5.63
++++++

* Add support to create cluster with managed cluster snapshot. Command is
    * `az aks create --cluster-snapshot-id <snapshot-id>`

0.5.62
++++++

* Add support for managing workload identity feature.

0.5.61
++++++

* Vendor new SDK and bump API version to 2022-03-02-preview.
* Add support for `--format` parameter in `az aks get-credentials` command.

0.5.60
++++++

* BugFix: Keep aad profile in PUT request of ManagedCluster. Modified commands are
    * `az aks scale`
    * `az aks upgrade`
    * `az aks enable-addons`
    * `az aks disable-addons`
    * `az aks addon enable`
    * `az aks addon disable`
    * `az aks addon update`

0.5.59
++++++

* Add support for managed cluster snapshot commands and modify current nodepool snapshot commands.
* Breaking Change: `az aks nodepool snapshot` will be the command to manage nodepool snapshot. `az aks snapshot` is used for managed cluster snapshot instead.

  More specifically, for managed cluster snapshot, it will be

    * `az aks snapshot create`
    * `az aks snapshot delete`
    * `az aks snapshot list`
    * `az aks snapshot show`

  For nodepool snapshot, it will be

    * `az aks nodepool snapshot create`
    * `az aks nodepool snapshot delete`
    * `az aks nodepool snapshot list`
    * `az aks nodepool snapshot show`

0.5.58
++++++

* Vendor new SDK and bump API version to 2022-02-02-preview.
* Add support for enabling Azure KeyVault KMS with `--enable-azure-keyvault-kms` flag.

0.5.57
++++++

* Add support for updating HTTP proxy configuration via `az aks update --http-proxy-config file.json`.

0.5.56
++++++

* Add `--message-of-the-day` flag for `az aks create` and `az aks nodepool add` for Linux message of the day.

0.5.55
++++++

* Add option `none` to `--network-plugin` parameter to skip CNI installation during cluster creation.

0.5.54
++++++

* Add --host-group-id to `az aks create` and `az aks nodepool add` commands to support Azure Dedicated Host Group, which requires registering the feature flag "Microsoft.ContainerService/DedicatedHostGroupPreview".
    * `az aks create --host-group-id`
    * `az aks nodepool add --host-group-id`

0.5.53
++++++

* Update the minimum required cli core version to `2.32.0`.
* Vendor new SDK and bump API version to 2022-01-02-preview.
* Add support for cluster creating with Capacity Reservation Group.
    * `az aks create --crg-id`
* Add support for nodepool adding with Capacity Reservation Group.
    * `az aks nodepool add --crg-id`

0.5.52
++++++

* Add yaml template files to package data to fix issue `\#148 <https://github.com/Azure/aks-periscope/issues/148>`_.
* Add support for using empty string to remove existing nodepool label by `az aks update --nodepool-labels` or `az aks nodepool update --labels`.
* Add support for using empty string to remove existing node taints by `az nodepool update --node-taints`.
* Correct the option for time control in `maintenanceconfiguration` series commands to `hourSlot`.
* GA (General Availability) for the snapshot feature.

0.5.51
++++++

* Add currentKubernetesVersion column for `az aks show --output table`.

0.5.50
++++++

* Add support for enabling OIDC issuer with `--enable-oidc-issuer` flag.

0.5.49
++++++

* Vendor new SDK and bump API version to 2021-11-01-preview.
* Update the minimum required cli core version to `2.31.0`.
* Add support for Alias Minor Version.

0.5.48
++++++

* Fix: `aks update` issue with load balancer profile defaults being set when CLI arguments only include outbound IPs or outbound prefixes.

0.5.47
++++++

* Add support for IPv4/IPv6 dual-stack networking AKS clusters. Commands is
    * `az aks create --pod-cidrs --service-cidrs --ip-families --load-balancer-managed-outbound-ipv6-count`.

0.5.46
++++++

* Vendor new SDK and bump API version to 2021-10-01.

0.5.45
++++++

* Update the minimum required cli core version to `2.30.0`.
* Remove the snapshot name trimming in `az aks snapshot create` command.

0.5.44
++++++

* In AKS Monitoring addon, fix DCR resource naming convention from DCR-<workspaceName> to MSCI-<workspaceName> to make consistent naming across.

0.5.43 (NOT RELEASED)
+++++++++++++++++++++

* Enable the new implementation in command `aks create`.

0.5.42
++++++

* Update the minimum required cli core version to `2.27.0`.
* Fix default value behavior for pod identity exception pod labels in upgrade/scale calls.

0.5.41
++++++

* Fix default value behavior for pod identity exception pod labels.

0.5.40
++++++

* Update the minimum required cli core version to `2.23.0`.
* Add support for new snapshot commands.
    * `az aks snapshot create`
    * `az aks snapshot delete`
    * `az aks snapshot list`
    * `az aks snapshot show`
* Add --snapshot-id to creating/upgrading commands.
    * `az aks create --snapshot-id`
    * `az aks nodepool add --snapshot-id`
    * `az aks nodepool upgrade --snapshot-id`

0.5.39
++++++

* Add commands for agentpool start stop feature.

0.5.38
++++++

* Add parameter `--rotation-poll-interval` for Azure Keyvault Secrets Provider Addon.

0.5.37
++++++

* Add Windows gMSA v2 support. Add parameters `--enable-windows-gmsa`, `--gmsa-dns-server` and `--gmsa-root-domain-name`.

0.5.36
++++++

* Vendor new SDK and bump API version to 2021-09-01.

0.5.35
++++++

* Add support for multi-instance GPU configuration (`--gpu_instance_profile`) in `az aks create` and `az aks nodepool add`.

0.5.34
++++++

* Add support for WASM nodepools (`--workload-runtime WasmWasi`) in `az aks create` and `az aks nodepool add`.

0.5.33
++++++

* Add support for new addon commands
    * `az aks addon list`
    * `az aks addon list-available`
    * `az aks addon show`
    * `az aks addon enable`
    * `az aks addon disable`
    * `az aks addon update`
* Refactored code to bring addon specific functionality into a separate file.

0.5.32
++++++

* Update to use 2021-08-01 api-version.

0.5.31
++++++

* Add support for new outbound types: 'managedNATGateway' and 'userAssignedNATGateway'.

0.5.30
++++++

* Add preview support for setting scaleDownMode field on nodepools. Requires registering the feature flag "Microsoft.ContainerService/AKS-ScaleDownModePreview" for setting the value to "Deallocate".

0.5.29
++++++

* Fix update (failed due to "ERROR: (BadRequest) Feature Microsoft.ContainerService/AutoUpgradePreview is not enabled" even when autoupgrade was not specified).
* Add podMaxPids argument for kubelet-config.

0.5.28
++++++

* Vendor new SDK and bump API version to 2021-07-01.

0.5.27
++++++

* GA private cluster public FQDN feature, breaking change to replace create parameter `--enable-public-fqdn` with `--disable-public-fqdn` since now it's enabled by default for private cluster during cluster creation.

0.5.26
++++++

* Correct containerLogMaxSizeMb to containerLogMaxSizeMB in customized kubelet config.

0.5.25
++++++

* Add support for http proxy.

0.5.24
++++++

* * Add "--aks-custom-headers" for "az aks nodepool upgrade".

0.5.23
++++++

* Fix issue that `maintenanceconfiguration add` subcommand cannot work.

0.5.22
++++++

* Fix issue in dcr template.

0.5.21
++++++

* Fix issue when disable monitoring on an AKS cluster would fail in regions where Data Collection Rules are not enabled

0.5.20
++++++

* Support enabling monitoring on AKS clusters with msi auth
* Add `--enable-msi-auth-for-monitoring` option in aks create and aks enable-addons

0.5.19
++++++

* Remove azure-defender from list of available addons to install via `az aks enable-addons` command

0.5.18
++++++

* Fix issue with node config not consuming logging settings

0.5.17
++++++

* Add parameter '--enable-ultra-ssd' to enable UltraSSD on agent node pool

0.5.16
++++++

* Vendor SDK using latest swagger with optional query parameter added
* Support private cluster public fqdn feature

0.5.15
++++++

* Vendor new SDK and bump API version to 2021-05-01.

0.5.14
++++++

* Add os-sku argument for cluster and nodepool creation

0.5.13
++++++

* Add compatible logic for the track 2 migration of resource dependence

0.5.12
++++++

* Add --enable-azure-rbac and --disable-azure-rbac in aks update
* Support disabling local accounts
* Add addon `azure-defender` to list of available addons under `az aks enable-addons` command

0.5.11
++++++

* Add get OS options support
* Fix wrong behavior when enabling pod identity addon for cluster with addon enabled

0.5.10
++++++

* Add `--binding-selector` to AAD pod identity add sub command
* Support using custom kubelet identity
* Support updating Windows password
* Add FIPS support to CLI extension

0.5.9
+++++

* Display result better for `az aks command invoke`, while still honor output option
* Fix the bug that checking the addon profile whether it exists

0.5.8
+++++

* Vendor new SDK and bump API version to 2021-03-01.

0.5.7
+++++

* Add command invoke for run-command feature

0.5.6
+++++

* Fix issue that assigning identity in another subscription will fail

0.5.5
+++++

* Add support for Azure KeyVault Secrets Provider as an AKS addon

0.5.4
+++++

* Add operations of maintenance configuration

0.5.3
+++++

* Add `--enable-pod-identity-with-kubenet` for enabling AAD Pod Identity in Kubenet cluster
* Add `--fqdn-subdomain parameter` to create private cluster with custom private dns zone scenario

0.5.2
+++++

* Add support for node public IP prefix ID '--node-public-ip-prefix-id'

0.5.1
+++++

* Vendor new SDK and bump API version to 2021-02-01.

0.5.0
+++++

* Modify addon confcom behavior to only enable SGX device plugin by default.
* Introducte argument '--enable-sgx-quotehelper'
* Breaking Change: remove argument '--diable-sgx-quotehelper'.

0.4.73
++++++

* Vendor new SDK and bump API version to 2020-12-01.
* Add argument '--enable-encryption-at-host'

0.4.72
+++++++

* Add --no-uptime-sla
* Create MSI clusters by default.

0.4.71
+++++++

* Add support using custom private dns zone resource id for parameter '--private-dns-zone'

0.4.70
+++++++

* Revert to use CLIError to be compatible with azure cli versions < 2.15.0

0.4.69
+++++++

* Add argument 'subnetCIDR' to replace 'subnetPrefix' when using ingress-azure addon.

0.4.68
+++++++

* Add support for AAD Pod Identity resources configuration in Azure CLI.

0.4.67
++++++

* Add support for node configuration when creating cluster or agent pool.
* Support private DNS zone for AKS private cluster.
* Vendor new SDK and bump API version to 2020-11-01.

0.4.66
++++++

* Add support for GitOps as an AKS addon
* Update standard load balancer (SLB) max idle timeout from 120 to 100 minutes

0.4.65
++++++

* Honor addon names defined in Azure CLI
* Add LicenseType support for Windows
* Remove patterns for adminUsername and adminPassword in WindowsProfile

0.4.64
++++++

* Add support for Open Service Mesh as an AKS addon
* Add support to get available upgrade versions for an agent pool in AKS

0.4.63
++++++

* Vendor new SDK and bump API version to 2020-09-01.
* Support Start/Stop cluster feature in preview
* Support ephemeral OS functionality
* Add new properties to the autoscaler profile: max-empty-bulk-delete, skip-nodes-with-local-storage, skip-nodes-with-system-pods, expander, max-total-unready-percentage, ok-total-unready-count and new-pod-scale-up-delay
* Fix case sensitive issue for AKS dashboard addon
* Remove PREVIEW from azure policy addon

0.4.62
++++++

* Add support for enable/disable confcom (sgx) addon.

0.4.61
++++++

* Fix AGIC typo and remove preview label from VN #2141
* Set network profile when using basic load balancer. #2137
* Fix bug that compare float number with 0 #2213

0.4.60
++++++

* Fix regression due to a change in the azure-mgmt-resource APIs in CLI 2.10.0

0.4.59
++++++

* Support bring-your-own VNET scenario for MSI clusters which use user assigned identity in control plane.

0.4.58
++++++

* Added clearer error message for invalid addon names

0.4.57
++++++

* Support "--assign-identity" for specifying an existing user assigned identity for control plane's usage in MSI clusters.

0.4.56
++++++

* Support "--enable-aad" for "az aks update" to update an existing RBAC-enabled non-AAD cluster to the new AKS-managed AAD experience

0.4.55
++++++

* Add "--enable-azure-rbac" for enabling Azure RBAC for Kubernetes authorization

0.4.54
++++++

* Support "--enable-aad" for "az aks update" to update an existing AAD-Integrated cluster to the new AKS-managed AAD experience

0.4.53
++++++

* Add --ppg for "az aks create" and "az aks nodepool add"
* Vendor new SDK and bump API version to 2020-06-01.

0.4.52
++++++

* Add --uptime-sla for az aks update

0.4.51
++++++

* Remove --appgw-shared flag from AGIC addon
* Handle role assignments for AGIC addon post-cluster creation
* Support --yes for "az aks upgrade"
* Revert default VM SKU to Standard_DS2_v2

0.4.50
++++++

* Add "--max-surge" for az aks nodepool add/update/upgrade

0.4.49
++++++

* Fix break in get-versions since container service needs to stay on old api.

0.4.48
++++++

* Fix issues of storage account name for az aks kollect

0.4.47
++++++

* Add "--node-image-only" for "az aks nodepool upgrade" and "az aks upgrade"".

0.4.46
++++++

* Fix issues for az aks kollect on private clusters

0.4.45
++++++

* Add "--aks-custom-headers" for "az aks nodepool add" and "az aks update"

0.4.44
++++++

* Fix issues with monitoring addon enabling with CLI versions 2.4.0+

0.4.43
++++++

* Add support for VMSS node public IP.

0.4.38
++++++

* Add support for AAD V2.

0.4.37
++++++

* Added slb outbound ip fix

0.4.36
++++++

* Added --uptime-sla for paid service

0.4.35
++++++

* Added support for creation time node labels

0.4.34
++++++

* Remove preview flag for private cluster feature.

0.4.33
++++++

* Adding az aks get-credentials --context argument

0.4.32
++++++

* Adding support for user assigned msi for monitoring addon.

0.4.31
++++++

* Fixed a regular agent pool creation bug.

0.4.30
++++++

* Remove "Low" option from --priority
* Add "Spot" option to --priority
* Add float value option "--spot-max-price" for Spot Pool
* Add "--cluster-autoscaler-profile" for configuring autoscaler settings

0.4.29
++++++

* Add option '--nodepool-tags for create cluster'
* Add option '--tags' for add or update node pool

0.4.28
++++++

* Add option '--outbound-type' for create
* Add options '--load-balancer-outbound-ports' and '--load-balancer-idle-timeout' for create and update

0.4.27
++++++

* Fixed aks cluster creation error

0.4.26
++++++

* Update to use 2020-01-01 api-version
* Support cluster creation with server side encryption using customer managed key

0.4.25
++++++

* List credentials for different users via parameter `--user`

0.4.24
++++++

* added custom header support

0.4.23
++++++

* Enable GA support of apiserver authorized IP ranges via parameter `--api-server-authorized-ip-ranges` in `az aks create` and `az aks update`

0.4.21
++++++

* Support cluster certificate rotation operation using `az aks rotate-certs`
* Add support for `az aks kanalyze`

0.4.20
++++++

* Add commands '--zones' and '-z' for availability zones in aks

0.4.19
++++++

* Refactor and remove a custom way of getting subscriptions

0.4.18
++++++

* Update to use 2019-10-01 api-version

0.4.17
++++++

* Add support for public IP per node during node pool creation
* Add support for taints during node pool creation
* Add support for low priority node pool

0.4.16
++++++

* Add support for `az aks kollect`
* Add support for `az aks upgrade --control-plane-only`

0.4.15
++++++

* Set default cluster creation to SLB and VMSS

0.4.14
++++++

* Add support for using managed identity to manage cluster resource group

0.4.13
+++++++

* Rename a few options for ACR integration, which includes
  * Rename `--attach-acr <acr-name-or-resource-id>` in `az aks create` command, which allows for attach the ACR to AKS cluster.
  * Rename `--attach-acr <acr-name-or-resource-id>` and `--detach-acr <acr-name-or-resource-id>` in `az aks update` command, which allows to attach or detach the ACR from AKS cluster.
* Add "--enable-private-cluster" flag for enabling private cluster on creation.

0.4.12
++++++

* Bring back "enable-vmss" flag  for backward compatibility
* Revert "Set default availability type to VMSS" for backward compatibility
* Revert "Set default load balancer SKU to Standard" for backward compatibility

0.4.11
++++++

* Add support for load-balancer-profile
* Set default availability type to VMSS
* Set default load balancer SKU to Standard

0.4.10
++++++

* Add support for `az aks update --disable-acr --acr <name-or-id>`

0.4.9
+++++

* Use https if dashboard container port is using https

0.4.8
+++++

* Add update support for `--enable-acr` together with `--acr <name-or-id>`
* Merge `az aks create --acr-name` into `az aks create --acr <name-or-id>`

0.4.7
+++++

* Add support for `--enable-acr` and `--acr-name`

0.4.4
+++++

* Add support for per node pool auto scaler settings.
* Add `az aks nodepool update` to allow users to change auto scaler settings per node pool.
* Add support for Standard sku load balancer.

0.4.1
+++++

* Add `az aks get-versions -l location` to allow users to see all managed cluster versions.
* Add `az aks get-upgrades` to get all available versions to upgrade.
* Add '(preview)' suffix if kubernetes version is preview when using `get-versions` and `get-upgrades`

0.4.0
+++++

* Add support for Azure policy add-on.

0.3.2
+++++

* Add support of customizing node resource group

0.3.1
+++++

* Add support of pod security policy.

0.3.0
+++++

* Add support of feature `--node-zones`

0.2.3
+++++

* `az aks create/scale --nodepool-name` configures nodepool name, truncated to 12 characters, default - nodepool1
* Don't require --nodepool-name in "az aks scale" if there's only one nodepool

0.2.2
+++++

* Add support of Network Policy when creating new AKS clusters

0.2.1
+++++

* add support of apiserver authorized IP ranges

0.2.0
+++++

* Breaking Change: Set default agentType to VMAS
* opt-in VMSS by --enable-VMSS when creating AKS

0.1.0
+++++

* new feature `enable-cluster-autoscaler`
* default agentType is VMSS