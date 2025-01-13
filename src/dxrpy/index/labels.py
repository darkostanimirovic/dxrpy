from typing import Any, Dict


class Label:
    def __init__(self, id: int, name: str, description: str, hex_color: str, type: str):
        self.id: int = id
        self.name: str = name
        self.description: str = description
        self.hex_color: str = hex_color
        self.type: str = type

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Label':
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            hex_color=data['hexColor'],
            type=data['type']
        )