# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines, disable=broad-except
import datetime
import json
import os
import os.path
import platform
import ssl
import sys
import threading
import time
import webbrowser

from azext_aks_preview._client_factory import (
    CUSTOM_MGMT_AKS_PREVIEW,
    cf_agent_pools,
    get_compute_client,
)
from azext_aks_preview._consts import (
    ADDONS,
    ADDONS_DESCRIPTIONS,
    CONST_ACC_SGX_QUOTE_HELPER_ENABLED,
    CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME,
    CONST_CONFCOM_ADDON_NAME,
    CONST_INGRESS_APPGW_ADDON_NAME,
    CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID,
    CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME,
    CONST_INGRESS_APPGW_SUBNET_CIDR,
    CONST_INGRESS_APPGW_SUBNET_ID,
    CONST_INGRESS_APPGW_WATCH_NAMESPACE,
    CONST_KUBE_DASHBOARD_ADDON_NAME,
    CONST_MONITORING_ADDON_NAME,
    CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID,
    CONST_MONITORING_USING_AAD_MSI_AUTH,
    CONST_NODEPOOL_MODE_USER,
    CONST_OPEN_SERVICE_MESH_ADDON_NAME,
    CONST_ROTATION_POLL_INTERVAL,
    CONST_SCALE_DOWN_MODE_DELETE,
    CONST_SCALE_SET_PRIORITY_REGULAR,
    CONST_SECRET_ROTATION_ENABLED,
    CONST_SPOT_EVICTION_POLICY_DELETE,
    CONST_VIRTUAL_NODE_ADDON_NAME,
    CONST_VIRTUAL_NODE_SUBNET_NAME,
    CONST_AZURE_SERVICE_MESH_MODE_ISTIO,
    CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_START,
    CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_COMPLETE,
    CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_ROLLBACK,
    CONST_SSH_ACCESS_LOCALUSER,
    CONST_NODE_PROVISIONING_STATE_SUCCEEDED,
    CONST_DEFAULT_NODE_OS_TYPE,
    CONST_VIRTUAL_MACHINE_SCALE_SETS,
    CONST_VIRTUAL_MACHINES,
    CONST_AVAILABILITY_SET,
    CONST_MIN_NODE_IMAGE_VERSION,
    CONST_ARTIFACT_SOURCE_DIRECT,
    CONST_K8S_EXTENSION_CUSTOM_MOD_NAME,
    CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME,
)
from azext_aks_preview._helpers import (
    check_is_private_link_cluster,
    get_cluster_snapshot_by_snapshot_id,
    get_k8s_extension_module,
    get_nodepool_snapshot_by_snapshot_id,
    print_or_merge_credentials,
    process_message_for_run_command,
    check_is_monitoring_addon_enabled,
    get_all_extension_types_in_allow_list,
    get_all_extensions_in_allow_list,
    raise_validation_error_if_extension_type_not_in_allow_list,
    get_extension_in_allow_list,
)
from azext_aks_preview._podidentity import (
    _ensure_managed_identity_operator_permission,
    _ensure_pod_identity_addon_is_enabled,
    _fill_defaults_for_pod_identity_profile,
    _update_addon_pod_identity,
)
from azext_aks_preview._resourcegroup import get_rg_location
from azext_aks_preview.addonconfiguration import (
    add_ingress_appgw_addon_role_assignment,
    add_virtual_node_role_assignment,
    enable_addons,
)
from azext_aks_preview.aks_diagnostics import aks_kanalyze_cmd, aks_kollect_cmd
from azext_aks_preview.aks_draft.commands import (
    aks_draft_cmd_create,
    aks_draft_cmd_generate_workflow,
    aks_draft_cmd_setup_gh,
    aks_draft_cmd_up,
    aks_draft_cmd_update,
)
from azext_aks_preview.bastion.bastion import (
    aks_bastion_parse_bastion_resource,
    aks_bastion_get_local_port,
    aks_bastion_extension,
    aks_bastion_set_kubeconfig,
    aks_bastion_runner,
    aks_batsion_clean_up
)
from azext_aks_preview.maintenanceconfiguration import (
    aks_maintenanceconfiguration_update_internal,
)
from azext_aks_preview.managednamespace import (
    aks_managed_namespace_add,
    aks_managed_namespace_update,
)
from azure.cli.command_modules.acs._helpers import (
    get_user_assigned_identity_by_resource_id
)
from azure.cli.command_modules.acs._validators import (
    extract_comma_separated_string,
)
from azure.cli.command_modules.acs.addonconfiguration import (
    ensure_container_insights_for_monitoring,
    ensure_default_log_analytics_workspace_for_monitoring,
    sanitize_loganalytics_ws_resource_id,
)
from azure.cli.core.api import get_config_dir
from azure.cli.core.azclierror import (
    ArgumentUsageError,
    ClientRequestError,
    InvalidArgumentValueError,
    MutuallyExclusiveArgumentError,
    RequiredArgumentMissingError,
    ValidationError,
)
from azure.cli.core.commands import LongRunningOperation
from azure.cli.core.commands.client_factory import (
    get_subscription_id,
    get_mgmt_service_client,
)
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import (
    in_cloud_console,
    sdk_no_wait,
    shell_safe_json_parse,
)
from azure.core.exceptions import (
    ResourceNotFoundError,
    HttpResponseError,
)
from dateutil.parser import parse
from knack.log import get_logger
from knack.prompting import prompt_y_n
from knack.util import CLIError
from six.moves.urllib.error import URLError
from six.moves.urllib.request import urlopen

logger = get_logger(__name__)


def wait_then_open(url):
    """
    Waits for a bit then opens a URL.  Useful for waiting for a proxy to come up, and then open the URL.
    """
    for _ in range(1, 10):
        try:
            with urlopen(url, context=_ssl_context()):
                break
        except URLError:
            time.sleep(1)
    webbrowser.open_new_tab(url)


def wait_then_open_async(url):
    """
    Spawns a thread that waits for a bit then opens a URL.
    """
    t = threading.Thread(target=wait_then_open, args=url)
    t.daemon = True
    t.start()


def _ssl_context():
    if sys.version_info < (3, 4) or (in_cloud_console() and platform.system() == 'Windows'):
        try:
            # added in python 2.7.13 and 3.6
            return ssl.SSLContext(ssl.PROTOCOL_TLS)
        except AttributeError:
            return ssl.SSLContext(ssl.PROTOCOL_TLSv1)

    return ssl.create_default_context()


# pylint: disable=too-many-locals
def store_acs_service_principal(subscription_id, client_secret, service_principal,
                                file_name='acsServicePrincipal.json'):
    obj = {}
    if client_secret:
        obj['client_secret'] = client_secret
    if service_principal:
        obj['service_principal'] = service_principal

    config_path = os.path.join(get_config_dir(), file_name)
    full_config = load_service_principals(config_path=config_path)
    if not full_config:
        full_config = {}
    full_config[subscription_id] = obj

    with os.fdopen(os.open(config_path, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600),
                   'w+') as spFile:
        json.dump(full_config, spFile)


def load_acs_service_principal(subscription_id, file_name='acsServicePrincipal.json'):
    config_path = os.path.join(get_config_dir(), file_name)
    config = load_service_principals(config_path)
    if not config:
        return None
    return config.get(subscription_id)


def load_service_principals(config_path):
    if not os.path.exists(config_path):
        return None
    fd = os.open(config_path, os.O_RDONLY)
    try:
        with os.fdopen(fd) as f:
            return shell_safe_json_parse(f.read())
    except:  # pylint: disable=bare-except
        return None


def aks_browse(
    cmd,
    client,
    resource_group_name,
    name,
    disable_browser=False,
    listen_address="127.0.0.1",
    listen_port="8001",
):
    from azure.cli.command_modules.acs.custom import _aks_browse

    return _aks_browse(
        cmd,
        client,
        resource_group_name,
        name,
        disable_browser,
        listen_address,
        listen_port,
        CUSTOM_MGMT_AKS_PREVIEW,
    )


# pylint: disable=unused-argument
def aks_namespace_add(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    name,
    cpu_request,
    cpu_limit,
    memory_request,
    memory_limit,
    tags=None,
    labels=None,
    annotations=None,
    aks_custom_headers=None,
    ingress_policy=None,
    egress_policy=None,
    adoption_policy=None,
    delete_policy=None,
    no_wait=False,
):
    existedNamespace = None
    try:
        existedNamespace = client.get(resource_group_name, cluster_name, name)
    except ResourceNotFoundError:
        pass

    if existedNamespace:
        raise ClientRequestError(
            f"Namespace '{name}' already exists. Please use 'az aks namespace update' to update it."
        )

    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()
    headers = get_aks_custom_headers(aks_custom_headers)
    return aks_managed_namespace_add(cmd, client, raw_parameters, headers, no_wait)


# pylint: disable=unused-argument
def aks_namespace_update(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    name,
    cpu_request=None,
    cpu_limit=None,
    memory_request=None,
    memory_limit=None,
    tags=None,
    labels=None,
    annotations=None,
    aks_custom_headers=None,
    ingress_policy=None,
    egress_policy=None,
    adoption_policy=None,
    delete_policy=None,
    no_wait=False,
):
    try:
        existedNamespace = client.get(resource_group_name, cluster_name, name)
    except ResourceNotFoundError:
        raise ClientRequestError(
            f"Namespace '{name}' doesn't exist."
            "Please use 'aks namespace list' to get current list of managed namespaces"
        )

    if existedNamespace:
        # DO NOT MOVE: get all the original parameters and save them as a dictionary
        raw_parameters = locals()
        headers = get_aks_custom_headers(aks_custom_headers)
        return aks_managed_namespace_update(cmd, client, raw_parameters, headers, existedNamespace, no_wait)


def aks_namespace_show(
    cmd,  # pylint: disable=unused-argument
    client,
    resource_group_name,
    cluster_name,
    name
):
    logger.warning('resource_group_name: %s, cluster_name: %s, managed_namespace_name: %s ',
                   resource_group_name, cluster_name, name)
    return client.get(resource_group_name, cluster_name, name)


def aks_namespace_list(
    cmd,  # pylint: disable=unused-argument
    client,
    resource_group_name=None,
    cluster_name=None,
):
    if resource_group_name and cluster_name:
        return client.list_by_managed_cluster(resource_group_name, cluster_name)
    rcf = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)
    full_resource_type = "Microsoft.ContainerService/managedClusters/managedNamespaces"
    filters = [f"resourceType eq '{full_resource_type}'"]
    if resource_group_name:
        filters.append(f"resourceGroup eq '{resource_group_name}'")
    odata_filter = " and ".join(filters)
    expand = "createdTime,changedTime,provisioningState"
    resources = rcf.resources.list(filter=odata_filter, expand=expand)
    return list(resources)


def aks_namespace_delete(
    cmd,  # pylint: disable=unused-argument
    client,
    resource_group_name,
    cluster_name,
    name,
    no_wait=False,
):
    namespace_exists = False
    namespace_instances = client.list_by_managed_cluster(resource_group_name, cluster_name)
    for instance in namespace_instances:
        if instance.name.lower() == name.lower():
            namespace_exists = True
            break

    if not namespace_exists:
        raise ClientRequestError(
            f"Managed namespace {name} doesn't exist, "
            "use 'aks namespace list' to get current managed namespace list"
        )

    return sdk_no_wait(
        no_wait,
        client.begin_delete,
        resource_group_name,
        cluster_name,
        name,
    )


def aks_namespace_get_credentials(
    cmd,  # pylint: disable=unused-argument
    client,
    resource_group_name,
    cluster_name,
    name,
    path=os.path.join(os.path.expanduser("~"), ".kube", "config"),
    overwrite_existing=False,
    context_name=None,
):
    credentialResults = None
    credentialResults = client.list_credential(resource_group_name, cluster_name, name)

    # Check if KUBECONFIG environmental variable is set
    # If path is different than default then that means -f/--file is passed
    # in which case we ignore the KUBECONFIG variable
    # KUBECONFIG can be colon separated. If we find that condition, use the first entry
    if "KUBECONFIG" in os.environ and path == os.path.join(os.path.expanduser('~'), '.kube', 'config'):
        kubeconfig_path = os.environ["KUBECONFIG"].split(os.pathsep)[0]
        if kubeconfig_path:
            logger.info("The default path '%s' is replaced by '%s' defined in KUBECONFIG.", path, kubeconfig_path)
            path = kubeconfig_path
        else:
            logger.warning("Invalid path '%s' defined in KUBECONFIG.", kubeconfig_path)

    if not credentialResults:
        raise CLIError("No Kubernetes credentials found.")
    try:
        kubeconfig = credentialResults.kubeconfigs[0].value.decode(
            encoding='UTF-8')
        print_or_merge_credentials(
            path, kubeconfig, overwrite_existing, context_name)
    except (IndexError, ValueError) as exc:
        raise CLIError("Fail to find kubeconfig file.") from exc


def aks_maintenanceconfiguration_list(
    cmd,  # pylint: disable=unused-argument
    client,
    resource_group_name,
    cluster_name
):
    return client.list_by_managed_cluster(resource_group_name, cluster_name)


def aks_maintenanceconfiguration_show(
    cmd,  # pylint: disable=unused-argument
    client,
    resource_group_name,
    cluster_name,
    config_name
):
    logger.warning('resource_group_name: %s, cluster_name: %s, config_name: %s ',
                   resource_group_name, cluster_name, config_name)
    return client.get(resource_group_name, cluster_name, config_name)


def aks_maintenanceconfiguration_delete(
    cmd,  # pylint: disable=unused-argument
    client,
    resource_group_name,
    cluster_name,
    config_name
):
    logger.warning('resource_group_name: %s, cluster_name: %s, config_name: %s ',
                   resource_group_name, cluster_name, config_name)
    return client.delete(resource_group_name, cluster_name, config_name)


# pylint: disable=unused-argument
def aks_maintenanceconfiguration_add(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    config_name,
    config_file=None,
    weekday=None,
    start_hour=None,
    schedule_type=None,
    interval_days=None,
    interval_weeks=None,
    interval_months=None,
    day_of_week=None,
    day_of_month=None,
    week_index=None,
    duration_hours=None,
    utc_offset=None,
    start_date=None,
    start_time=None
):
    configs = client.list_by_managed_cluster(resource_group_name, cluster_name)
    for config in configs:
        if config.name == config_name:
            raise CLIError(
                f"Maintenance configuration '{config_name}' already exists, please try a different name, "
                "use 'aks maintenanceconfiguration list' to get current list of maitenance configurations"
            )
    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()
    return aks_maintenanceconfiguration_update_internal(cmd, client, raw_parameters)


def aks_maintenanceconfiguration_update(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    config_name,
    config_file=None,
    weekday=None,
    start_hour=None,
    schedule_type=None,
    interval_days=None,
    interval_weeks=None,
    interval_months=None,
    day_of_week=None,
    day_of_month=None,
    week_index=None,
    duration_hours=None,
    utc_offset=None,
    start_date=None,
    start_time=None
):
    configs = client.list_by_managed_cluster(resource_group_name, cluster_name)
    found = False
    for config in configs:
        if config.name == config_name:
            found = True
            break
    if not found:
        raise CLIError(
            f"Maintenance configuration '{config_name}' doesn't exist."
            "use 'aks maintenanceconfiguration list' to get current list of maitenance configurations"
        )
    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()
    return aks_maintenanceconfiguration_update_internal(cmd, client, raw_parameters)


