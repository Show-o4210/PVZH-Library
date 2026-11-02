from config import SHIP_CONTAINER_MARKER, SHIP_INHAND_MARKER


def get_path_id(ptr):
    for attr in ("path_id", "pathID", "m_PathID"):
        if hasattr(ptr, attr):
            return getattr(ptr, attr)
    return -1


def build_container_map(env):
    container_map = {}
    if not hasattr(env, "container"):
        return container_map
    for container_path, ptr in env.container.items():
        container_map[get_path_id(ptr)] = container_path
    return container_map


def is_ship_container_path(container_path):
    if not container_path:
        return False
    normalized = container_path.replace("\\", "/").lower()
    return (
        SHIP_CONTAINER_MARKER in normalized
        or SHIP_INHAND_MARKER in normalized
    )


def collect_ship_protected_ids(env):
    protected = set()
    container_map = build_container_map(env)
    serialized_file = env.assets[0]

    for path_id, container_path in container_map.items():
        if not is_ship_container_path(container_path):
            continue
        protected.add(path_id)
        obj = serialized_file.objects.get(path_id)
        if obj is None or obj.type.name != "Sprite":
            continue
        sprite = obj.read()
        texture_path_id = get_path_id(sprite.m_RD.texture)
        if texture_path_id not in (0, -1):
            protected.add(texture_path_id)

    return protected


def find_ship_inhand_texture(ship_assets):
    for asset in ship_assets:
        if asset.get("type") != "Texture2D":
            continue
        container = asset.get("container", "").replace("\\", "/").lower()
        if SHIP_INHAND_MARKER in container:
            return asset
    return None


def describe_ship_protected_assets(env):
    protected = collect_ship_protected_ids(env)
    container_map = build_container_map(env)
    details = []

    for path_id in sorted(protected, key=lambda value: (str(value))):
        obj = next((item for item in env.objects if item.path_id == path_id), None)
        if obj is None:
            continue
        try:
            name = obj.read().m_Name
        except Exception:
            name = ""
        details.append(
            {
                "path_id": path_id,
                "type": obj.type.name,
                "name": name,
                "container": container_map.get(path_id, ""),
            }
        )
    return details


def build_type_refs(env):
    refs = {}
    for obj in env.objects:
        type_name = obj.type.name
        if type_name not in refs:
            refs[type_name] = obj
    return refs


def find_big_hash_root(env):
    max_components = 0
    root_transform = None

    for obj in env.objects:
        if obj.type.name != "GameObject":
            continue
        go_data = obj.read()
        component_count = len(go_data.m_Component)
        if component_count <= max_components:
            continue
        max_components = component_count
        first_component = go_data.m_Component[0].component.read()
        if get_path_id(first_component.m_Father) == 0:
            root_transform = first_component

    return root_transform, max_components