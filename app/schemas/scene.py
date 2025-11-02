from pydantic import BaseModel

# Schema base para Scene
class SceneBase(BaseModel):
    scene_key: str
    name: str
    is_relevant: bool = False


class SceneCreate(SceneBase):
    pass

class SceneUpdate(BaseModel):
    scene_key: str = None
    name: str = None
    is_relevant: bool = None

class Scene(SceneBase):
    id: int

    class Config:
        from_attributes = True

# Schema para respuesta simple
class SceneSimple(SceneBase):
    id: int

    class Config:
        from_attributes = True