# pylint: disable=too-many-locals, unused-argument
def aks_create(
    cmd,
    client,
    resource_group_name,
    name,
    ssh_key_value,
    location=None,
    kubernetes_version="",
    tags=None,
    dns_name_prefix=None,
    node_osdisk_diskencryptionset_id=None,
    disable_local_accounts=False,
    disable_rbac=None,
    edge_zone=None,
    admin_username="azureuser",
    generate_ssh_keys=False,
    no_ssh_key=False,
    pod_cidr=None,
    service_cidr=None,
    dns_service_ip=None,
    docker_bridge_address=None,
    load_balancer_sku=None,
    load_balancer_managed_outbound_ip_count=None,
    load_balancer_outbound_ips=None,
    load_balancer_outbound_ip_prefixes=None,
    load_balancer_outbound_ports=None,
    load_balancer_idle_timeout=None,
    load_balancer_backend_pool_type=None,
    nat_gateway_managed_outbound_ip_count=None,
    nat_gateway_idle_timeout=None,
    outbound_type=None,
    network_plugin=None,
    network_plugin_mode=None,
    network_policy=None,
    network_dataplane=None,
    kube_proxy_config=None,
    auto_upgrade_channel=None,
    node_os_upgrade_channel=None,
    cluster_autoscaler_profile=None,
    sku=None,
    tier=None,
    fqdn_subdomain=None,
    api_server_authorized_ip_ranges=None,
    enable_private_cluster=False,
    private_dns_zone=None,
    disable_public_fqdn=False,
    service_principal=None,
    client_secret=None,
    enable_managed_identity=None,
    assign_identity=None,
    assign_kubelet_identity=None,
    enable_aad=False,
    enable_azure_rbac=False,
    aad_tenant_id=None,
    aad_admin_group_object_ids=None,
    enable_oidc_issuer=False,
    windows_admin_username=None,
    windows_admin_password=None,
    enable_ahub=False,
    enable_windows_gmsa=False,
    gmsa_dns_server=None,
    gmsa_root_domain_name=None,
    attach_acr=None,
    skip_subnet_role_assignment=False,
    node_resource_group=None,
    k8s_support_plan=None,
    nrg_lockdown_restriction_level=None,
    enable_defender=False,
    defender_config=None,
    disk_driver_version=None,
    disable_disk_driver=False,
    disable_file_driver=False,
    enable_blob_driver=None,
    disable_snapshot_controller=False,
    enable_azure_keyvault_kms=False,
    azure_keyvault_kms_key_id=None,
    azure_keyvault_kms_key_vault_network_access=None,
    azure_keyvault_kms_key_vault_resource_id=None,
    http_proxy_config=None,
    bootstrap_artifact_source=CONST_ARTIFACT_SOURCE_DIRECT,
    bootstrap_container_registry_resource_id=None,
    # addons
    enable_addons=None,  # pylint: disable=redefined-outer-name
    workspace_resource_id=None,
    enable_msi_auth_for_monitoring=True,
    enable_syslog=False,
    data_collection_settings=None,
    ampls_resource_id=None,
    enable_high_log_scale_mode=False,
    aci_subnet_name=None,
    appgw_name=None,
    appgw_subnet_cidr=None,
    appgw_id=None,
    appgw_subnet_id=None,
    appgw_watch_namespace=None,
    enable_sgxquotehelper=False,
    enable_secret_rotation=False,
    rotation_poll_interval=None,
    enable_app_routing=False,
    app_routing_default_nginx_controller=None,
    # nodepool paramerters
    nodepool_name="nodepool1",
    node_vm_size=None,
    os_sku=None,
    snapshot_id=None,
    vnet_subnet_id=None,
    pod_subnet_id=None,
    pod_ip_allocation_mode=None,
    enable_node_public_ip=False,
    node_public_ip_prefix_id=None,
    enable_cluster_autoscaler=False,
    min_count=None,
    max_count=None,
    node_count=3,
    nodepool_tags=None,
    nodepool_labels=None,
    nodepool_taints=None,
    nodepool_initialization_taints=None,
    node_osdisk_type=None,
    node_osdisk_size=0,
    vm_set_type=None,
    zones=None,
    ppg=None,
    max_pods=0,
    enable_encryption_at_host=False,
    enable_ultra_ssd=False,
    enable_fips_image=False,
    kubelet_config=None,
    linux_os_config=None,
    host_group_id=None,
    gpu_instance_profile=None,
    # misc
    yes=False,
    no_wait=False,
    aks_custom_headers=None,
    # extensions
    # managed cluster
    ip_families=None,
    pod_cidrs=None,
    service_cidrs=None,
    load_balancer_managed_outbound_ipv6_count=None,
    enable_pod_identity=False,
    enable_pod_identity_with_kubenet=False,
    enable_workload_identity=False,
    enable_image_cleaner=False,
    image_cleaner_interval_hours=None,
    enable_image_integrity=False,
    cluster_snapshot_id=None,
    enable_apiserver_vnet_integration=False,
    apiserver_subnet_id=None,
    dns_zone_resource_id=None,
    dns_zone_resource_ids=None,
    enable_keda=False,
    enable_vpa=False,
    enable_optimized_addon_scaling=False,
    enable_cilium_dataplane=False,
    custom_ca_trust_certificates=None,
    # advanced networking
    enable_acns=None,
    disable_acns_observability=None,
    disable_acns_security=None,
    acns_advanced_networkpolicies=None,
    acns_transit_encryption_type=None,
    enable_retina_flow_logs=None,
    # nodepool
    crg_id=None,
    message_of_the_day=None,
    workload_runtime=None,
    enable_custom_ca_trust=False,
    nodepool_allowed_host_ports=None,
    nodepool_asg_ids=None,
    node_public_ip_tags=None,
    # safeguards parameters
    safeguards_level=None,
    safeguards_version=None,
    safeguards_excluded_ns=None,
    # azure service mesh
    enable_azure_service_mesh=None,
    revision=None,
    # azure monitor profile - metrics
    enable_azuremonitormetrics=False,
    enable_azure_monitor_metrics=False,
    azure_monitor_workspace_resource_id=None,
    ksm_metric_labels_allow_list=None,
    ksm_metric_annotations_allow_list=None,
    grafana_resource_id=None,
    enable_windows_recording_rules=False,
    # azure monitor profile - app monitoring
    enable_azure_monitor_app_monitoring=False,
    # metrics profile
    enable_cost_analysis=False,
    # AI toolchain operator
    enable_ai_toolchain_operator=False,
    # azure container storage
    enable_azure_container_storage=None,
    storage_pool_name=None,
    storage_pool_size=None,
    storage_pool_sku=None,
    storage_pool_option=None,
    ephemeral_disk_volume_type=None,
    ephemeral_disk_nvme_perf_tier=None,
    node_provisioning_mode=None,
    node_provisioning_default_pools=None,
    ssh_access=CONST_SSH_ACCESS_LOCALUSER,
    # trusted launch
    enable_secure_boot=False,
    enable_vtpm=False,
    cluster_service_load_balancer_health_probe_mode=None,
    if_match=None,
    if_none_match=None,
    # Static Egress Gateway
    enable_static_egress_gateway=False,
    # virtualmachines
    vm_sizes=None,
    # IMDS restriction
    enable_imds_restriction=False,
    # managed system pool
    enable_managed_system_pool=False,
):
    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()

    # validation for existing cluster
    existing_mc = None
    try:
        existing_mc = client.get(resource_group_name, name)
    # pylint: disable=broad-except
    except Exception as ex:
        logger.debug("failed to get cluster, error: %s", ex)
    if existing_mc:
        raise ClientRequestError(
            f"The cluster '{name}' under resource group '{resource_group_name}' already exists. "
            "Please use command 'az aks update' to update the existing cluster, "
            "or select a different cluster name to create a new cluster."
        )

    # decorator pattern
    from azure.cli.command_modules.acs._consts import DecoratorEarlyExitException
    from azext_aks_preview.managed_cluster_decorator import AKSPreviewManagedClusterCreateDecorator
    aks_create_decorator = AKSPreviewManagedClusterCreateDecorator(
        cmd=cmd,
        client=client,
        raw_parameters=raw_parameters,
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
    )
    try:
        # construct mc profile
        mc = aks_create_decorator.construct_mc_profile_preview()
    except DecoratorEarlyExitException:
        # exit gracefully
        return None

    # send request to create a real managed cluster
    return aks_create_decorator.create_mc(mc)


# pylint: disable=too-many-locals, unused-argument
def aks_update(
    cmd,
    client,
    resource_group_name,
    name,
    tags=None,
    disable_local_accounts=False,
    enable_local_accounts=False,
    load_balancer_sku=None,
    load_balancer_managed_outbound_ip_count=None,
    load_balancer_outbound_ips=None,
    load_balancer_outbound_ip_prefixes=None,
    load_balancer_outbound_ports=None,
    load_balancer_idle_timeout=None,
    load_balancer_backend_pool_type=None,
    nat_gateway_managed_outbound_ip_count=None,
    nat_gateway_idle_timeout=None,
    kube_proxy_config=None,
    auto_upgrade_channel=None,
    node_os_upgrade_channel=None,
    enable_force_upgrade=False,
    disable_force_upgrade=False,
    upgrade_override_until=None,
    cluster_autoscaler_profile=None,
    sku=None,
    tier=None,
    api_server_authorized_ip_ranges=None,
    enable_public_fqdn=False,
    disable_public_fqdn=False,
    enable_managed_identity=False,
    assign_identity=None,
    assign_kubelet_identity=None,
    enable_aad=False,
    enable_azure_rbac=False,
    disable_azure_rbac=False,
    aad_tenant_id=None,
    aad_admin_group_object_ids=None,
    enable_oidc_issuer=False,
    k8s_support_plan=None,
    windows_admin_password=None,
    enable_ahub=False,
    disable_ahub=False,
    enable_windows_gmsa=False,
    gmsa_dns_server=None,
    gmsa_root_domain_name=None,
    attach_acr=None,
    detach_acr=None,
    nrg_lockdown_restriction_level=None,
    enable_defender=False,
    disable_defender=False,
    defender_config=None,
    enable_disk_driver=False,
    disk_driver_version=None,
    disable_disk_driver=False,
    enable_file_driver=False,
    disable_file_driver=False,
    enable_blob_driver=None,
    disable_blob_driver=None,
    enable_snapshot_controller=False,
    disable_snapshot_controller=False,
    enable_azure_keyvault_kms=False,
    disable_azure_keyvault_kms=False,
    azure_keyvault_kms_key_id=None,
    azure_keyvault_kms_key_vault_network_access=None,
    azure_keyvault_kms_key_vault_resource_id=None,
    http_proxy_config=None,
    disable_http_proxy=False,
    enable_http_proxy=False,
    bootstrap_artifact_source=None,
    bootstrap_container_registry_resource_id=None,
    # addons
    enable_secret_rotation=False,
    disable_secret_rotation=False,
    rotation_poll_interval=None,
    # nodepool paramerters
    enable_cluster_autoscaler=False,
    disable_cluster_autoscaler=False,
    update_cluster_autoscaler=False,
    min_count=None,
    max_count=None,
    nodepool_labels=None,
    nodepool_taints=None,
    nodepool_initialization_taints=None,
    # misc
    yes=False,
    no_wait=False,
    aks_custom_headers=None,
    # extensions
    # managed cluster
    ssh_key_value=None,
    load_balancer_managed_outbound_ipv6_count=None,
    outbound_type=None,
    network_plugin=None,
    network_plugin_mode=None,
    network_policy=None,
    network_dataplane=None,
    ip_families=None,
    pod_cidr=None,
    enable_pod_identity=False,
    enable_pod_identity_with_kubenet=False,
    disable_pod_identity=False,
    enable_workload_identity=False,
    disable_workload_identity=False,
    enable_image_cleaner=False,
    disable_image_cleaner=False,
    image_cleaner_interval_hours=None,
    enable_image_integrity=False,
    disable_image_integrity=False,
    enable_apiserver_vnet_integration=False,
    apiserver_subnet_id=None,
    enable_keda=False,
    disable_keda=False,
    enable_private_cluster=False,
    disable_private_cluster=False,
    private_dns_zone=None,
    enable_azuremonitormetrics=False,
    enable_azure_monitor_metrics=False,
    azure_monitor_workspace_resource_id=None,
    ksm_metric_labels_allow_list=None,
    ksm_metric_annotations_allow_list=None,
    grafana_resource_id=None,
    enable_windows_recording_rules=False,
    disable_azuremonitormetrics=False,
    disable_azure_monitor_metrics=False,
    # azure monitor profile - app monitoring
    enable_azure_monitor_app_monitoring=False,
    disable_azure_monitor_app_monitoring=False,
    enable_vpa=False,
    disable_vpa=False,
    enable_optimized_addon_scaling=False,
    disable_optimized_addon_scaling=False,
    cluster_snapshot_id=None,
    custom_ca_trust_certificates=None,
    # safeguards parameters
    safeguards_level=None,
    safeguards_version=None,
    safeguards_excluded_ns=None,
    # advanced networking
    enable_acns=None,
    disable_acns=None,
    disable_acns_observability=None,
    disable_acns_security=None,
    acns_advanced_networkpolicies=None,
    acns_transit_encryption_type=None,
    enable_retina_flow_logs=None,
    disable_retina_flow_logs=None,
    # metrics profile
    enable_cost_analysis=False,
    disable_cost_analysis=False,
    # AI toolchain operator
    enable_ai_toolchain_operator=False,
    disable_ai_toolchain_operator=False,
    # azure container storage
    enable_azure_container_storage=None,
    disable_azure_container_storage=None,
    storage_pool_name=None,
    storage_pool_size=None,
    storage_pool_sku=None,
    storage_pool_option=None,
    azure_container_storage_nodepools=None,
    ephemeral_disk_volume_type=None,
    ephemeral_disk_nvme_perf_tier=None,
    node_provisioning_mode=None,
    node_provisioning_default_pools=None,
    cluster_service_load_balancer_health_probe_mode=None,
    if_match=None,
    if_none_match=None,
    # Static Egress Gateway
    enable_static_egress_gateway=False,
    disable_static_egress_gateway=False,
    # IMDS restriction
    enable_imds_restriction=False,
    disable_imds_restriction=False,
    migrate_vmas_to_vms=False,
):
    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()

    from azure.cli.command_modules.acs._consts import DecoratorEarlyExitException
    from azext_aks_preview.managed_cluster_decorator import AKSPreviewManagedClusterUpdateDecorator

    # decorator pattern
    aks_update_decorator = AKSPreviewManagedClusterUpdateDecorator(
        cmd=cmd,
        client=client,
        raw_parameters=raw_parameters,
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
    )
    try:
        # update mc profile
        mc = aks_update_decorator.update_mc_profile_preview()
    except DecoratorEarlyExitException:
        # exit gracefully
        return None
    # send request to update the real managed cluster
    return aks_update_decorator.update_mc(mc)


# pylint: disable=unused-argument
def aks_show(cmd, client, resource_group_name, name, aks_custom_headers=None):
    headers = get_aks_custom_headers(aks_custom_headers)
    mc = client.get(resource_group_name, name, headers=headers)
    return _remove_nulls([mc])[0]


# pylint: disable=unused-argument
def aks_stop(cmd, client, resource_group_name, name, no_wait=False):
    instance = client.get(resource_group_name, name)
    # print warning when stopping a private cluster
    if check_is_private_link_cluster(instance):
        logger.warning(
            "Your private cluster apiserver IP might get changed when it's stopped and started.\n"
            "Any user provisioned private endpoints linked to this private cluster will need to be deleted and "
            "created again. Any user managed DNS record also needs to be updated with the new IP."
        )
    return sdk_no_wait(no_wait, client.begin_stop, resource_group_name, name)


# pylint: disable=unused-argument
def aks_list(cmd, client, resource_group_name=None):
    if resource_group_name:
        managed_clusters = client.list_by_resource_group(resource_group_name)
    else:
        managed_clusters = client.list()
    return _remove_nulls(list(managed_clusters))


def _remove_nulls(managed_clusters):
    """
    Remove some often-empty fields from a list of ManagedClusters, so the JSON representation
    doesn't contain distracting null fields.

    This works around a quirk of the SDK for python behavior. These fields are not sent
    by the server, but get recreated by the CLI's own "to_dict" serialization.
    """
    attrs = ['tags']
    ap_attrs = ['os_disk_size_gb', 'vnet_subnet_id']
    sp_attrs = ['secret']
    for managed_cluster in managed_clusters:
        for attr in attrs:
            if getattr(managed_cluster, attr, None) is None:
                delattr(managed_cluster, attr)
        if managed_cluster.agent_pool_profiles is not None:
            for ap_profile in managed_cluster.agent_pool_profiles:
                for attr in ap_attrs:
                    if getattr(ap_profile, attr, None) is None:
                        delattr(ap_profile, attr)
        for attr in sp_attrs:
            if getattr(managed_cluster.service_principal_profile, attr, None) is None:
                delattr(managed_cluster.service_principal_profile, attr)
    return managed_clusters


def aks_get_credentials(
    cmd,  # pylint: disable=unused-argument
    client,
    resource_group_name,
    name,
    admin=False,
    user="clusterUser",
    path=os.path.join(os.path.expanduser("~"), ".kube", "config"),
    overwrite_existing=False,
    context_name=None,
    public_fqdn=False,
    credential_format=None,
    aks_custom_headers=None,
):
    headers = get_aks_custom_headers(aks_custom_headers)
    credentialResults = None
    serverType = None
    if public_fqdn:
        serverType = 'public'
    if credential_format:
        credential_format = credential_format.lower()
        if admin:
            raise InvalidArgumentValueError("--format can only be specified when requesting clusterUser credential.")
    if admin:
        credentialResults = client.list_cluster_admin_credentials(
            resource_group_name, name, serverType, headers=headers)
    else:
        if user.lower() == 'clusteruser':
            credentialResults = client.list_cluster_user_credentials(
                resource_group_name, name, serverType, credential_format, headers=headers)
        elif user.lower() == 'clustermonitoringuser':
            credentialResults = client.list_cluster_monitoring_user_credentials(
                resource_group_name, name, serverType, headers=headers)
        else:
            raise InvalidArgumentValueError("The value of option --user is invalid.")

    # Check if KUBECONFIG environmental variable is set
    # If path is different than default then that means -f/--file is passed
    # in which case we ignore the KUBECONFIG variable
    # KUBECONFIG can be colon separated. If we find that condition, use the first entry
    if "KUBECONFIG" in os.environ and path == os.path.join(os.path.expanduser('~'), '.kube', 'config'):
        kubeconfig_path = os.environ["KUBECONFIG"].split(os.pathsep)[0]
        if kubeconfig_path:
            logger.info("The default path '%s' is replaced by '%s' defined in KUBECONFIG.", path, kubeconfig_path)
            path = kubeconfig_path
        else:
            logger.warning("Invalid path '%s' defined in KUBECONFIG.", kubeconfig_path)

    if not credentialResults:
        raise CLIError("No Kubernetes credentials found.")
    try:
        kubeconfig = credentialResults.kubeconfigs[0].value.decode(
            encoding='UTF-8')
        print_or_merge_credentials(
            path, kubeconfig, overwrite_existing, context_name)
    except (IndexError, ValueError) as exc:
        raise CLIError("Fail to find kubeconfig file.") from exc


