"""Podman environment for mini-SWE-agent.

This module provides a Podman-based container environment that is a drop-in
replacement for the Docker environment. Podman is preferred in environments
where daemonless and rootless container execution is required.
"""

from dataclasses import dataclass

from minisweagent.environments.docker import DockerEnvironment, DockerEnvironmentConfig


@dataclass
class PodmanEnvironmentConfig(DockerEnvironmentConfig):
    """Configuration for PodmanEnvironment.

    Inherits all settings from DockerEnvironmentConfig but defaults
    the executable to 'podman' instead of 'docker'.
    """

    executable: str = "podman"


class PodmanEnvironment(DockerEnvironment):
    """Container environment using Podman instead of Docker.

    Podman is a daemonless, rootless container engine that is CLI-compatible
    with Docker. This environment class allows using Podman directly without
    needing to alias `docker` to `podman` or set environment variables.

    Usage:
        - CLI: `--environment-class podman`
        - Config: `environment_class: podman`

    All DockerEnvironmentConfig options are supported.
    """

    def __init__(self, **kwargs):
        super().__init__(config_class=PodmanEnvironmentConfig, **kwargs)
