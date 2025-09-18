from pydantic import BaseModel
from typing import Optional, List

# Schema base para SceneLevel
class SceneLevelBase(BaseModel):
    tile_size: int
    size: int
    fallback_only: bool = False

class SceneLevelCreate(SceneLevelBase):
    pass

class SceneLevel(SceneLevelBase):
    id: int
    scene_id: int

    class Config:
        from_attributes = True

# Schema base para LinkHotspot
class LinkHotspotBase(BaseModel):
    yaw: float
    pitch: float
    rotation: Optional[float] = None
    target_scene_id: str

class LinkHotspotCreate(LinkHotspotBase):
    pass

class LinkHotspot(LinkHotspotBase):
    id: int
    scene_id: int

    class Config:
        from_attributes = True

# Schema base para InfoHotspot
class InfoHotspotBase(BaseModel):
    yaw: float
    pitch: float
    title: str
    text: str

class InfoHotspotCreate(InfoHotspotBase):
    pass

class InfoHotspot(InfoHotspotBase):
    id: int
    scene_id: int

    class Config:
        from_attributes = True

# Schema base para Scene
class SceneBase(BaseModel):
    scene_key: str
    name: str
    face_size: int
    initial_yaw: Optional[float] = None
    initial_pitch: Optional[float] = None
    initial_fov: Optional[float] = None

class SceneCreate(SceneBase):
    link_hotspots: Optional[List[LinkHotspotCreate]] = []
    info_hotspots: Optional[List[InfoHotspotCreate]] = []
    levels: Optional[List[SceneLevelCreate]] = []

class SceneUpdate(BaseModel):
    scene_key: Optional[str] = None
    name: Optional[str] = None
    face_size: Optional[int] = None
    initial_yaw: Optional[float] = None
    initial_pitch: Optional[float] = None
    initial_fov: Optional[float] = None

class Scene(SceneBase):
    id: int
    link_hotspots: List[LinkHotspot] = []
    info_hotspots: List[InfoHotspot] = []
    levels: List[SceneLevel] = []

    class Config:
        from_attributes = True

# Schema para respuesta simple sin relaciones
class SceneSimple(SceneBase):
    id: int

    class Config:
        from_attributes = True