def aks_scale(cmd,  # pylint: disable=unused-argument
              client,
              resource_group_name,
              name,
              node_count,
              nodepool_name="",
              no_wait=False,
              aks_custom_headers=None):
    headers = get_aks_custom_headers(aks_custom_headers)
    instance = client.get(resource_group_name, name)
    _fill_defaults_for_pod_identity_profile(instance.pod_identity_profile)

    if len(instance.agent_pool_profiles) > 1 and nodepool_name == "":
        raise CLIError(
            "There are more than one node pool in the cluster. "
            "Please specify nodepool name or use az aks nodepool command to scale node pool"
        )

    for agent_profile in instance.agent_pool_profiles:
        if agent_profile.name == nodepool_name or (nodepool_name == "" and len(instance.agent_pool_profiles) == 1):
            if agent_profile.enable_auto_scaling:
                raise CLIError(
                    "Cannot scale cluster autoscaler enabled node pool.")

            if agent_profile.type == CONST_VIRTUAL_MACHINES:
                if len(agent_profile.virtual_machines_profile.scale.manual) == 1:
                    agent_profile.virtual_machines_profile.scale.manual[0].count = int(node_count)
                else:
                    raise ClientRequestError("Cannot scale virtual machines node pool with more than one size.")
            else:
                agent_profile.count = int(node_count)
            # null out the SP profile because otherwise validation complains
            instance.service_principal_profile = None
            return sdk_no_wait(
                no_wait,
                client.begin_create_or_update,
                resource_group_name,
                name,
                instance,
                headers=headers,
            )
    raise CLIError(f'The nodepool "{nodepool_name}" was not found.')


# pylint: disable=too-many-return-statements, too-many-branches
def aks_upgrade(cmd,
                client,
                resource_group_name,
                name,
                kubernetes_version='',
                control_plane_only=False,
                no_wait=False,
                node_image_only=False,
                cluster_snapshot_id=None,
                aks_custom_headers=None,
                enable_force_upgrade=False,
                disable_force_upgrade=False,
                upgrade_override_until=None,
                yes=False,
                if_match=None,
                if_none_match=None):
    msg = 'Kubernetes may be unavailable during cluster upgrades.\n Are you sure you want to perform this operation?'
    if not yes and not prompt_y_n(msg, default="n"):
        return None

    instance = client.get(resource_group_name, name)
    _fill_defaults_for_pod_identity_profile(instance.pod_identity_profile)

    vmas_cluster = False
    for agent_profile in instance.agent_pool_profiles:
        if agent_profile.type.lower() == "availabilityset":
            vmas_cluster = True
            break

    if kubernetes_version != '' and node_image_only:
        raise CLIError('Conflicting flags. Upgrading the Kubernetes version will also upgrade node image version. '
                       'If you only want to upgrade the node version please use the "--node-image-only" option only.')

    if node_image_only:
        msg = "This node image upgrade operation will run across every node pool in the cluster " \
              "and might take a while. Do you wish to continue?"
        if not yes and not prompt_y_n(msg, default="n"):
            return None

        # This only provide convenience for customer at client side so they can run az aks upgrade to upgrade all
        # nodepools of a cluster. The SDK only support upgrade single nodepool at a time.
        for agent_pool_profile in instance.agent_pool_profiles:
            if vmas_cluster:
                raise CLIError('This cluster is not using VirtualMachineScaleSets. Node image upgrade only operation '
                               'can only be applied on VirtualMachineScaleSets and VirtualMachines(Preview) cluster.')
            agent_pool_client = cf_agent_pools(cmd.cli_ctx)
            _upgrade_single_nodepool_image_version(
                True, agent_pool_client, resource_group_name, name, agent_pool_profile.name, None)
        mc = client.get(resource_group_name, name)
        return _remove_nulls([mc])[0]

    if cluster_snapshot_id:
        CreationData = cmd.get_models(
            "CreationData",
            resource_type=CUSTOM_MGMT_AKS_PREVIEW,
            operation_group="managed_clusters",
        )
        instance.creation_data = CreationData(
            source_resource_id=cluster_snapshot_id
        )
        mcsnapshot = get_cluster_snapshot_by_snapshot_id(cmd.cli_ctx, cluster_snapshot_id)
        kubernetes_version = mcsnapshot.managed_cluster_properties_read_only.kubernetes_version

    instance = _update_upgrade_settings(
        cmd,
        instance,
        enable_force_upgrade=enable_force_upgrade,
        disable_force_upgrade=disable_force_upgrade,
        upgrade_override_until=upgrade_override_until)

    if instance.kubernetes_version == kubernetes_version:
        if instance.provisioning_state == "Succeeded":
            logger.warning("The cluster is already on version %s and is not in a failed state. No operations "
                           "will occur when upgrading to the same version if the cluster is not in a failed state.",
                           instance.kubernetes_version)
        elif instance.provisioning_state == "Failed":
            logger.warning("Cluster currently in failed state. Proceeding with upgrade to existing version %s to "
                           "attempt resolution of failed cluster state.", instance.kubernetes_version)

    upgrade_all = False
    instance.kubernetes_version = kubernetes_version

    # for legacy clusters, we always upgrade node pools with CCP.
    if instance.max_agent_pools < 8 or vmas_cluster:
        if control_plane_only:
            msg = (
                "Legacy clusters do not support control plane only upgrade. All node pools will be "
                f"upgraded to {instance.kubernetes_version} as well. Continue?"
            )
            if not yes and not prompt_y_n(msg, default="n"):
                return None
        upgrade_all = True
    else:
        if not control_plane_only:
            msg = (
                "Since control-plane-only argument is not specified, this will upgrade the control plane "
                f"AND all nodepools to version {instance.kubernetes_version}. Continue?"
            )
            if not yes and not prompt_y_n(msg, default="n"):
                return None
            upgrade_all = True
        else:
            msg = (
                "Since control-plane-only argument is specified, this will upgrade only the control plane to "
                f"{instance.kubernetes_version}. Node pool will not change. Continue?"
            )
            if not yes and not prompt_y_n(msg, default="n"):
                return None

    if upgrade_all:
        for agent_profile in instance.agent_pool_profiles:
            agent_profile.orchestrator_version = kubernetes_version
            agent_profile.creation_data = None

    # null out the SP profile because otherwise validation complains
    instance.service_principal_profile = None

    headers = get_aks_custom_headers(aks_custom_headers)

    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        name,
        instance,
        headers=headers,
        if_match=if_match,
        if_none_match=if_none_match)


def _update_upgrade_settings(cmd, instance,
                             enable_force_upgrade=False,
                             disable_force_upgrade=False,
                             upgrade_override_until=None):
    existing_until = None
    if (instance.upgrade_settings is not None and instance.upgrade_settings.override_settings is not None
            and instance.upgrade_settings.override_settings.until is not None):
        existing_until = instance.upgrade_settings.override_settings.until

    force_upgrade = None
    if enable_force_upgrade is False and disable_force_upgrade is False:
        force_upgrade = None
    elif enable_force_upgrade is not None:
        force_upgrade = enable_force_upgrade
    elif disable_force_upgrade is not None:
        force_upgrade = not disable_force_upgrade

    ClusterUpgradeSettings = cmd.get_models(
        "ClusterUpgradeSettings",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_clusters",
    )

    UpgradeOverrideSettings = cmd.get_models(
        "UpgradeOverrideSettings",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_clusters",
    )

    if force_upgrade is not None or upgrade_override_until is not None:
        if instance.upgrade_settings is None:
            instance.upgrade_settings = ClusterUpgradeSettings()
        if instance.upgrade_settings.override_settings is None:
            instance.upgrade_settings.override_settings = UpgradeOverrideSettings()
        # sets force_upgrade
        if force_upgrade is not None:
            instance.upgrade_settings.override_settings.force_upgrade = force_upgrade
        # sets until
        if upgrade_override_until is not None:
            try:
                instance.upgrade_settings.override_settings.until = parse(upgrade_override_until)
            except Exception:  # pylint: disable=broad-except
                raise InvalidArgumentValueError(
                    f"{upgrade_override_until} is not a valid datatime format."
                )
        elif force_upgrade:
            default_extended_until = datetime.datetime.utcnow() + datetime.timedelta(days=3)
            if existing_until is None or existing_until.timestamp() < default_extended_until.timestamp():
                instance.upgrade_settings.override_settings.until = default_extended_until
    return instance


def _upgrade_single_nodepool_image_version(
    no_wait, client, resource_group_name, cluster_name, nodepool_name, snapshot_id=None
):
    headers = {}
    if snapshot_id:
        headers["AKSSnapshotId"] = snapshot_id

    return sdk_no_wait(
        no_wait,
        client.begin_upgrade_node_image_version,
        resource_group_name,
        cluster_name,
        nodepool_name,
        headers=headers,
    )


def aks_agentpool_show(cmd,     # pylint: disable=unused-argument
                       client,
                       resource_group_name,
                       cluster_name,
                       nodepool_name):
    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    return instance


def aks_agentpool_list(cmd,     # pylint: disable=unused-argument
                       client,
                       resource_group_name,
                       cluster_name):
    return client.list(resource_group_name, cluster_name)


# pylint: disable=too-many-locals
def aks_agentpool_add(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    nodepool_name,
    kubernetes_version=None,
    node_vm_size=None,
    os_type=None,
    os_sku=None,
    snapshot_id=None,
    vnet_subnet_id=None,
    pod_subnet_id=None,
    pod_ip_allocation_mode=None,
    enable_node_public_ip=False,
    node_public_ip_prefix_id=None,
    enable_cluster_autoscaler=False,
    min_count=None,
    max_count=None,
    node_count=3,
    priority=CONST_SCALE_SET_PRIORITY_REGULAR,
    eviction_policy=CONST_SPOT_EVICTION_POLICY_DELETE,
    spot_max_price=float("nan"),
    labels=None,
    tags=None,
    node_taints=None,
    node_osdisk_type=None,
    node_osdisk_size=0,
    max_surge=None,
    drain_timeout=None,
    node_soak_duration=None,
    undrainable_node_behavior=None,
    max_unavailable=None,
    max_blocked_nodes=None,
    mode=CONST_NODEPOOL_MODE_USER,
    scale_down_mode=CONST_SCALE_DOWN_MODE_DELETE,
    max_pods=0,
    zones=None,
    ppg=None,
    vm_set_type=None,
    enable_encryption_at_host=False,
    enable_ultra_ssd=False,
    enable_fips_image=False,
    kubelet_config=None,
    linux_os_config=None,
    host_group_id=None,
    gpu_instance_profile=None,
    # misc
    no_wait=False,
    aks_custom_headers=None,
    # extensions
    crg_id=None,
    message_of_the_day=None,
    workload_runtime=None,
    enable_custom_ca_trust=False,
    disable_windows_outbound_nat=False,
    allowed_host_ports=None,
    asg_ids=None,
    node_public_ip_tags=None,
    enable_artifact_streaming=False,
    skip_gpu_driver_install=False,
    gpu_driver=None,
    driver_type=None,
    ssh_access=CONST_SSH_ACCESS_LOCALUSER,
    # trusted launch
    enable_secure_boot=False,
    enable_vtpm=False,
    if_match=None,
    if_none_match=None,
    # static egress gateway - gateway-mode pool
    gateway_prefix_size=None,
    # virtualmachines
    vm_sizes=None,
    # local DNS
    localdns_config=None,
):
    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()

    # decorator pattern
    from azure.cli.command_modules.acs._consts import AgentPoolDecoratorMode, DecoratorEarlyExitException
    from azext_aks_preview.agentpool_decorator import AKSPreviewAgentPoolAddDecorator
    aks_agentpool_add_decorator = AKSPreviewAgentPoolAddDecorator(
        cmd=cmd,
        client=client,
        raw_parameters=raw_parameters,
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        agentpool_decorator_mode=AgentPoolDecoratorMode.STANDALONE,
    )
    try:
        # construct agentpool profile
        agentpool = aks_agentpool_add_decorator.construct_agentpool_profile_preview()
    except DecoratorEarlyExitException:
        # exit gracefully
        return None
    # send request to add a real agentpool
    return aks_agentpool_add_decorator.add_agentpool(agentpool)


# pylint: disable=too-many-locals
def aks_agentpool_update(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    nodepool_name,
    enable_cluster_autoscaler=False,
    disable_cluster_autoscaler=False,
    update_cluster_autoscaler=False,
    min_count=None,
    max_count=None,
    labels=None,
    tags=None,
    node_taints=None,
    max_surge=None,
    drain_timeout=None,
    node_soak_duration=None,
    undrainable_node_behavior=None,
    max_unavailable=None,
    max_blocked_nodes=None,
    mode=None,
    scale_down_mode=None,
    no_wait=False,
    aks_custom_headers=None,
    # extensions
    enable_custom_ca_trust=False,
    disable_custom_ca_trust=False,
    allowed_host_ports=None,
    asg_ids=None,
    enable_artifact_streaming=False,
    os_sku=None,
    ssh_access=None,
    yes=False,
    # trusted launch
    enable_secure_boot=False,
    disable_secure_boot=False,
    enable_vtpm=False,
    disable_vtpm=False,
    if_match=None,
    if_none_match=None,
    enable_fips_image=False,
    disable_fips_image=False,
    # local DNS
    localdns_config=None,
):
    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()

    # decorator pattern
    from azure.cli.command_modules.acs._consts import AgentPoolDecoratorMode, DecoratorEarlyExitException
    from azext_aks_preview.agentpool_decorator import AKSPreviewAgentPoolUpdateDecorator
    aks_agentpool_update_decorator = AKSPreviewAgentPoolUpdateDecorator(
        cmd=cmd,
        client=client,
        raw_parameters=raw_parameters,
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        agentpool_decorator_mode=AgentPoolDecoratorMode.STANDALONE,
    )
    try:
        # update agentpool profile
        agentpool = aks_agentpool_update_decorator.update_agentpool_profile_preview()
    except DecoratorEarlyExitException:
        # exit gracefully
        return None
    # send request to update the real agentpool
    return aks_agentpool_update_decorator.update_agentpool(agentpool)


def aks_agentpool_scale(cmd,    # pylint: disable=unused-argument
                        client,
                        resource_group_name,
                        cluster_name,
                        nodepool_name,
                        node_count=3,
                        no_wait=False,
                        aks_custom_headers=None):
    headers = get_aks_custom_headers(aks_custom_headers)
    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    new_node_count = int(node_count)
    if instance.enable_auto_scaling:
        raise CLIError("Cannot scale cluster autoscaler enabled node pool.")
    if new_node_count == instance.count:
        raise CLIError(
            "The new node count is the same as the current node count.")
    if instance.type_properties_type == CONST_VIRTUAL_MACHINES:
        if len(instance.virtual_machines_profile.scale.manual) == 1:
            instance.virtual_machines_profile.scale.manual[0].count = new_node_count
        else:
            raise ClientRequestError("Cannot scale virtual machines node pool with more than one size.")
    else:
        instance.count = new_node_count  # pylint: disable=no-member
    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        nodepool_name,
        instance,
        headers=headers,
    )


