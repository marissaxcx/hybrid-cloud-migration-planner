from __future__ import annotations

from typing import Any

TARGETS = {
    "web-frontend": "Azure Static Web Apps or Azure App Service",
    "api": "Azure App Service or Azure Container Apps",
    "container": "Azure Container Apps or Azure Kubernetes Service",
    "relational-database": "Azure SQL Database (compatibility review required)",
    "nosql-database": "Azure Cosmos DB (data model review required)",
    "object-storage": "Azure Blob Storage",
    "batch": "Azure Functions or Azure Container Apps Jobs",
    "virtual-machine": "Azure Virtual Machines (right-size and modernize review)",
    "data-warehouse": "Microsoft Fabric or Azure Data Explorer (workload review required)",
}


def build_plan(payload: dict[str, Any]) -> dict[str, Any]:
    workloads = payload.get("workloads")
    if not isinstance(workloads, list) or not workloads:
        raise ValueError("workloads must be a non-empty array")
    wave_size = payload.get("wave_size", 3)
    if not isinstance(wave_size, int) or not 1 <= wave_size <= 20:
        raise ValueError("wave_size must be an integer between 1 and 20")

    by_id: dict[str, dict[str, Any]] = {}
    for row in workloads:
        if not isinstance(row, dict):
            raise ValueError("each workload must be an object")
        workload_id = str(row.get("id", "")).strip()
        if not workload_id:
            raise ValueError("each workload needs a non-empty id")
        if workload_id in by_id:
            raise ValueError(f"duplicate workload id: {workload_id}")
        by_id[workload_id] = row

    dependencies: dict[str, set[str]] = {}
    for workload_id, row in by_id.items():
        deps = row.get("depends_on", [])
        if not isinstance(deps, list):
            raise ValueError(f"depends_on for {workload_id} must be an array")
        unknown = sorted(set(deps) - by_id.keys())
        if unknown:
            raise ValueError(f"{workload_id} depends on unknown workload(s): {', '.join(unknown)}")
        dependencies[workload_id] = set(deps)

    remaining = {key: set(value) for key, value in dependencies.items()}
    waves: list[list[str]] = []
    scheduled: set[str] = set()
    while len(scheduled) < len(by_id):
        ready = sorted(key for key, deps in remaining.items() if key not in scheduled and deps <= scheduled)
        if not ready:
            cycle_members = sorted(set(by_id) - scheduled)
            raise ValueError(f"dependency cycle detected among: {', '.join(cycle_members)}")
        for start in range(0, len(ready), wave_size):
            wave = ready[start : start + wave_size]
            waves.append(wave)
            scheduled.update(wave)

    planned: list[dict[str, Any]] = []
    flags: list[dict[str, str]] = []
    for index, wave in enumerate(waves, start=1):
        for workload_id in wave:
            row = by_id[workload_id]
            workload_type = str(row.get("type", "unknown")).lower()
            item_flags: list[str] = []
            classification = str(row.get("data_classification", "unspecified")).lower()
            if classification in {"confidential", "restricted", "regulated"}:
                item_flags.append("Confirm encryption, identity, network isolation, and data residency controls.")
            if row.get("rto_hours") is None or row.get("rpo_hours") is None:
                item_flags.append("Set and validate both RTO and RPO with the workload owner.")
            target = TARGETS.get(workload_type)
            if target is None:
                item_flags.append("No target mapping exists yet; choose a landing service after discovery.")
            planned.append({
                "id": workload_id,
                "name": str(row.get("name") or workload_id),
                "type": workload_type,
                "environment": str(row.get("environment", "unspecified")),
                "wave": index,
                "depends_on": sorted(dependencies[workload_id]),
                "suggested_azure_target": target or "Needs architecture review",
                "review_flags": item_flags,
            })
            for message in item_flags:
                flags.append({"workload_id": workload_id, "severity": "review", "message": message})

    return {
        "summary": {"workload_count": len(by_id), "wave_count": len(waves), "review_flag_count": len(flags)},
        "waves": [{"wave": index, "workload_ids": wave} for index, wave in enumerate(waves, start=1)],
        "workloads": planned,
        "review_flags": flags,
        "assumptions": [
            "A listed dependency must migrate in an earlier wave than its dependent workload.",
            f"Each wave contains at most {wave_size} workloads; readiness and cutover windows still require owner review.",
            "Azure targets are starting points, not compatibility or cost guarantees.",
        ],
    }
