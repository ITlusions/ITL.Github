"""Collect the container images that rendered Kubernetes resources reference."""

# AI generated code: GitHub Copilot Claude Haiku 5.5
WORKLOAD_KINDS = ('Deployment', 'DaemonSet', 'StatefulSet', 'ReplicaSet', 'ReplicationController', 'Job')
CONTAINER_GROUPS = ('containers', 'initContainers', 'ephemeralContainers')


class ImageFinder:
    """Find the images of the containers in rendered workloads, pods, and lists."""

    def find(self, resources):
        """Return the sorted, unique image references of the resources.

        Args:
            resources: Iterable of parsed Kubernetes resources; non-mapping items are skipped.

        Returns:
            A sorted list of image references.
        """
        images = set()
        for resource in resources:
            if isinstance(resource, dict):
                images.update(self.resource_images(resource))
        return sorted(images)

    def resource_images(self, resource):
        """Return the image references of one resource, expanding List items."""
        if resource.get('kind') == 'List':
            return set(self.find(resource.get('items') or []))
        spec = self.pod_spec(resource)
        images = set()
        if spec is None:
            return images
        for group in CONTAINER_GROUPS:
            for container in spec.get(group) or []:
                if isinstance(container, dict) and isinstance(container.get('image'), str):
                    images.add(container['image'])
        return images

    def pod_spec(self, resource):
        """Return the pod spec of a workload, CronJob, or Pod, or None for any other kind."""
        kind = resource.get('kind')
        spec = resource.get('spec') or {}
        if kind in WORKLOAD_KINDS:
            return (spec.get('template') or {}).get('spec') or {}
        if kind == 'CronJob':
            job = (spec.get('jobTemplate') or {}).get('spec') or {}
            return (job.get('template') or {}).get('spec') or {}
        if kind == 'Pod':
            return spec
        return None