def aks_agentpool_upgrade(cmd,
                          client,
                          resource_group_name,
                          cluster_name,
                          nodepool_name,
                          kubernetes_version='',
                          node_image_only=False,
                          max_surge=None,
                          drain_timeout=None,
                          node_soak_duration=None,
                          undrainable_node_behavior=None,
                          max_unavailable=None,
                          max_blocked_nodes=None,
                          snapshot_id=None,
                          no_wait=False,
                          aks_custom_headers=None,
                          yes=False,
                          if_match=None,
                          if_none_match=None):
    AgentPoolUpgradeSettings = cmd.get_models(
        "AgentPoolUpgradeSettings",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="agent_pools",
    )
    if kubernetes_version != '' and node_image_only:
        raise MutuallyExclusiveArgumentError(
            'Conflicting flags. Upgrading the Kubernetes version will also '
            'upgrade node image version. If you only want to upgrade the '
            'node version please use the "--node-image-only" option only.'
        )

    # Note: we exclude this option because node image upgrade can't accept nodepool put fields like max surge
    hasUpgradeSetting = (
        max_surge or
        drain_timeout or
        node_soak_duration or
        undrainable_node_behavior or
        max_unavailable or
        max_blocked_nodes)
    if hasUpgradeSetting and node_image_only:
        raise MutuallyExclusiveArgumentError(
            "Conflicting flags. Unable to specify "
            "max-surge/drain-timeout/node-soak-duration/undrainable-node-behavior/max-unavailable/max-blocked-nodes"
            " with node-image-only.If you want to use "
            "max-surge/drain-timeout/node-soak-duration/undrainable-node-behavior/max-unavailable/max-blocked-nodes"
            " with a node image upgrade, please first update "
            "max-surge/drain-timeout/node-soak-duration/undrainable-node-behavior/max-unavailable/max-blocked-nodes"
            " using 'az aks nodepool update "
            "--max-surge/--drain-timeout/--node-soak-duration/"
            "--undrainable-node-behavior/--max-unavailable/--max-blocked-nodes'."
        )

    if node_image_only:
        return _upgrade_single_nodepool_image_version(no_wait,
                                                      client,
                                                      resource_group_name,
                                                      cluster_name,
                                                      nodepool_name,
                                                      snapshot_id)

    # load model CreationData, for nodepool snapshot
    CreationData = cmd.get_models(
        "CreationData",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_clusters",
    )

    creationData = None
    if snapshot_id:
        snapshot = get_nodepool_snapshot_by_snapshot_id(cmd.cli_ctx, snapshot_id)
        if not kubernetes_version and not node_image_only:
            kubernetes_version = snapshot.kubernetes_version

        creationData = CreationData(
            source_resource_id=snapshot_id
        )

    instance = client.get(resource_group_name, cluster_name, nodepool_name)

    if kubernetes_version != '' or instance.orchestrator_version == kubernetes_version:
        msg = "The new kubernetes version is the same as the current kubernetes version."
        if instance.provisioning_state == "Succeeded":
            msg = (
                f"The cluster is already on version {instance.orchestrator_version} and is not in a failed state. "
                "No operations will occur when upgrading to the same version if the cluster "
                "is not in a failed state."
            )
        elif instance.provisioning_state == "Failed":
            msg = (
                "Cluster currently in failed state. Proceeding with upgrade to existing version "
                f"{instance.orchestrator_version} to attempt resolution of failed cluster state."
            )
        if not yes and not prompt_y_n(msg):
            return None

    instance.orchestrator_version = kubernetes_version
    instance.creation_data = creationData

    if not instance.upgrade_settings:
        instance.upgrade_settings = AgentPoolUpgradeSettings()

    if max_surge:
        instance.upgrade_settings.max_surge = max_surge
    if drain_timeout:
        instance.upgrade_settings.drain_timeout_in_minutes = drain_timeout
    if isinstance(node_soak_duration, int) and node_soak_duration >= 0:
        instance.upgrade_settings.node_soak_duration_in_minutes = node_soak_duration
    if undrainable_node_behavior:
        instance.upgrade_settings.undrainable_node_behavior = undrainable_node_behavior
    if max_unavailable:
        instance.upgrade_settings.max_unavailable = max_unavailable
    if max_blocked_nodes:
        instance.upgrade_settings.max_blocked_nodes = max_blocked_nodes

    # custom headers
    aks_custom_headers = extract_comma_separated_string(
        aks_custom_headers,
        enable_strip=True,
        extract_kv=True,
        default_value={},
        allow_appending_values_to_same_key=True,
    )

    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        nodepool_name,
        instance,
        headers=aks_custom_headers,
        if_match=if_match,
        if_none_match=if_none_match,
    )


def aks_agentpool_get_upgrade_profile(cmd,   # pylint: disable=unused-argument
                                      client,
                                      resource_group_name,
                                      cluster_name,
                                      nodepool_name):
    return client.get_upgrade_profile(resource_group_name, cluster_name, nodepool_name)


def aks_agentpool_stop(cmd,   # pylint: disable=unused-argument
                       client,
                       resource_group_name,
                       cluster_name,
                       nodepool_name,
                       aks_custom_headers=None,
                       no_wait=False):
    PowerState = cmd.get_models(
        "PowerState",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_clusters",
    )

    agentpool_exists = False
    instances = client.list(resource_group_name, cluster_name)
    for agentpool_profile in instances:
        if agentpool_profile.name.lower() == nodepool_name.lower():
            agentpool_exists = True
            break

    if not agentpool_exists:
        raise InvalidArgumentValueError(
            f"Node pool {nodepool_name} doesnt exist, use 'aks nodepool list' to get current node pool list"
        )

    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    power_state = PowerState(code="Stopped")
    instance.power_state = power_state
    headers = get_aks_custom_headers(aks_custom_headers)
    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        nodepool_name,
        instance,
        headers=headers,
    )


def aks_agentpool_start(cmd,   # pylint: disable=unused-argument
                        client,
                        resource_group_name,
                        cluster_name,
                        nodepool_name,
                        aks_custom_headers=None,
                        no_wait=False):
    PowerState = cmd.get_models(
        "PowerState",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_clusters",
    )

    agentpool_exists = False
    instances = client.list(resource_group_name, cluster_name)
    for agentpool_profile in instances:
        if agentpool_profile.name.lower() == nodepool_name.lower():
            agentpool_exists = True
            break
    if not agentpool_exists:
        raise InvalidArgumentValueError(
            f"Node pool {nodepool_name} doesnt exist, use 'aks nodepool list' to get current node pool list"
        )
    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    power_state = PowerState(code="Running")
    instance.power_state = power_state
    headers = get_aks_custom_headers(aks_custom_headers)
    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        nodepool_name,
        instance,
        headers=headers,
    )


def aks_agentpool_delete(cmd,   # pylint: disable=unused-argument
                         client,
                         resource_group_name,
                         cluster_name,
                         nodepool_name,
                         ignore_pod_disruption_budget=None,
                         no_wait=False,
                         if_match=None):
    agentpool_exists = False
    instances = client.list(resource_group_name, cluster_name)
    for agentpool_profile in instances:
        if agentpool_profile.name.lower() == nodepool_name.lower():
            agentpool_exists = True
            break

    if not agentpool_exists:
        raise CLIError(
            f"Node pool {nodepool_name} doesnt exist, "
            "use 'aks nodepool list' to get current node pool list"
        )

    return sdk_no_wait(
        no_wait,
        client.begin_delete,
        resource_group_name,
        cluster_name,
        nodepool_name,
        if_match=if_match,
        ignore_pod_disruption_budget=ignore_pod_disruption_budget,
    )


def aks_agentpool_operation_abort(cmd,   # pylint: disable=unused-argument
                                  client,
                                  resource_group_name,
                                  cluster_name,
                                  nodepool_name,
                                  aks_custom_headers=None,
                                  no_wait=False):
    PowerState = cmd.get_models(
        "PowerState",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="agent_pools",
    )

    agentpool_exists = False
    instances = client.list(resource_group_name, cluster_name)
    for agentpool_profile in instances:
        if agentpool_profile.name.lower() == nodepool_name.lower():
            agentpool_exists = True
            break
    if not agentpool_exists:
        raise InvalidArgumentValueError(
            f"Node pool {nodepool_name} doesnt exist, use 'aks nodepool list' to get current node pool list")
    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    power_state = PowerState(code="Running")
    instance.power_state = power_state
    headers = get_aks_custom_headers(aks_custom_headers)
    return sdk_no_wait(
        no_wait,
        client.begin_abort_latest_operation,
        resource_group_name,
        cluster_name,
        nodepool_name,
        headers=headers,
    )


def aks_agentpool_delete_machines(cmd,   # pylint: disable=unused-argument
                                  client,
                                  resource_group_name,
                                  cluster_name,
                                  nodepool_name,
                                  machine_names,
                                  no_wait=False):
    agentpool_exists = False
    instances = client.list(resource_group_name, cluster_name)
    for agentpool_profile in instances:
        if agentpool_profile.name.lower() == nodepool_name.lower():
            agentpool_exists = True
            break

    if not agentpool_exists:
        raise ResourceNotFoundError(
            f"Node pool {nodepool_name} doesn't exist, "
            "use 'az aks nodepool list' to get current node pool list"
        )

    if len(machine_names) == 0:
        raise RequiredArgumentMissingError(
            "--machine-names doesn't provide, "
            "use 'az aks machine list' to get current machine list"
        )

    AgentPoolDeleteMachinesParameter = cmd.get_models(
        "AgentPoolDeleteMachinesParameter",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="agent_pools",
    )

    machines = AgentPoolDeleteMachinesParameter(machine_names=machine_names)
    return sdk_no_wait(
        no_wait,
        client.begin_delete_machines,
        resource_group_name,
        cluster_name,
        nodepool_name,
        machines,
    )


def aks_agentpool_manual_scale_add(cmd,
                                   client,
                                   resource_group_name,
                                   cluster_name,
                                   nodepool_name,
                                   vm_sizes,
                                   node_count,
                                   no_wait=False):
    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    if instance.type_properties_type != CONST_VIRTUAL_MACHINES:
        raise ClientRequestError("Cannot add manual to a non-virtualmachines node pool.")
    ManualScaleProfile = cmd.get_models(
        "ManualScaleProfile",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_clusters",
    )
    sizes = [x.strip() for x in vm_sizes.split(",")]
    if len(sizes) != 1:
        raise ClientRequestError("We only accept single sku size for manual profile.")
    new_manual_scale_profile = ManualScaleProfile(size=sizes[0], count=int(node_count))
    instance.virtual_machines_profile.scale.manual.append(new_manual_scale_profile)

    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        nodepool_name,
        instance
    )


def aks_agentpool_manual_scale_update(cmd,    # pylint: disable=unused-argument
                                      client,
                                      resource_group_name,
                                      cluster_name,
                                      nodepool_name,
                                      current_vm_sizes,
                                      vm_sizes=None,
                                      node_count=None,
                                      no_wait=False):
    if vm_sizes is None and node_count is None:
        raise RequiredArgumentMissingError("specify --vm-sizes or --node-count or both.")

    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    if instance.type_properties_type != CONST_VIRTUAL_MACHINES:
        raise ClientRequestError("Cannot update manual in a non-virtualmachines node pool.")

    _current_vm_sizes = [x.strip() for x in current_vm_sizes.split(",")]
    if len(_current_vm_sizes) != 1:
        raise InvalidArgumentValueError(
            f"We only accept single sku size for manual profile. {current_vm_sizes} is invalid."
        )
    _vm_sizes = [x.strip() for x in vm_sizes.split(",")] if vm_sizes else []
    if len(_vm_sizes) != 1:
        raise InvalidArgumentValueError(f"We only accept single sku size for manual profile. {vm_sizes} is invalid.")
    manual_exists = False
    for m in instance.virtual_machines_profile.scale.manual:
        if m.size == _current_vm_sizes[0]:
            manual_exists = True
            if vm_sizes:
                m.size = _vm_sizes[0]
            if node_count:
                m.count = int(node_count)
            break
    if not manual_exists:
        raise InvalidArgumentValueError(
            f"Manual with size {current_vm_sizes[0]} doesn't exist in node pool {nodepool_name}"
        )

    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        nodepool_name,
        instance
    )


def aks_agentpool_manual_scale_delete(cmd,    # pylint: disable=unused-argument
                                      client,
                                      resource_group_name,
                                      cluster_name,
                                      nodepool_name,
                                      current_vm_sizes,
                                      no_wait=False):
    instance = client.get(resource_group_name, cluster_name, nodepool_name)
    if instance.type_properties_type != CONST_VIRTUAL_MACHINES:
        raise CLIError("Cannot delete manual in a non-virtualmachines node pool.")
    _current_vm_sizes = [x.strip() for x in current_vm_sizes.split(",")]
    if len(_current_vm_sizes) != 1:
        raise InvalidArgumentValueError(
            f"We only accept single sku size for manual profile. {current_vm_sizes} is invalid."
        )
    manual_exists = False
    for m in instance.virtual_machines_profile.scale.manual:
        if m.size == _current_vm_sizes[0]:
            manual_exists = True
            instance.virtual_machines_profile.scale.manual.remove(m)
            break
    if not manual_exists:
        raise InvalidArgumentValueError(
            f"Manual with size {current_vm_sizes[0]} doesn't exist in node pool {nodepool_name}"
        )

    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        nodepool_name,
        instance
    )


def aks_operation_show(cmd,
                       client,
                       resource_group_name,
                       name,
                       nodepool_name,
                       operation_id,):
    if nodepool_name:
        return client.get_by_agent_pool(resource_group_name, name, nodepool_name, operation_id)
    return client.get(resource_group_name, name, operation_id)


def aks_operation_show_latest(cmd,
                              client,
                              resource_group_name,
                              name,
                              nodepool_name,):
    if nodepool_name:
        return client.get_by_agent_pool(resource_group_name, name, nodepool_name, "latest")
    return client.get(resource_group_name, name, "latest")


def aks_operation_abort(cmd,   # pylint: disable=unused-argument
                        client,
                        resource_group_name,
                        name,
                        aks_custom_headers=None,
                        no_wait=False):
    PowerState = cmd.get_models(
        "PowerState",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_clusters",
    )

    instance = client.get(resource_group_name, name)
    power_state = PowerState(code="Running")
    if instance is None:
        raise InvalidArgumentValueError(
            f"Cluster {name} doesnt exist, use 'aks list' to get current cluster list"
        )
    instance.power_state = power_state
    headers = get_aks_custom_headers(aks_custom_headers)
    return sdk_no_wait(no_wait, client.begin_abort_latest_operation, resource_group_name, name, headers=headers)


def aks_machine_list(cmd, client, resource_group_name, cluster_name, nodepool_name):
    return client.list(resource_group_name, cluster_name, nodepool_name)


def aks_machine_show(cmd, client, resource_group_name, cluster_name, nodepool_name, machine_name):
    return client.get(resource_group_name, cluster_name, nodepool_name, machine_name)


def aks_addon_list_available():
    available_addons = []
    for k, v in ADDONS.items():
        available_addons.append({
            "name": k,
            "description": ADDONS_DESCRIPTIONS[v]
        })
    return available_addons


# pylint: disable=unused-argument
def aks_addon_list(cmd, client, resource_group_name, name):
    mc = client.get(resource_group_name, name)
    current_addons = []
    os_type = 'Linux'

    for addon_name, addon_key in ADDONS.items():
        # web_application_routing is a special case, the configuration is stored in a separate profile
        if addon_name == "web_application_routing":
            enabled = bool(
                mc.ingress_profile and
                mc.ingress_profile.web_app_routing and
                mc.ingress_profile.web_app_routing.enabled
            )
        else:
            if addon_name == "virtual-node":
                addon_key += os_type
            enabled = False
            if mc.addon_profiles:
                matching_key = next((key for key in mc.addon_profiles if key.lower() == addon_key.lower()), None)
                if matching_key:
                    enabled = bool(mc.addon_profiles[matching_key].enabled)
        current_addons.append({
            "name": addon_name,
            "api_key": addon_key,
            "enabled": enabled
        })

    return current_addons


# pylint: disable=unused-argument
def aks_addon_show(cmd, client, resource_group_name, name, addon):
    mc = client.get(resource_group_name, name)
    addon_key = ADDONS[addon]

    # web_application_routing is a special case, the configuration is stored in a separate profile
    if addon == "web_application_routing":
        if (
            not mc.ingress_profile and
            not mc.ingress_profile.web_app_routing and
            not mc.ingress_profile.web_app_routing.enabled
        ):
            raise InvalidArgumentValueError(f'Addon "{addon}" is not enabled in this cluster.')
        return {
            "name": addon,
            "api_key": addon_key,
            "config": mc.ingress_profile.web_app_routing,
        }

    # normal addons
    if not mc.addon_profiles or addon_key not in mc.addon_profiles or not mc.addon_profiles[addon_key].enabled:
        raise InvalidArgumentValueError(f'Addon "{addon}" is not enabled in this cluster.')
    return {
        "name": addon,
        "api_key": addon_key,
        "config": mc.addon_profiles[addon_key].config,
        "identity": mc.addon_profiles[addon_key].identity
    }


def aks_addon_enable(
    cmd,
    client,
    resource_group_name,
    name,
    addon,
    workspace_resource_id=None,
    subnet_name=None,
    appgw_name=None,
    appgw_subnet_prefix=None,
    appgw_subnet_cidr=None,
    appgw_id=None,
    appgw_subnet_id=None,
    appgw_watch_namespace=None,
    enable_sgxquotehelper=False,
    enable_secret_rotation=False,
    rotation_poll_interval=None,
    no_wait=False,
    enable_msi_auth_for_monitoring=True,
    dns_zone_resource_id=None,
    dns_zone_resource_ids=None,
    enable_syslog=False,
    data_collection_settings=None,
    ampls_resource_id=None,
    enable_high_log_scale_mode=False
):
    return enable_addons(
        cmd,
        client,
        resource_group_name,
        name,
        addon,
        workspace_resource_id=workspace_resource_id,
        subnet_name=subnet_name,
        appgw_name=appgw_name,
        appgw_subnet_prefix=appgw_subnet_prefix,
        appgw_subnet_cidr=appgw_subnet_cidr,
        appgw_id=appgw_id,
        appgw_subnet_id=appgw_subnet_id,
        appgw_watch_namespace=appgw_watch_namespace,
        enable_sgxquotehelper=enable_sgxquotehelper,
        enable_secret_rotation=enable_secret_rotation,
        rotation_poll_interval=rotation_poll_interval,
        no_wait=no_wait,
        enable_msi_auth_for_monitoring=enable_msi_auth_for_monitoring,
        dns_zone_resource_id=dns_zone_resource_id,
        dns_zone_resource_ids=dns_zone_resource_ids,
        enable_syslog=enable_syslog,
        data_collection_settings=data_collection_settings,
        ampls_resource_id=ampls_resource_id,
        enable_high_log_scale_mode=enable_high_log_scale_mode
    )


def aks_addon_disable(cmd, client, resource_group_name, name, addon, no_wait=False):
    return aks_disable_addons(cmd, client, resource_group_name, name, addon, no_wait)


