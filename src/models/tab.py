"""
Tab Data Model

Data model for application tabs representing device-mode combinations.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


@dataclass
class Tab:
    """Represents an application tab for device-mode combination."""
    
    id: str
    device_id: str
    mode: str
    title: str
    is_active: bool = False
    created_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    state: Dict[str, Any] = None
    widget_instance: Any = None  # Reference to the actual widget
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.state is None:
            self.state = {}
    
    @property
    def display_title(self) -> str:
        """Get display title for the tab."""
        return self.title or f"{self.device_id}-{self.mode}"
    
    def mark_accessed(self):
        """Mark tab as accessed."""
        self.last_accessed = datetime.now()
    
    def update_state(self, new_state: Dict[str, Any]):
        """Update tab state."""
        self.state.update(new_state)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tab to dictionary."""
        # TODO: Implement dictionary conversion
        pass
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tab':
        """Create tab from dictionary."""
        # TODO: Implement tab creation from dict
        pass
    
    def __str__(self) -> str:
        return f"Tab({self.display_title})"
