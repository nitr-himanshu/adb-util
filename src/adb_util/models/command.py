"""
Command Data Model

Data model for saved ADB commands.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


@dataclass
class Command:
    """Represents a saved ADB command."""
    
    id: str
    name: str
    command: str
    category: str = "General"
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    use_count: int = 0
    is_favorite: bool = False
    tags: list = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.tags is None:
            self.tags = []
    
    def mark_used(self):
        """Mark command as used and update statistics."""
        self.last_used = datetime.now()
        self.use_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary."""
        # TODO: Implement dictionary conversion
        pass
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Command':
        """Create command from dictionary."""
        # TODO: Implement command creation from dict
        pass
    
    def __str__(self) -> str:
        return f"{self.name}: {self.command}"