def aks_addon_update(
    cmd,
    client,
    resource_group_name,
    name,
    addon,
    workspace_resource_id=None,
    subnet_name=None,
    appgw_name=None,
    appgw_subnet_prefix=None,
    appgw_subnet_cidr=None,
    appgw_id=None,
    appgw_subnet_id=None,
    appgw_watch_namespace=None,
    enable_sgxquotehelper=False,
    enable_secret_rotation=False,
    rotation_poll_interval=None,
    no_wait=False,
    enable_msi_auth_for_monitoring=None,
    dns_zone_resource_id=None,
    dns_zone_resource_ids=None,
    enable_syslog=False,
    data_collection_settings=None,
    ampls_resource_id=None,
    enable_high_log_scale_mode=False
):
    instance = client.get(resource_group_name, name)
    addon_profiles = instance.addon_profiles

    if instance.service_principal_profile.client_id != "msi":
        enable_msi_auth_for_monitoring = False

    if addon == "web_application_routing":
        if (
            (instance.ingress_profile is None) or
            (instance.ingress_profile.web_app_routing is None) or
            not instance.ingress_profile.web_app_routing.enabled
        ):
            raise InvalidArgumentValueError(
                f'Addon "{addon}" is not enabled in this cluster.'
            )

    elif addon == "monitoring" and enable_msi_auth_for_monitoring is None:
        enable_msi_auth_for_monitoring = True

    else:
        addon_key = ADDONS[addon]
        if not addon_profiles or addon_key not in addon_profiles or not addon_profiles[addon_key].enabled:
            raise InvalidArgumentValueError(f'Addon "{addon}" is not enabled in this cluster.')

    return enable_addons(
        cmd,
        client,
        resource_group_name,
        name,
        addon,
        check_enabled=False,
        workspace_resource_id=workspace_resource_id,
        subnet_name=subnet_name,
        appgw_name=appgw_name,
        appgw_subnet_prefix=appgw_subnet_prefix,
        appgw_subnet_cidr=appgw_subnet_cidr,
        appgw_id=appgw_id,
        appgw_subnet_id=appgw_subnet_id,
        appgw_watch_namespace=appgw_watch_namespace,
        enable_sgxquotehelper=enable_sgxquotehelper,
        enable_secret_rotation=enable_secret_rotation,
        rotation_poll_interval=rotation_poll_interval,
        no_wait=no_wait,
        enable_msi_auth_for_monitoring=enable_msi_auth_for_monitoring,
        dns_zone_resource_id=dns_zone_resource_id,
        dns_zone_resource_ids=dns_zone_resource_ids,
        enable_syslog=enable_syslog,
        data_collection_settings=data_collection_settings,
        ampls_resource_id=ampls_resource_id,
        enable_high_log_scale_mode=enable_high_log_scale_mode
    )


def aks_disable_addons(cmd, client, resource_group_name, name, addons, no_wait=False):
    instance = client.get(resource_group_name, name)
    subscription_id = get_subscription_id(cmd.cli_ctx)

    try:
        if (
            addons == "monitoring" and
            CONST_MONITORING_ADDON_NAME in instance.addon_profiles and
            instance.addon_profiles[CONST_MONITORING_ADDON_NAME].enabled and
            CONST_MONITORING_USING_AAD_MSI_AUTH in
            instance.addon_profiles[CONST_MONITORING_ADDON_NAME].config and
            str(
                instance.addon_profiles[CONST_MONITORING_ADDON_NAME].config[
                    CONST_MONITORING_USING_AAD_MSI_AUTH
                ]
            ).lower() == "true"
        ):
            # remove the DCR association because otherwise the DCR can't be deleted
            ensure_container_insights_for_monitoring(
                cmd,
                instance.addon_profiles[CONST_MONITORING_ADDON_NAME],
                subscription_id,
                resource_group_name,
                name,
                instance.location,
                remove_monitoring=True,
                aad_route=True,
                create_dcr=False,
                create_dcra=True,
                enable_syslog=False,
                data_collection_settings=None,
                ampls_resource_id=None,
                enable_high_log_scale_mode=False
            )
    except TypeError:
        pass

    instance = _update_addons(
        cmd,
        instance,
        subscription_id,
        resource_group_name,
        name,
        addons,
        enable=False,
        no_wait=no_wait
    )

    # send the managed cluster representation to update the addon profiles
    return sdk_no_wait(no_wait, client.begin_create_or_update, resource_group_name, name, instance)


def aks_enable_addons(
    cmd,
    client,
    resource_group_name,
    name,
    addons,
    workspace_resource_id=None,
    subnet_name=None,
    appgw_name=None,
    appgw_subnet_prefix=None,
    appgw_subnet_cidr=None,
    appgw_id=None,
    appgw_subnet_id=None,
    appgw_watch_namespace=None,
    enable_sgxquotehelper=False,
    enable_secret_rotation=False,
    rotation_poll_interval=None,
    no_wait=False,
    enable_msi_auth_for_monitoring=True,
    dns_zone_resource_id=None,
    dns_zone_resource_ids=None,
    enable_syslog=False,
    data_collection_settings=None,
    ampls_resource_id=None,
    enable_high_log_scale_mode=False,
    aks_custom_headers=None,
):
    headers = get_aks_custom_headers(aks_custom_headers)
    instance = client.get(resource_group_name, name)
    # this is overwritten by _update_addons(), so the value needs to be recorded here
    msi_auth = False
    if instance.service_principal_profile.client_id == "msi":
        msi_auth = True
    else:
        enable_msi_auth_for_monitoring = False

    subscription_id = get_subscription_id(cmd.cli_ctx)

    is_private_cluster = False
    if instance.api_server_access_profile and instance.api_server_access_profile.enable_private_cluster:
        is_private_cluster = True

    instance = _update_addons(
        cmd,
        instance,
        subscription_id,
        resource_group_name,
        name,
        addons,
        enable=True,
        workspace_resource_id=workspace_resource_id,
        enable_msi_auth_for_monitoring=enable_msi_auth_for_monitoring,
        subnet_name=subnet_name,
        appgw_name=appgw_name,
        appgw_subnet_prefix=appgw_subnet_prefix,
        appgw_subnet_cidr=appgw_subnet_cidr,
        appgw_id=appgw_id,
        appgw_subnet_id=appgw_subnet_id,
        appgw_watch_namespace=appgw_watch_namespace,
        enable_sgxquotehelper=enable_sgxquotehelper,
        enable_secret_rotation=enable_secret_rotation,
        rotation_poll_interval=rotation_poll_interval,
        no_wait=no_wait,
        dns_zone_resource_id=dns_zone_resource_id,
        dns_zone_resource_ids=dns_zone_resource_ids,
    )

    is_monitoring_addon_enabled = check_is_monitoring_addon_enabled(addons, instance)
    if (
        is_monitoring_addon_enabled
    ):
        if (
            CONST_MONITORING_USING_AAD_MSI_AUTH in
            instance.addon_profiles[CONST_MONITORING_ADDON_NAME].config and
            str(
                instance.addon_profiles[CONST_MONITORING_ADDON_NAME].config[
                    CONST_MONITORING_USING_AAD_MSI_AUTH
                ]
            ).lower() == "true"
        ):
            if not msi_auth:
                raise ArgumentUsageError(
                    "--enable-msi-auth-for-monitoring can not be used on clusters with service principal auth.")
            # create a Data Collection Rule (DCR) and associate it with the cluster
            ensure_container_insights_for_monitoring(
                cmd,
                instance.addon_profiles[CONST_MONITORING_ADDON_NAME],
                subscription_id,
                resource_group_name,
                name,
                instance.location,
                aad_route=True,
                create_dcr=True,
                create_dcra=True,
                enable_syslog=enable_syslog,
                data_collection_settings=data_collection_settings,
                is_private_cluster=is_private_cluster,
                ampls_resource_id=ampls_resource_id,
                enable_high_log_scale_mode=enable_high_log_scale_mode
            )
        else:
            # monitoring addon will use legacy path
            if enable_syslog:
                raise ArgumentUsageError(
                    "--enable-syslog can not be used without MSI auth.")
            if enable_high_log_scale_mode:
                raise ArgumentUsageError(
                    "--enable-high-log-scale-mode can not be used without MSI auth.")
            if data_collection_settings is not None:
                raise ArgumentUsageError("--data-collection-settings can not be used without MSI auth.")
            if ampls_resource_id is not None:
                raise ArgumentUsageError("--ampls-resource-id can not be used without MSI auth.")
            ensure_container_insights_for_monitoring(
                cmd,
                instance.addon_profiles[CONST_MONITORING_ADDON_NAME],
                subscription_id,
                resource_group_name,
                name,
                instance.location,
                aad_route=False,
            )

    ingress_appgw_addon_enabled = CONST_INGRESS_APPGW_ADDON_NAME in instance.addon_profiles and instance.addon_profiles[
        CONST_INGRESS_APPGW_ADDON_NAME].enabled

    os_type = 'Linux'
    enable_virtual_node = False
    if CONST_VIRTUAL_NODE_ADDON_NAME + os_type in instance.addon_profiles:
        enable_virtual_node = True

    need_post_creation_role_assignment = (
        is_monitoring_addon_enabled or
        ingress_appgw_addon_enabled or
        enable_virtual_node
    )
    if need_post_creation_role_assignment:
        # adding a wait here since we rely on the result for role assignment
        result = LongRunningOperation(cmd.cli_ctx)(
            client.begin_create_or_update(resource_group_name, name, instance))

        if ingress_appgw_addon_enabled:
            add_ingress_appgw_addon_role_assignment(result, cmd)
        if enable_virtual_node:
            # All agent pool will reside in the same vnet, we will grant vnet level Contributor role
            # in later function, so using a random agent pool here is OK
            random_agent_pool = result.agent_pool_profiles[0]
            if random_agent_pool.vnet_subnet_id != "":
                add_virtual_node_role_assignment(
                    cmd, result, random_agent_pool.vnet_subnet_id)
            # Else, the cluster is not using custom VNet, the permission is already granted in AKS RP,
            # we don't need to handle it in client side in this case.

    else:
        result = sdk_no_wait(no_wait, client.begin_create_or_update,
                             resource_group_name, name, instance, headers=headers)
    return result


def aks_rotate_certs(cmd, client, resource_group_name, name, no_wait=True):     # pylint: disable=unused-argument
    return sdk_no_wait(no_wait, client.begin_rotate_cluster_certificates, resource_group_name, name)


def _update_addons(cmd,  # pylint: disable=too-many-branches,too-many-statements,
                   instance,
                   subscription_id,
                   resource_group_name,
                   name,
                   addons,
                   enable,
                   workspace_resource_id=None,
                   enable_msi_auth_for_monitoring=True,
                   subnet_name=None,
                   appgw_name=None,
                   appgw_subnet_prefix=None,
                   appgw_subnet_cidr=None,
                   appgw_id=None,
                   appgw_subnet_id=None,
                   appgw_watch_namespace=None,
                   enable_sgxquotehelper=False,
                   enable_secret_rotation=False,
                   disable_secret_rotation=False,
                   rotation_poll_interval=None,
                   dns_zone_resource_id=None,
                   dns_zone_resource_ids=None,
                   no_wait=False,):  # pylint: disable=unused-argument

    ManagedClusterAddonProfile = cmd.get_models(
        "ManagedClusterAddonProfile",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_clusters",
    )
    ManagedClusterIngressProfile = cmd.get_models(
        "ManagedClusterIngressProfile",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_clusters",
    )
    ManagedClusterIngressProfileWebAppRouting = cmd.get_models(
        "ManagedClusterIngressProfileWebAppRouting",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_clusters",
    )

    # parse the comma-separated addons argument
    addon_args = addons.split(',')

    addon_profiles = instance.addon_profiles or {}

    os_type = 'Linux'

    # for each addons argument
    for addon_arg in addon_args:
        if addon_arg == "web_application_routing":
            # web app routing settings are in ingress profile, not addon profile, so deal
            # with it separately
            if instance.ingress_profile is None:
                instance.ingress_profile = ManagedClusterIngressProfile()
            if instance.ingress_profile.web_app_routing is None:
                instance.ingress_profile.web_app_routing = ManagedClusterIngressProfileWebAppRouting()
            instance.ingress_profile.web_app_routing.enabled = enable

            if dns_zone_resource_ids is not None:
                instance.ingress_profile.web_app_routing.dns_zone_resource_ids = [
                    x.strip()
                    for x in (
                        dns_zone_resource_ids.split(",")
                        if dns_zone_resource_ids
                        else []
                    )
                ]
            # for backward compatibility, if --dns-zone-resource-ids is not specified,
            # try to read from --dns-zone-resource-id
            if not instance.ingress_profile.web_app_routing.dns_zone_resource_ids and dns_zone_resource_id:
                instance.ingress_profile.web_app_routing.dns_zone_resource_ids = [dns_zone_resource_id]
            continue

        if addon_arg not in ADDONS:
            raise CLIError(f"Invalid addon name: {addon_arg}.")
        addon = ADDONS[addon_arg]
        if addon == CONST_VIRTUAL_NODE_ADDON_NAME:
            # only linux is supported for now, in the future this will be a user flag
            addon += os_type

        # honor addon names defined in Azure CLI
        for key in list(addon_profiles):
            if key.lower() == addon.lower() and key != addon:
                addon_profiles[addon] = addon_profiles.pop(key)

        if enable:
            # add new addons or update existing ones and enable them
            addon_profile = addon_profiles.get(
                addon, ManagedClusterAddonProfile(enabled=False))
            # special config handling for certain addons
            if addon == CONST_MONITORING_ADDON_NAME:
                logAnalyticsConstName = CONST_MONITORING_LOG_ANALYTICS_WORKSPACE_RESOURCE_ID
                if addon_profile.enabled:
                    raise CLIError('The monitoring addon is already enabled for this managed cluster.\n'
                                   'To change monitoring configuration, run "az aks disable-addons -a monitoring"'
                                   'before enabling it again.')
                if not workspace_resource_id:
                    workspace_resource_id = ensure_default_log_analytics_workspace_for_monitoring(
                        cmd,
                        subscription_id,
                        resource_group_name)
                workspace_resource_id = sanitize_loganalytics_ws_resource_id(
                    workspace_resource_id)

                cloud_name = cmd.cli_ctx.cloud.name
                if enable_msi_auth_for_monitoring and (cloud_name.lower() == 'ussec' or cloud_name.lower() == 'usnat'):
                    if (
                        instance.identity is not None and
                        instance.identity.type is not None and
                        instance.identity.type == "userassigned"
                    ):
                        logger.warning(
                            "--enable_msi_auth_for_monitoring is not supported in %s cloud and continuing "
                            "monitoring enablement without this flag.",
                            cloud_name,
                        )
                        enable_msi_auth_for_monitoring = False

                addon_profile.config = {
                    logAnalyticsConstName: workspace_resource_id}
                addon_profile.config[CONST_MONITORING_USING_AAD_MSI_AUTH] = (
                    "true" if enable_msi_auth_for_monitoring else "false"
                )
            elif addon == (CONST_VIRTUAL_NODE_ADDON_NAME + os_type):
                if addon_profile.enabled:
                    raise CLIError('The virtual-node addon is already enabled for this managed cluster.\n'
                                   'To change virtual-node configuration, run '
                                   '"az aks disable-addons -a virtual-node -g {resource_group_name}" '
                                   'before enabling it again.')
                if not subnet_name:
                    raise CLIError(
                        'The aci-connector addon requires setting a subnet name.')
                addon_profile.config = {
                    CONST_VIRTUAL_NODE_SUBNET_NAME: subnet_name}
            elif addon == CONST_INGRESS_APPGW_ADDON_NAME:
                if addon_profile.enabled:
                    raise CLIError('The ingress-appgw addon is already enabled for this managed cluster.\n'
                                   'To change ingress-appgw configuration, run '
                                   f'"az aks disable-addons -a ingress-appgw -n {name} -g {resource_group_name}" '
                                   'before enabling it again.')
                addon_profile = ManagedClusterAddonProfile(
                    enabled=True, config={})
                if appgw_name is not None:
                    addon_profile.config[CONST_INGRESS_APPGW_APPLICATION_GATEWAY_NAME] = appgw_name
                if appgw_subnet_prefix is not None:
                    addon_profile.config[CONST_INGRESS_APPGW_SUBNET_CIDR] = appgw_subnet_prefix
                if appgw_subnet_cidr is not None:
                    addon_profile.config[CONST_INGRESS_APPGW_SUBNET_CIDR] = appgw_subnet_cidr
                if appgw_id is not None:
                    addon_profile.config[CONST_INGRESS_APPGW_APPLICATION_GATEWAY_ID] = appgw_id
                if appgw_subnet_id is not None:
                    addon_profile.config[CONST_INGRESS_APPGW_SUBNET_ID] = appgw_subnet_id
                if appgw_watch_namespace is not None:
                    addon_profile.config[CONST_INGRESS_APPGW_WATCH_NAMESPACE] = appgw_watch_namespace
            elif addon == CONST_OPEN_SERVICE_MESH_ADDON_NAME:
                if addon_profile.enabled:
                    raise CLIError('The open-service-mesh addon is already enabled for this managed cluster.\n'
                                   'To change open-service-mesh configuration, run '
                                   f'"az aks disable-addons -a open-service-mesh -n {name} -g {resource_group_name}" '
                                   'before enabling it again.')
                addon_profile = ManagedClusterAddonProfile(
                    enabled=True, config={})
            elif addon == CONST_CONFCOM_ADDON_NAME:
                if addon_profile.enabled:
                    raise CLIError('The confcom addon is already enabled for this managed cluster.\n'
                                   'To change confcom configuration, run '
                                   f'"az aks disable-addons -a confcom -n {name} -g {resource_group_name}" '
                                   'before enabling it again.')
                addon_profile = ManagedClusterAddonProfile(
                    enabled=True, config={CONST_ACC_SGX_QUOTE_HELPER_ENABLED: "false"})
                if enable_sgxquotehelper:
                    addon_profile.config[CONST_ACC_SGX_QUOTE_HELPER_ENABLED] = "true"
            elif addon == CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME:
                if addon_profile.enabled:
                    raise CLIError(
                        "The azure-keyvault-secrets-provider addon is already enabled for this managed cluster.\n"
                        'To change azure-keyvault-secrets-provider configuration, run "az aks disable-addons '
                        f'-a azure-keyvault-secrets-provider -n {name} -g {resource_group_name}" '
                        "before enabling it again."
                    )
                addon_profile = ManagedClusterAddonProfile(
                    enabled=True, config={CONST_SECRET_ROTATION_ENABLED: "false", CONST_ROTATION_POLL_INTERVAL: "2m"})
                if enable_secret_rotation:
                    addon_profile.config[CONST_SECRET_ROTATION_ENABLED] = "true"
                if disable_secret_rotation:
                    addon_profile.config[CONST_SECRET_ROTATION_ENABLED] = "false"
                if rotation_poll_interval is not None:
                    addon_profile.config[CONST_ROTATION_POLL_INTERVAL] = rotation_poll_interval
                addon_profiles[CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME] = addon_profile
            addon_profiles[addon] = addon_profile
        else:
            if addon not in addon_profiles:
                if addon == CONST_KUBE_DASHBOARD_ADDON_NAME:
                    addon_profiles[addon] = ManagedClusterAddonProfile(
                        enabled=False)
                else:
                    raise CLIError(f"The addon {addon} is not installed.")
            addon_profiles[addon].config = None
        addon_profiles[addon].enabled = enable

    instance.addon_profiles = addon_profiles

    # null out the SP profile because otherwise validation complains
    instance.service_principal_profile = None

    return instance


