from app.models.request_response import ComponentModel


def build_mermaid_diagram(components: list[ComponentModel]) -> str:
    if not components:
        return "graph TD;\n    User[User] --> System[System];"

    lines = ["graph TD;"]
    declared_nodes: set[str] = set()
    edges: set[tuple[str, str]] = set()

    for component in components:
        source_id = _node_id(component.name)
        if source_id not in declared_nodes:
            lines.append(f"    {source_id}[{component.name}];")
            declared_nodes.add(source_id)

        for target in component.communicates_with:
            target_id = _node_id(target)
            if target_id not in declared_nodes:
                lines.append(f"    {target_id}[{target}];")
                declared_nodes.add(target_id)

            edge = (source_id, target_id)
            if edge not in edges:
                lines.append(f"    {source_id} --> {target_id};")
                edges.add(edge)

    return "\n".join(lines)


def _node_id(name: str) -> str:
    sanitized = "".join(char for char in name.title() if char.isalnum())
    return sanitized or "Node"