def aks_get_versions(cmd, client, location):    # pylint: disable=unused-argument
    return client.list_kubernetes_versions(location)


def get_aks_custom_headers(aks_custom_headers=None):
    headers = {}
    if aks_custom_headers is not None:
        if aks_custom_headers != "":
            for pair in aks_custom_headers.split(','):
                parts = pair.split('=')
                if len(parts) != 2:
                    raise CLIError('custom headers format is incorrect')
                headers[parts[0]] = parts[1]
    return headers


def aks_draft_create(destination='.',
                     app=None,
                     language=None,
                     create_config=None,
                     dockerfile_only=None,
                     deployment_only=None,
                     path=None):
    aks_draft_cmd_create(destination, app, language, create_config, dockerfile_only, deployment_only, path)


def aks_draft_setup_gh(app=None,
                       subscription_id=None,
                       resource_group=None,
                       provider="azure",
                       gh_repo=None,
                       path=None):
    aks_draft_cmd_setup_gh(app, subscription_id, resource_group, provider, gh_repo, path)


def aks_draft_generate_workflow(cluster_name=None,
                                registry_name=None,
                                container_name=None,
                                resource_group=None,
                                destination=None,
                                branch=None,
                                path=None):
    aks_draft_cmd_generate_workflow(cluster_name, registry_name, container_name,
                                    resource_group, destination, branch, path)


def aks_draft_up(app=None,
                 subscription_id=None,
                 resource_group=None,
                 provider="azure",
                 gh_repo=None,
                 cluster_name=None,
                 registry_name=None,
                 container_name=None,
                 destination=None,
                 branch=None,
                 path=None):
    aks_draft_cmd_up(app, subscription_id, resource_group, provider, gh_repo,
                     cluster_name, registry_name, container_name, destination, branch, path)


def aks_draft_update(host=None, certificate=None, destination=None, path=None):
    aks_draft_cmd_update(host, certificate, destination, path)


def aks_kollect(cmd,    # pylint: disable=too-many-statements,too-many-locals
                client,
                resource_group_name,
                name,
                storage_account=None,
                sas_token=None,
                container_logs=None,
                kube_objects=None,
                node_logs=None,
                node_logs_windows=None):
    aks_kollect_cmd(cmd, client, resource_group_name, name, storage_account, sas_token,
                    container_logs, kube_objects, node_logs, node_logs_windows)


def aks_kanalyze(cmd, client, resource_group_name, name):
    aks_kanalyze_cmd(cmd, client, resource_group_name, name)


def aks_pod_identity_add(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    identity_name,
    identity_namespace,
    identity_resource_id,
    binding_selector=None,
    no_wait=False,
    aks_custom_headers=None,
):  # pylint: disable=unused-argument
    ManagedClusterPodIdentity = cmd.get_models(
        "ManagedClusterPodIdentity",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_clusters",
    )
    UserAssignedIdentity = cmd.get_models(
        "UserAssignedIdentity",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_clusters",
    )

    instance = client.get(resource_group_name, cluster_name)
    _ensure_pod_identity_addon_is_enabled(instance)

    user_assigned_identity = get_user_assigned_identity_by_resource_id(
        cmd.cli_ctx, identity_resource_id)
    _ensure_managed_identity_operator_permission(
        cmd, instance, user_assigned_identity.id)

    pod_identities = []
    if instance.pod_identity_profile.user_assigned_identities:
        pod_identities = instance.pod_identity_profile.user_assigned_identities
    pod_identity = ManagedClusterPodIdentity(
        name=identity_name,
        namespace=identity_namespace,
        identity=UserAssignedIdentity(
            resource_id=user_assigned_identity.id,
            client_id=user_assigned_identity.client_id,
            object_id=user_assigned_identity.principal_id,
        )
    )
    if binding_selector is not None:
        pod_identity.binding_selector = binding_selector
    pod_identities.append(pod_identity)

    from azext_aks_preview.managed_cluster_decorator import AKSPreviewManagedClusterModels
    # store all the models used by pod identity
    pod_identity_models = AKSPreviewManagedClusterModels(
        cmd, CUSTOM_MGMT_AKS_PREVIEW).pod_identity_models
    _update_addon_pod_identity(
        instance, enable=True,
        pod_identities=pod_identities,
        pod_identity_exceptions=instance.pod_identity_profile.user_assigned_identity_exceptions,
        models=pod_identity_models
    )

    headers = get_aks_custom_headers(aks_custom_headers)
    # send the managed cluster represeentation to update the pod identity addon
    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        instance,
        headers=headers
    )


def aks_pod_identity_delete(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    identity_name,
    identity_namespace,
    no_wait=False,
    aks_custom_headers=None,
):  # pylint: disable=unused-argument
    instance = client.get(resource_group_name, cluster_name)
    _ensure_pod_identity_addon_is_enabled(instance)

    pod_identities = []
    if instance.pod_identity_profile.user_assigned_identities:
        for pod_identity in instance.pod_identity_profile.user_assigned_identities:
            if pod_identity.name == identity_name and pod_identity.namespace == identity_namespace:
                # to remove
                continue
            pod_identities.append(pod_identity)

    from azext_aks_preview.managed_cluster_decorator import AKSPreviewManagedClusterModels
    # store all the models used by pod identity
    pod_identity_models = AKSPreviewManagedClusterModels(
        cmd, CUSTOM_MGMT_AKS_PREVIEW).pod_identity_models
    _update_addon_pod_identity(
        instance, enable=True,
        pod_identities=pod_identities,
        pod_identity_exceptions=instance.pod_identity_profile.user_assigned_identity_exceptions,
        models=pod_identity_models
    )

    headers = get_aks_custom_headers(aks_custom_headers)
    # send the managed cluster represeentation to update the pod identity addon
    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        instance,
        headers=headers
    )


def aks_pod_identity_list(cmd, client, resource_group_name, cluster_name):  # pylint: disable=unused-argument
    instance = client.get(resource_group_name, cluster_name)
    return _remove_nulls([instance])[0]


def aks_pod_identity_exception_add(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    exc_name,
    exc_namespace,
    pod_labels,
    no_wait=False,
    aks_custom_headers=None,
):  # pylint: disable=unused-argument
    ManagedClusterPodIdentityException = cmd.get_models(
        "ManagedClusterPodIdentityException",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_clusters",
    )

    instance = client.get(resource_group_name, cluster_name)
    _ensure_pod_identity_addon_is_enabled(instance)

    pod_identity_exceptions = []
    if instance.pod_identity_profile.user_assigned_identity_exceptions:
        pod_identity_exceptions = instance.pod_identity_profile.user_assigned_identity_exceptions
    exc = ManagedClusterPodIdentityException(
        name=exc_name, namespace=exc_namespace, pod_labels=pod_labels)
    pod_identity_exceptions.append(exc)

    from azext_aks_preview.managed_cluster_decorator import AKSPreviewManagedClusterModels
    # store all the models used by pod identity
    pod_identity_models = AKSPreviewManagedClusterModels(
        cmd, CUSTOM_MGMT_AKS_PREVIEW).pod_identity_models
    _update_addon_pod_identity(
        instance, enable=True,
        pod_identities=instance.pod_identity_profile.user_assigned_identities,
        pod_identity_exceptions=pod_identity_exceptions,
        models=pod_identity_models
    )

    headers = get_aks_custom_headers(aks_custom_headers)
    # send the managed cluster represeentation to update the pod identity addon
    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        instance,
        headers=headers
    )


def aks_pod_identity_exception_delete(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    exc_name,
    exc_namespace,
    no_wait=False,
    aks_custom_headers=None,
):  # pylint: disable=unused-argument
    instance = client.get(resource_group_name, cluster_name)
    _ensure_pod_identity_addon_is_enabled(instance)

    pod_identity_exceptions = []
    if instance.pod_identity_profile.user_assigned_identity_exceptions:
        for exc in instance.pod_identity_profile.user_assigned_identity_exceptions:
            if exc.name == exc_name and exc.namespace == exc_namespace:
                # to remove
                continue
            pod_identity_exceptions.append(exc)

    from azext_aks_preview.managed_cluster_decorator import AKSPreviewManagedClusterModels
    # store all the models used by pod identity
    pod_identity_models = AKSPreviewManagedClusterModels(
        cmd, CUSTOM_MGMT_AKS_PREVIEW).pod_identity_models
    _update_addon_pod_identity(
        instance, enable=True,
        pod_identities=instance.pod_identity_profile.user_assigned_identities,
        pod_identity_exceptions=pod_identity_exceptions,
        models=pod_identity_models
    )

    headers = get_aks_custom_headers(aks_custom_headers)
    # send the managed cluster represeentation to update the pod identity addon
    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        instance,
        headers=headers
    )


def aks_pod_identity_exception_update(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    exc_name,
    exc_namespace,
    pod_labels,
    no_wait=False,
    aks_custom_headers=None,
):  # pylint: disable=unused-argument
    ManagedClusterPodIdentityException = cmd.get_models(
        "ManagedClusterPodIdentityException",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_clusters",
    )

    instance = client.get(resource_group_name, cluster_name)
    _ensure_pod_identity_addon_is_enabled(instance)

    found_target = False
    updated_exc = ManagedClusterPodIdentityException(
        name=exc_name, namespace=exc_namespace, pod_labels=pod_labels)
    pod_identity_exceptions = []
    if instance.pod_identity_profile.user_assigned_identity_exceptions:
        for exc in instance.pod_identity_profile.user_assigned_identity_exceptions:
            if exc.name == exc_name and exc.namespace == exc_namespace:
                found_target = True
                pod_identity_exceptions.append(updated_exc)
            else:
                pod_identity_exceptions.append(exc)

    if not found_target:
        raise CLIError(f"pod identity exception {exc_namespace}/{exc_name} not found")

    from azext_aks_preview.managed_cluster_decorator import AKSPreviewManagedClusterModels
    # store all the models used by pod identity
    pod_identity_models = AKSPreviewManagedClusterModels(
        cmd, CUSTOM_MGMT_AKS_PREVIEW).pod_identity_models
    _update_addon_pod_identity(
        instance, enable=True,
        pod_identities=instance.pod_identity_profile.user_assigned_identities,
        pod_identity_exceptions=pod_identity_exceptions,
        models=pod_identity_models
    )

    headers = get_aks_custom_headers(aks_custom_headers)
    # send the managed cluster represeentation to update the pod identity addon
    return sdk_no_wait(
        no_wait,
        client.begin_create_or_update,
        resource_group_name,
        cluster_name,
        instance,
        headers=headers,
    )


def aks_pod_identity_exception_list(cmd, client, resource_group_name, cluster_name):
    instance = client.get(resource_group_name, cluster_name)
    return _remove_nulls([instance])[0]


def aks_egress_endpoints_list(cmd, client, resource_group_name, name):   # pylint: disable=unused-argument
    return client.list_outbound_network_dependencies_endpoints(resource_group_name, name)


def aks_snapshot_create(cmd,    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
                        client,
                        resource_group_name,
                        name,
                        cluster_id,
                        location=None,
                        tags=None,
                        aks_custom_headers=None,
                        no_wait=False):
    ManagedClusterSnapshot = cmd.get_models(
        "ManagedClusterSnapshot",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_cluster_snapshots",
    )
    CreationData = cmd.get_models(
        "CreationData",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_clusters",
    )

    rg_location = get_rg_location(cmd.cli_ctx, resource_group_name)
    if location is None:
        location = rg_location

    creationData = CreationData(
        source_resource_id=cluster_id
    )

    snapshot = ManagedClusterSnapshot(
        name=name,
        tags=tags,
        location=location,
        creation_data=creationData,
        snapshot_type="ManagedCluster",
    )

    headers = get_aks_custom_headers(aks_custom_headers)
    return client.create_or_update(resource_group_name, name, snapshot, headers=headers)


def aks_snapshot_show(cmd, client, resource_group_name, name):   # pylint: disable=unused-argument
    snapshot = client.get(resource_group_name, name)
    return snapshot


def aks_snapshot_delete(cmd,    # pylint: disable=unused-argument
                        client,
                        resource_group_name,
                        name,
                        no_wait=False,
                        yes=False):
    msg = (
        f'This will delete the cluster snapshot "{name}" in resource group "{resource_group_name}".\n'
        "Are you sure?"
    )
    if not yes and not prompt_y_n(msg, default="n"):
        return None

    return client.delete(resource_group_name, name)


def aks_snapshot_list(cmd, client, resource_group_name=None):  # pylint: disable=unused-argument
    if resource_group_name is None or resource_group_name == '':
        return client.list()

    return client.list_by_resource_group(resource_group_name)


def aks_nodepool_snapshot_create(cmd,    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
                                 client,
                                 resource_group_name,
                                 snapshot_name,
                                 nodepool_id,
                                 location=None,
                                 tags=None,
                                 aks_custom_headers=None,
                                 no_wait=False):
    Snapshot = cmd.get_models(
        "Snapshot",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="snapshots",
    )
    CreationData = cmd.get_models(
        "CreationData",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="managed_clusters",
    )

    rg_location = get_rg_location(cmd.cli_ctx, resource_group_name)
    if location is None:
        location = rg_location

    creationData = CreationData(
        source_resource_id=nodepool_id
    )

    snapshot = Snapshot(
        name=snapshot_name,
        tags=tags,
        location=location,
        creation_data=creationData
    )

    headers = get_aks_custom_headers(aks_custom_headers)
    return client.create_or_update(resource_group_name, snapshot_name, snapshot, headers=headers)


def aks_nodepool_snapshot_update(cmd, client, resource_group_name, snapshot_name, tags):   # pylint: disable=unused-argument
    TagsObject = cmd.get_models(
        "TagsObject",
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
        operation_group="snapshots",
    )
    tagsObject = TagsObject(
        tags=tags
    )

    snapshot = client.update_tags(resource_group_name, snapshot_name, tagsObject)
    return snapshot


def aks_nodepool_snapshot_show(cmd, client, resource_group_name, snapshot_name):   # pylint: disable=unused-argument
    snapshot = client.get(resource_group_name, snapshot_name)
    return snapshot


def aks_nodepool_snapshot_delete(cmd,    # pylint: disable=unused-argument
                                 client,
                                 resource_group_name,
                                 snapshot_name,
                                 no_wait=False,
                                 yes=False):
    msg = (
        f'This will delete the nodepool snapshot "{snapshot_name}" in resource group "{resource_group_name}".\n'
        "Are you sure?"
    )
    if not yes and not prompt_y_n(msg, default="n"):
        return None

    return client.delete(resource_group_name, snapshot_name)


def aks_nodepool_snapshot_list(cmd, client, resource_group_name=None):  # pylint: disable=unused-argument
    if resource_group_name is None or resource_group_name == '':
        return client.list()

    return client.list_by_resource_group(resource_group_name)


def aks_mesh_enable(
    cmd,
    client,
    resource_group_name,
    name,
    revision=None,
    key_vault_id=None,
    ca_cert_object_name=None,
    ca_key_object_name=None,
    root_cert_object_name=None,
    cert_chain_object_name=None,
):
    instance = client.get(resource_group_name, name)
    addon_profiles = instance.addon_profiles
    if (
        key_vault_id is not None and
        ca_cert_object_name is not None and
        ca_key_object_name is not None and
        root_cert_object_name is not None and
        cert_chain_object_name is not None
    ):
        if (
            not addon_profiles or
            not addon_profiles[CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME] or
            not addon_profiles[
                CONST_AZURE_KEYVAULT_SECRETS_PROVIDER_ADDON_NAME
            ].enabled
        ):
            raise CLIError(
                "AzureKeyvaultSecretsProvider addon is required for Azure Service Mesh plugin "
                "certificate authority feature."
            )

    return _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        key_vault_id,
        ca_cert_object_name,
        ca_key_object_name,
        root_cert_object_name,
        cert_chain_object_name,
        revision=revision,
        enable_azure_service_mesh=True,
    )


def aks_mesh_disable(
        cmd,
        client,
        resource_group_name,
        name,
):
    return _aks_mesh_update(cmd, client, resource_group_name, name, disable_azure_service_mesh=True)


def aks_mesh_enable_ingress_gateway(
        cmd,
        client,
        resource_group_name,
        name,
        ingress_gateway_type,
):
    return _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        enable_ingress_gateway=True,
        ingress_gateway_type=ingress_gateway_type)


def aks_mesh_disable_ingress_gateway(
        cmd,
        client,
        resource_group_name,
        name,
        ingress_gateway_type,
):
    return _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        disable_ingress_gateway=True,
        ingress_gateway_type=ingress_gateway_type)


def aks_mesh_enable_egress_gateway(
        cmd,
        client,
        resource_group_name,
        name,
        istio_egressgateway_name,
        istio_egressgateway_namespace,
        gateway_configuration_name,
):
    return _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        enable_egress_gateway=True,
        istio_egressgateway_name=istio_egressgateway_name,
        istio_egressgateway_namespace=istio_egressgateway_namespace,
        gateway_configuration_name=gateway_configuration_name)


def aks_mesh_disable_egress_gateway(
        cmd,
        client,
        resource_group_name,
        name,
        istio_egressgateway_name,
        istio_egressgateway_namespace,
):
    return _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        istio_egressgateway_name=istio_egressgateway_name,
        istio_egressgateway_namespace=istio_egressgateway_namespace,
        disable_egress_gateway=True)


def aks_mesh_get_revisions(
        cmd,
        client,
        location
):
    revisonProfiles = client.list_mesh_revision_profiles(location)
    # 'revisonProfiles' is an ItemPaged object
    revisions = []
    # Iterate over items within pages
    for page in revisonProfiles.by_page():
        for item in page:
            revisions.append(item)

    if revisions:
        return revisions[0].properties
    return None


def check_iterator(iterator):
    import itertools
    try:
        first = next(iterator)
    except StopIteration:   # iterator is empty
        return True, iterator
    except TypeError:       # iterator is not iterable, e.g. None
        return True, iterator
    return False, itertools.chain([first], iterator)


def aks_mesh_get_upgrades(
        cmd,
        client,
        resource_group_name,
        name
):
    upgradeProfiles = client.list_mesh_upgrade_profiles(resource_group_name, name)
    is_empty, upgradeProfiles = check_iterator(upgradeProfiles)
    if is_empty:
        logger.warning("No mesh upgrade profiles found for the cluster '%s' " +
                       "in the resource group '%s'.", name, resource_group_name)
        return None
    upgrade = next(upgradeProfiles, None)
    if upgrade:
        return upgrade.properties
    return None


def aks_mesh_upgrade_start(
        cmd,
        client,
        resource_group_name,
        name,
        revision
):
    return _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        revision=revision,
        mesh_upgrade_command=CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_START)


def aks_mesh_upgrade_complete(
        cmd,
        client,
        resource_group_name,
        name,
        yes=False
):
    return _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        yes=yes,
        mesh_upgrade_command=CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_COMPLETE)


def aks_mesh_upgrade_rollback(
        cmd,
        client,
        resource_group_name,
        name,
        yes=False
):
    return _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        yes=yes,
        mesh_upgrade_command=CONST_AZURE_SERVICE_MESH_UPGRADE_COMMAND_ROLLBACK)


def _aks_mesh_get_supported_revisions(
        cmd,
        client,
        location):

    revisions = aks_mesh_get_revisions(cmd, client, location)
    supported_revisions = [r.revision for r in revisions.mesh_revisions]
    return supported_revisions


# pylint: disable=unused-argument
def _aks_mesh_update(
        cmd,
        client,
        resource_group_name,
        name,
        key_vault_id=None,
        ca_cert_object_name=None,
        ca_key_object_name=None,
        root_cert_object_name=None,
        cert_chain_object_name=None,
        enable_azure_service_mesh=None,
        disable_azure_service_mesh=None,
        enable_ingress_gateway=None,
        disable_ingress_gateway=None,
        ingress_gateway_type=None,
        enable_egress_gateway=None,
        disable_egress_gateway=None,
        istio_egressgateway_name=None,
        istio_egressgateway_namespace=None,
        gateway_configuration_name=None,
        revision=None,
        yes=False,
        mesh_upgrade_command=None,
):
    raw_parameters = locals()

    from azure.cli.command_modules.acs._consts import DecoratorEarlyExitException
    from azext_aks_preview.managed_cluster_decorator import AKSPreviewManagedClusterUpdateDecorator

    aks_update_decorator = AKSPreviewManagedClusterUpdateDecorator(
        cmd=cmd,
        client=client,
        raw_parameters=raw_parameters,
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
    )
    try:
        mc = aks_update_decorator.fetch_mc()
        mc = aks_update_decorator.update_azure_service_mesh_profile(mc)

        # check for unsupported asm revision once the smp in mc object has been updated
        # skip the warning incase upgrade is in progress
        service_mesh_profile = mc.service_mesh_profile
        if (
            service_mesh_profile
            and service_mesh_profile.mode == CONST_AZURE_SERVICE_MESH_MODE_ISTIO
            and service_mesh_profile.istio
            and service_mesh_profile.istio.revisions
            and len(service_mesh_profile.istio.revisions) == 1
        ):
            revision = service_mesh_profile.istio.revisions[0]
            supported_revisions = _aks_mesh_get_supported_revisions(cmd, client, mc.location)
            if revision not in supported_revisions:
                msg = (
                    f"Istio mesh revision {revision} currently in use in your cluster is no longer supported.\n"
                    "Please upgrade for continued support. Use `az aks mesh get-upgrades` to check for available "
                    "upgrades.\nMore information about mesh upgrades and version support can be found here:"
                    " https://aka.ms/asm-aks-upgrade-docs"
                )
                logger.warning(msg)

    except DecoratorEarlyExitException:
        return None

    return aks_update_decorator.update_mc(mc)


def aks_approuting_enable(
        cmd,
        client,
        resource_group_name,
        name,
        enable_kv=False,
        keyvault_id=None,
        nginx=None,
):
    return _aks_approuting_update(
        cmd,
        client,
        resource_group_name,
        name,
        enable_app_routing=True,
        keyvault_id=keyvault_id,
        enable_kv=enable_kv,
        nginx=nginx)


def aks_approuting_disable(
        cmd,
        client,
        resource_group_name,
        name
):
    return _aks_approuting_update(
        cmd,
        client,
        resource_group_name,
        name,
        enable_app_routing=False)


def aks_approuting_update(
        cmd,
        client,
        resource_group_name,
        name,
        keyvault_id=None,
        enable_kv=False,
        nginx=None
):
    return _aks_approuting_update(
        cmd,
        client,
        resource_group_name,
        name,
        keyvault_id=keyvault_id,
        enable_kv=enable_kv,
        nginx=nginx)


def aks_approuting_zone_add(
        cmd,
        client,
        resource_group_name,
        name,
        dns_zone_resource_ids,
        attach_zones=False
):
    return _aks_approuting_update(
        cmd,
        client,
        resource_group_name,
        name,
        dns_zone_resource_ids=dns_zone_resource_ids,
        add_dns_zone=True,
        attach_zones=attach_zones)


def aks_approuting_zone_delete(
        cmd,
        client,
        resource_group_name,
        name,
        dns_zone_resource_ids
):
    return _aks_approuting_update(
        cmd,
        client,
        resource_group_name,
        name,
        dns_zone_resource_ids=dns_zone_resource_ids,
        delete_dns_zone=True)


def aks_approuting_zone_update(
        cmd,
        client,
        resource_group_name,
        name,
        dns_zone_resource_ids,
        attach_zones=False
):
    return _aks_approuting_update(
        cmd,
        client,
        resource_group_name,
        name,
        dns_zone_resource_ids=dns_zone_resource_ids,
        update_dns_zone=True,
        attach_zones=attach_zones)


def aks_approuting_zone_list(
        cmd,
        client,
        resource_group_name,
        name
):
    from azure.mgmt.core.tools import parse_resource_id
    mc = client.get(resource_group_name, name)

    if mc.ingress_profile and mc.ingress_profile.web_app_routing and mc.ingress_profile.web_app_routing.enabled:
        if mc.ingress_profile.web_app_routing.dns_zone_resource_ids:
            dns_zone_resource_ids = mc.ingress_profile.web_app_routing.dns_zone_resource_ids
            dns_zone_list = []
            for dns_zone in dns_zone_resource_ids:
                dns_zone_dict = {}
                parsed_dns_zone = parse_resource_id(dns_zone)
                dns_zone_dict['id'] = dns_zone
                dns_zone_dict['subscription'] = parsed_dns_zone['subscription']
                dns_zone_dict['resource_group'] = parsed_dns_zone['resource_group']
                dns_zone_dict['name'] = parsed_dns_zone['name']
                dns_zone_dict['type'] = parsed_dns_zone['type']
                dns_zone_list.append(dns_zone_dict)
            return dns_zone_list
        raise CLIError('No dns zone attached to the cluster')
    raise CLIError('App routing addon is not enabled')


# pylint: disable=unused-argument
def _aks_approuting_update(
        cmd,
        client,
        resource_group_name,
        name,
        enable_app_routing=None,
        enable_kv=None,
        keyvault_id=None,
        add_dns_zone=None,
        delete_dns_zone=None,
        update_dns_zone=None,
        dns_zone_resource_ids=None,
        attach_zones=None,
        nginx=None
):
    from azure.cli.command_modules.acs._consts import DecoratorEarlyExitException
    from azext_aks_preview.managed_cluster_decorator import AKSPreviewManagedClusterUpdateDecorator

    raw_parameters = locals()

    aks_update_decorator = AKSPreviewManagedClusterUpdateDecorator(
        cmd=cmd,
        client=client,
        raw_parameters=raw_parameters,
        resource_type=CUSTOM_MGMT_AKS_PREVIEW,
    )

    try:
        mc = aks_update_decorator.fetch_mc()
        mc = aks_update_decorator.update_app_routing_profile(mc)
    except DecoratorEarlyExitException:
        return None

    return aks_update_decorator.update_mc(mc)


def _aks_run_command(
        cmd,
        vm_set_type,
        managed_resource_group,
        vmss_name=None,
        instance_id=None,
        vm_name=None,
        custom_endpoints=None):
    try:
        command = "bash /opt/azure/containers/aks-check-network.sh"
        if custom_endpoints:
            all_endpoints = ",".join(custom_endpoints)
            command += f" {all_endpoints}"
            logger.debug("Full command: %s", command)

        compute_client = get_compute_client(cmd.cli_ctx)

        if vm_set_type == CONST_VIRTUAL_MACHINE_SCALE_SETS:
            RunCommandInput = cmd.get_models('RunCommandInput',
                                             resource_type=ResourceType.MGMT_COMPUTE,
                                             operation_group="virtual_machine_scale_sets")
            command_result = LongRunningOperation(cmd.cli_ctx)(
                compute_client.virtual_machine_scale_set_vms.begin_run_command(
                    managed_resource_group, vmss_name, instance_id,
                    RunCommandInput(command_id="RunShellScript", script=[command])))
        elif vm_set_type == CONST_AVAILABILITY_SET:
            RunCommandInput = cmd.get_models('RunCommandInput',
                                             resource_type=ResourceType.MGMT_COMPUTE,
                                             operation_group="virtual_machine_run_commands")
            command_result = LongRunningOperation(cmd.cli_ctx)(
                compute_client.virtual_machines.begin_run_command(
                    managed_resource_group, vm_name,
                    RunCommandInput(command_id="RunShellScript", script=[command])))
        else:
            raise ValidationError(f"VM set type {vm_set_type} is not supported!")

        display_status = command_result.value[0].display_status
        message = command_result.value[0].message
        if display_status != "Provisioning succeeded":
            raise InvalidArgumentValueError(
                f"Can not run command with returned code {display_status} and message {message}")
        return process_message_for_run_command(message)
    except Exception as ex:
        raise HttpResponseError(f"Can not run command with returned exception {ex}") from ex


def _aks_verify_resource(resource, resource_type):
    if resource.provisioning_state != CONST_NODE_PROVISIONING_STATE_SUCCEEDED:
        raise ValidationError(f"Node pool {resource.name} is in {resource.provisioning_state} state!")

    node_image_version = ""
    os_type = ""
    if resource_type == CONST_VIRTUAL_MACHINE_SCALE_SETS:
        node_image_version = resource.node_image_version
        os_type = resource.os_type
    else:
        node_image_version = resource.storage_profile.image_reference.id
        os_type = resource.storage_profile.os_disk.os_type

    if not os_type or os_type != CONST_DEFAULT_NODE_OS_TYPE:
        raise ValidationError(f"Resource must be of type {CONST_DEFAULT_NODE_OS_TYPE}!")

    if not node_image_version:
        raise ValidationError(f"No image version found for {resource.name}! Cannot verify supported versions.")

    if resource_type == CONST_VIRTUAL_MACHINE_SCALE_SETS:
        version = node_image_version.split("-")[-1]
    else:
        version = node_image_version.split("/")[-1]

    if version < CONST_MIN_NODE_IMAGE_VERSION:
        raise ValidationError(f"Node image version {version} is not supported! "
                              f"Image version must be at least {CONST_MIN_NODE_IMAGE_VERSION}.")


def _aks_get_node_name_vmss(
        cmd,
        resource_group,
        cluster_name,
        node_name,
        managed_resource_group):
    compute_client = get_compute_client(cmd.cli_ctx)

    if not node_name:
        logger.debug("No node name specified, will randomly select a node from the cluster")
        agentpool_client = cf_agent_pools(cmd.cli_ctx)

        nodepool_list = list(aks_agentpool_list(cmd, agentpool_client, resource_group, cluster_name))
        if not nodepool_list:
            raise ValidationError("No node pool found in the cluster!")

        nodepool_name = ""
        for nodepool in nodepool_list:
            try:
                _aks_verify_resource(nodepool, CONST_VIRTUAL_MACHINE_SCALE_SETS)
                nodepool_name = nodepool.name
                logger.debug("Select nodepool: %s", nodepool_name)
                break
            except ValidationError as ex:
                logger.warning(ex)
                continue

        if not nodepool_name:
            raise ValidationError("No suitable node pool found in the cluster.")

        vmss_list = compute_client.virtual_machine_scale_sets.list(managed_resource_group)
        if not vmss_list:
            raise ValidationError(f"No VMSS found in the managed resource group {managed_resource_group}!")

        for vmss in vmss_list:
            vmss_tag = vmss.tags.get("aks-managed-poolName")
            if vmss_tag and vmss_tag == nodepool_name:
                vmss_name = vmss.name
                logger.debug("Select VMSS: %s", vmss_name)
                break
        if not vmss_name:
            raise ValidationError(f"No VMSS pool matched AKS node pool {nodepool_name}!")

        instances = list(compute_client.virtual_machine_scale_set_vms.list(managed_resource_group, vmss_name))
        if not instances:
            raise ValidationError(f"No instances found in the VMSS {vmss_name}!")

        instance_id = instances[0].instance_id
        logger.debug("Select instance id: %s", instance_id)
    else:
        index = node_name.find("vmss")
        if index != -1:
            vmss_name = node_name[:index + 4]
            instance_id = int(node_name[index + 4:], base=36)
            instance_info = compute_client.virtual_machine_scale_set_vms.get(
                managed_resource_group, vmss_name, instance_id)
            if not instance_info:
                raise ValidationError(f"Instance id {instance_id} not found in VMSS {vmss_name}!")
            _aks_verify_resource(instance_info, CONST_VIRTUAL_MACHINES)
        else:
            raise ValidationError(f"Node name {node_name} is invalid!")

    return vmss_name, instance_id


def _aks_get_node_name_as(
        cmd,
        node_name,
        managed_resource_group):
    compute_client = get_compute_client(cmd.cli_ctx)

    if not node_name:
        logger.debug("No node name specified, will randomly select a node from the cluster")

        vm_list = compute_client.virtual_machines.list(managed_resource_group)
        if not vm_list:
            raise ValidationError(f"No VM found in the managed resource group {managed_resource_group}!")

        vm_name = ""
        for vm in vm_list:
            try:
                _aks_verify_resource(vm, CONST_VIRTUAL_MACHINES)
                vm_name = vm.name
                logger.debug("Select VM: %s", vm_name)
                break
            except ValidationError as ex:
                logger.warning(ex)
                continue

        if not vm_name:
            raise ValidationError("No suitable VM found in the managed resource!")
    else:
        vm_name = node_name
        vm_info = compute_client.virtual_machines.get(managed_resource_group, vm_name)
        if not vm_info:
            raise ValidationError(f"VM {vm_name} not found in the managed resource group {managed_resource_group}!")
        _aks_verify_resource(vm_info, CONST_VIRTUAL_MACHINES)

    return vm_name


def aks_check_network_outbound(
        cmd,
        client,
        resource_group_name,
        cluster_name,
        node_name=None,
        custom_endpoints=None):
    cluster = aks_show(cmd, client, resource_group_name, cluster_name, None)
    if not cluster:
        raise ValidationError("Can not get cluster information!")

    vm_set_type = cluster.agent_pool_profiles[0].type
    if not vm_set_type:
        raise ValidationError("Can not get VM set type of the cluster!")
    print("Get node pool VM set type:", vm_set_type)

    location = get_rg_location(cmd.cli_ctx, resource_group_name)
    managed_resource_group = f"MC_{resource_group_name}_{cluster_name}_{location}"
    logger.debug("Location: %s, Managed Resource Group: %s", location, managed_resource_group)

    vmss_name = ""
    instance_id = ""
    vm_name = ""
    if vm_set_type == CONST_VIRTUAL_MACHINE_SCALE_SETS:
        vmss_name, instance_id = _aks_get_node_name_vmss(
            cmd, resource_group_name, cluster_name, node_name, managed_resource_group)

        print(f"Start checking outbound network for vmss: {vmss_name},"
              f" instance_id: {instance_id}, managed_resource_group: {managed_resource_group}")
    elif vm_set_type == CONST_AVAILABILITY_SET:
        vm_name = _aks_get_node_name_as(
            cmd, node_name, managed_resource_group)

        print(f"Start checking outbound network for vm: {vm_name},"
              f" managed_resource_group: {managed_resource_group}")
    else:
        raise ValidationError(f"VM set type {vm_set_type} is not supported!")

    return _aks_run_command(cmd,
                            vm_set_type,
                            managed_resource_group,
                            vmss_name,
                            instance_id,
                            vm_name,
                            custom_endpoints)


def create_k8s_extension(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    name,
    extension_type,
    scope=None,
    target_namespace=None,
    release_namespace=None,
    configuration_settings=None,
    configuration_protected_settings=None,
    configuration_settings_file=None,
    configuration_protected_settings_file=None,
    no_wait=False,
):
    raise_validation_error_if_extension_type_not_in_allow_list(extension_type.lower())
    k8s_extension_custom_mod = get_k8s_extension_module(CONST_K8S_EXTENSION_CUSTOM_MOD_NAME)
    client_factory = get_k8s_extension_module(CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME)
    client = client_factory.cf_k8s_extension_operation(cmd.cli_ctx)

    try:
        result = k8s_extension_custom_mod.create_k8s_extension(
            cmd,
            client,
            resource_group_name,
            cluster_name,
            name=name,
            cluster_type="managedClusters",
            extension_type=extension_type,
            scope=scope,
            target_namespace=target_namespace,
            release_namespace=release_namespace,
            configuration_settings=configuration_settings,
            configuration_protected_settings=configuration_protected_settings,
            configuration_settings_file=configuration_settings_file,
            configuration_protected_settings_file=configuration_protected_settings_file,
            no_wait=no_wait,
        )
        return result
    except Exception as ex:
        logger.error("K8s extension failed to install.\nError: %s", ex)


def list_k8s_extension(
    cmd,
    client,
    resource_group_name,
    cluster_name
):
    k8s_extension_custom_mod = get_k8s_extension_module(CONST_K8S_EXTENSION_CUSTOM_MOD_NAME)
    client_factory = get_k8s_extension_module(CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME)
    client = client_factory.cf_k8s_extension_operation(cmd.cli_ctx)

    try:
        result = k8s_extension_custom_mod.list_k8s_extension(
            client,
            resource_group_name,
            cluster_name,
            cluster_type="managedClusters",
        )
        return get_all_extensions_in_allow_list(result)
    except Exception as ex:
        logger.error("Failed to list the K8s extension.\nError: %s", ex)


def update_k8s_extension(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    name,
    configuration_settings=None,
    configuration_protected_settings=None,
    configuration_settings_file=None,
    configuration_protected_settings_file=None,
    no_wait=False,
    yes=False,
):
    k8s_extension_custom_mod = get_k8s_extension_module(CONST_K8S_EXTENSION_CUSTOM_MOD_NAME)
    client_factory = get_k8s_extension_module(CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME)
    client = client_factory.cf_k8s_extension_operation(cmd.cli_ctx)

    try:
        result = k8s_extension_custom_mod.update_k8s_extension(
            cmd,
            client,
            resource_group_name,
            cluster_name,
            name,
            "managedClusters",
            configuration_settings=configuration_settings,
            configuration_protected_settings=configuration_protected_settings,
            configuration_settings_file=configuration_settings_file,
            configuration_protected_settings_file=configuration_protected_settings_file,
            no_wait=no_wait,
            yes=yes,
        )
        return result
    except Exception as ex:
        logger.error("K8s extension failed to patch.\nError: %s", ex)


def delete_k8s_extension(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    name,
    no_wait=False,
    yes=False,
    force=False,
):
    k8s_extension_custom_mod = get_k8s_extension_module(CONST_K8S_EXTENSION_CUSTOM_MOD_NAME)
    client_factory = get_k8s_extension_module(CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME)
    client = client_factory.cf_k8s_extension_operation(cmd.cli_ctx)

    try:
        result = k8s_extension_custom_mod.delete_k8s_extension(
            cmd,
            client,
            resource_group_name,
            cluster_name,
            name,
            "managedClusters",
            no_wait=no_wait,
            yes=yes,
            force=force,
        )
        return result
    except Exception as ex:
        logger.error("Failed to delete K8s extension.\nError: %s", ex)


def show_k8s_extension(cmd, client, resource_group_name, cluster_name, name):
    k8s_extension_custom_mod = get_k8s_extension_module(CONST_K8S_EXTENSION_CUSTOM_MOD_NAME)
    client_factory = get_k8s_extension_module(CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME)
    client = client_factory.cf_k8s_extension_operation(cmd.cli_ctx)

    try:
        result = k8s_extension_custom_mod.show_k8s_extension(
            client,
            resource_group_name,
            cluster_name,
            name,
            "managedClusters",
        )
        return get_extension_in_allow_list(result)
    except Exception as ex:
        logger.error("Failed to get K8s extension.\nError: %s", ex)


def list_k8s_extension_types(
    cmd,
    client,
    location=None,
    resource_group_name=None,
    cluster_name=None,
    release_train=None
):
    k8s_extension_custom_mod = get_k8s_extension_module(CONST_K8S_EXTENSION_CUSTOM_MOD_NAME)
    client_factory = get_k8s_extension_module(CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME)
    client = client_factory.cf_k8s_extension_types(cmd.cli_ctx)
    try:
        if location:
            result = k8s_extension_custom_mod.list_extension_types_by_location(
                client,
                location,
                cluster_type="managedClusters",
            )
            return get_all_extension_types_in_allow_list(result)
        if cluster_name and resource_group_name:
            result = k8s_extension_custom_mod.list_extension_types_by_cluster(
                client,
                resource_group_name,
                cluster_name,
                "managedClusters",
                release_train=release_train,
            )
            return get_all_extension_types_in_allow_list(result)
    except Exception as ex:
        logger.error("Failed to list K8s extension types by location.\nError: %s", ex)


# get K8s extension type
def show_k8s_extension_type(
    cmd,
    client,
    extension_type,
    location=None,
    resource_group_name=None,
    cluster_name=None
):
    raise_validation_error_if_extension_type_not_in_allow_list(extension_type.lower())
    k8s_extension_custom_mod = get_k8s_extension_module(CONST_K8S_EXTENSION_CUSTOM_MOD_NAME)
    client_factory = get_k8s_extension_module(CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME)
    client = client_factory.cf_k8s_extension_types(cmd.cli_ctx)
    try:
        if location:
            result = k8s_extension_custom_mod.show_extension_type_by_location(
                client,
                location,
                extension_type=extension_type,
            )
            return result
        if cluster_name and resource_group_name:
            result = k8s_extension_custom_mod.show_extension_type_by_cluster(
                client,
                resource_group_name,
                cluster_name,
                "managedClusters",
                extension_type,
            )
            return result
    except Exception as ex:
        logger.error("Failed to get K8s extension types by location.\nError: %s", ex)


# list version by location
def list_k8s_extension_type_versions(
    cmd,
    client,
    extension_type,
    location=None,
    resource_group_name=None,
    cluster_name=None,
    release_train=None,
    major_version=None,
    show_latest=False
):
    raise_validation_error_if_extension_type_not_in_allow_list(extension_type.lower())
    k8s_extension_custom_mod = get_k8s_extension_module(CONST_K8S_EXTENSION_CUSTOM_MOD_NAME)
    client_factory = get_k8s_extension_module(CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME)
    client = client_factory.cf_k8s_extension_types(cmd.cli_ctx)
    try:
        if location:
            result = k8s_extension_custom_mod.list_extension_type_versions_by_location(
                client,
                location,
                extension_type,
                release_train=release_train,
                cluster_type="managedClusters",
                major_version=major_version,
                show_latest=show_latest,
            )
            return result
        if cluster_name and resource_group_name:
            result = k8s_extension_custom_mod.list_extension_type_versions_by_cluster(
                client,
                resource_group_name,
                "managedClusters",
                cluster_name,
                extension_type,
                release_train=release_train,
                major_version=major_version,
                show_latest=show_latest,
            )
            return result
    except Exception as ex:
        logger.error("Failed to list K8s extension type versions by location.\nError: %s", ex)


# show extension type version
def show_k8s_extension_type_version(
    cmd,
    client,
    extension_type,
    version,
    location=None,
    resource_group_name=None,
    cluster_name=None
):
    raise_validation_error_if_extension_type_not_in_allow_list(extension_type.lower())
    k8s_extension_custom_mod = get_k8s_extension_module(CONST_K8S_EXTENSION_CUSTOM_MOD_NAME)
    client_factory = get_k8s_extension_module(CONST_K8S_EXTENSION_CLIENT_FACTORY_MOD_NAME)
    client = client_factory.cf_k8s_extension_types(cmd.cli_ctx)
    try:
        if location:
            result = k8s_extension_custom_mod.show_extension_type_version_by_location(
                client,
                location,
                extension_type,
                version,
            )
            return result
        if cluster_name and resource_group_name:
            result = k8s_extension_custom_mod.show_extension_type_version_by_cluster(
                client,
                resource_group_name,
                "managedClusters",
                cluster_name,
                extension_type,
                version
            )
            return result
    except Exception as ex:
        logger.error("Failed to get K8s extension type versions by cluster.\nError: %s", ex)


# pylint: disable=unused-argument
def aks_loadbalancer_add(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    name,
    primary_agent_pool_name,
    allow_service_placement=None,
    service_label_selector=None,
    service_namespace_selector=None,
    node_selector=None,
    aks_custom_headers=None,
):
    """Add a load balancer configuration to a managed cluster.
    :param resource_group_name: Name of resource group.
    :type resource_group_name: str
    :param cluster_name: Name of the managed cluster.
    :type cluster_name: str
    :param name: Name of the public load balancer.
    :type name: str
    :param primary_agent_pool_name: Name of the primary agent pool for this load balancer.
    :type primary_agent_pool_name: str
    :param allow_service_placement: Whether to automatically place services on the load balancer. Default is true.
    :type allow_service_placement: bool
    :param service_label_selector: Only services that match this selector can be placed on this load balancer.
    :type service_label_selector: str
    :param service_namespace_selector: Services created in namespaces that match the selector can be
        placed on this load balancer.
    :type service_namespace_selector: str
    :param node_selector: Nodes that match this selector will be possible members of this load balancer.
    :type node_selector: str
    """
    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()
    from azext_aks_preview.loadbalancerconfiguration import (
        aks_loadbalancer_add_internal,
    )

    return aks_loadbalancer_add_internal(cmd, client, raw_parameters)


def aks_loadbalancer_update(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    name,
    primary_agent_pool_name=None,
    allow_service_placement=None,
    service_label_selector=None,
    service_namespace_selector=None,
    node_selector=None,
    aks_custom_headers=None,
):
    """Update a load balancer configuration in a managed cluster.
    :param resource_group_name: Name of resource group.
    :type resource_group_name: str
    :param cluster_name: Name of the managed cluster.
    :type cluster_name: str
    :param loadbalancer_name: Name of the load balancer configuration.
    :type loadbalancer_name: str
    :param name: Name of the public load balancer.
    :type name: str
    :param primary_agent_pool_name: Name of the primary agent pool for this load balancer.
    :type primary_agent_pool_name: str
    :param allow_service_placement: Whether to automatically place services on the load balancer. Default is true.
    :type allow_service_placement: bool
    :param service_label_selector: Only services that match this selector can be placed on this load balancer.
    :type service_label_selector: str
    :param service_namespace_selector: Services created in namespaces that match the selector can be
        placed on this load balancer.
    :type service_namespace_selector: str
    :param node_selector: Nodes that match this selector will be possible members of this load balancer.
    :type node_selector: str
    """

    # DO NOT MOVE: get all the original parameters and save them as a dictionary
    raw_parameters = locals()
    from azext_aks_preview.loadbalancerconfiguration import (
        aks_loadbalancer_update_internal,
    )

    return aks_loadbalancer_update_internal(cmd, client, raw_parameters)


def aks_loadbalancer_delete(cmd, client, resource_group_name, cluster_name, name):
    """Delete a load balancer configuration in a managed cluster.
    :param resource_group_name: Name of resource group.
    :type resource_group_name: str
    :param cluster_name: Name of the managed cluster.
    :type cluster_name: str
    :param name: Name of the load balancer configuration.
    :type name: str
    """
    return client.begin_delete(resource_group_name, cluster_name, name)


def aks_loadbalancer_list(cmd, client, resource_group_name, cluster_name):
    """List load balancer configurations in a managed cluster.
    :param resource_group_name: Name of resource group.
    :type resource_group_name: str
    :param cluster_name: Name of the managed cluster.
    :type cluster_name: str
    """
    return client.list_by_managed_cluster(resource_group_name, cluster_name)


def aks_loadbalancer_show(cmd, client, resource_group_name, cluster_name, name):
    """Show the details for a load balancer configuration.
    :param resource_group_name: Name of resource group.
    :type resource_group_name: str
    :param cluster_name: Name of the managed cluster.
    :type cluster_name: str
    :param name: Name of the load balancer configuration.
    :type name: str
    """
    return client.get(resource_group_name, cluster_name, name)


# pylint: disable=unused-argument
def aks_loadbalancer_rebalance_nodes(
    cmd,
    client,
    resource_group_name,
    cluster_name,
    load_balancer_names=None,
):
    """Rebalance nodes across specific load balancers.
    :param cmd: Command context
    :param client: AKS client
    :param resource_group_name: Name of resource group.
    :type resource_group_name: str
    :param cluster_name: Name of the managed cluster.
    :type cluster_name: str
    :param load_balancer_names: Names of load balancers to rebalance.
        If not specified, all load balancers will be rebalanced.
    :type load_balancer_names: list[str]
    :param no_wait: Do not wait for the long-running operation to finish.
    :type no_wait: bool
    :return: The result of the rebalance operation
    """
    from azext_aks_preview.loadbalancerconfiguration import (
        aks_loadbalancer_rebalance_internal,
    )
    from azext_aks_preview._client_factory import cf_managed_clusters

    # Get the load balancers client
    managed_clusters_client = cf_managed_clusters(cmd.cli_ctx)

    # Prepare parameters for the internal function
    parameters = {
        "resource_group_name": resource_group_name,
        "cluster_name": cluster_name,
        "load_balancer_names": load_balancer_names,
    }

    return aks_loadbalancer_rebalance_internal(managed_clusters_client, parameters)


def aks_bastion(cmd, client, resource_group_name, name, bastion=None, port=None, admin=False, yes=False):
    import asyncio
    import tempfile

    from azure.cli.command_modules.acs._consts import DecoratorEarlyExitException

    try:
        aks_bastion_extension(yes)
    except DecoratorEarlyExitException as ex:
        logger.error(ex)
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info("creating temporary directory: %s", temp_dir)
        try:
            kubeconfig_path = os.path.join(temp_dir, ".kube", "config")
            mc = client.get(resource_group_name, name)
            mc_id = mc.id
            nrg = mc.node_resource_group
            bastion_resource = aks_bastion_parse_bastion_resource(bastion, [nrg])
            port = aks_bastion_get_local_port(port)
            aks_get_credentials(cmd, client, resource_group_name, name, admin=admin, path=kubeconfig_path)
            aks_bastion_set_kubeconfig(kubeconfig_path, port)
            asyncio.run(
                aks_bastion_runner(
                    bastion_resource,
                    port,
                    mc_id,
                    kubeconfig_path,
                    test_hook=os.getenv("AKS_BASTION_TEST_HOOK"),
                )
            )
        finally:
            aks_batsion_clean_up()
