"""
galaxy_core/models/base.py
Base model with event system support for all game entities
"""

from typing import Dict, List, Callable, Any, Optional, Set
from datetime import datetime
import weakref
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class GameEvent:
    """Represents a game event that can be published"""
    event_type: str
    source: Any
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class EventPublisher:
    """Mixin class that provides event publishing capabilities"""
    
    def __init__(self):
        self._event_handlers: Dict[str, List[weakref.ref]] = {}
        self._event_history: List[GameEvent] = []
        self._max_history_size = 100
    
    def subscribe(self, event_type: str, handler: Callable[[GameEvent], None]) -> None:
        """Subscribe to events of a specific type"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        # Use weak references to avoid circular dependencies
        self._event_handlers[event_type].append(weakref.ref(handler))
        logger.debug(f"Handler subscribed to {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable[[GameEvent], None]) -> None:
        """Unsubscribe from events of a specific type"""
        if event_type in self._event_handlers:
            # Remove dead weak references and the specified handler
            self._event_handlers[event_type] = [
                ref for ref in self._event_handlers[event_type]
                if ref() is not None and ref() != handler
            ]
    
    def publish_event(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Publish an event to all subscribers"""
        event = GameEvent(
            event_type=event_type,
            source=self,
            data=data or {}
        )
        
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history_size:
            self._event_history.pop(0)
        
        # Notify subscribers
        if event_type in self._event_handlers:
            # Clean up dead references while iterating
            alive_handlers = []
            for handler_ref in self._event_handlers[event_type]:
                handler = handler_ref()
                if handler is not None:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Error in event handler for {event_type}: {e}")
                    alive_handlers.append(handler_ref)
            
            self._event_handlers[event_type] = alive_handlers
        
        logger.debug(f"Published event: {event_type} from {type(self).__name__}")
    
    def get_event_history(self, event_type: Optional[str] = None) -> List[GameEvent]:
        """Get event history, optionally filtered by type"""
        if event_type:
            return [e for e in self._event_history if e.event_type == event_type]
        return list(self._event_history)


class BaseModel(EventPublisher, ABC):
    """Base model class for all game entities"""
    
    def __init__(self, model_id: Optional[int] = None):
        super().__init__()
        self._id = model_id
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
        self._is_dirty = False
        self._tracked_fields: Set[str] = set()
    
    @property
    def id(self) -> Optional[int]:
        return self._id
    
    @id.setter
    def id(self, value: int):
        self._id = value
        self._mark_dirty()
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    @property
    def is_dirty(self) -> bool:
        """Check if the model has unsaved changes"""
        return self._is_dirty
    
    def _mark_dirty(self):
        """Mark the model as having unsaved changes"""
        self._is_dirty = True
        self._updated_at = datetime.now()
    
    def _mark_clean(self):
        """Mark the model as having no unsaved changes"""
        self._is_dirty = False
    
    def track_field(self, field_name: str):
        """Mark a field for change tracking"""
        self._tracked_fields.add(field_name)
    
    def __setattr__(self, name: str, value: Any):
        """Override setattr to track changes and publish events"""
        # Skip private attributes and initial setup
        if name.startswith('_') or not hasattr(self, '_tracked_fields'):
            super().__setattr__(name, value)
            return
        
        # Check if this is a tracked field
        if hasattr(self, name) and name in self._tracked_fields:
            old_value = getattr(self, name)
            if old_value != value:
                super().__setattr__(name, value)
                self._mark_dirty()
                self.publish_event(f"{name}_changed", {
                    'field': name,
                    'old_value': old_value,
                    'new_value': value
                })
        else:
            super().__setattr__(name, value)
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate the model's current state"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary representation"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Create model instance from dictionary"""
        pass


class ModelCollection(EventPublisher):
    """Manages a collection of models with event support"""
    
    def __init__(self, model_class: type):
        super().__init__()
        self._model_class = model_class
        self._models: Dict[int, BaseModel] = {}
    
    def add(self, model: BaseModel) -> None:
        """Add a model to the collection"""
        if model.id is None:
            raise ValueError("Cannot add model without ID to collection")
        
        self._models[model.id] = model
        self.publish_event("model_added", {"model": model})
    
    def remove(self, model_id: int) -> Optional[BaseModel]:
        """Remove a model from the collection"""
        if model_id in self._models:
            model = self._models.pop(model_id)
            self.publish_event("model_removed", {"model": model})
            return model
        return None
    
    def get(self, model_id: int) -> Optional[BaseModel]:
        """Get a model by ID"""
        return self._models.get(model_id)
    
    def get_all(self) -> List[BaseModel]:
        """Get all models in the collection"""
        return list(self._models.values())
    
    def filter(self, predicate: Callable[[BaseModel], bool]) -> List[BaseModel]:
        """Filter models by a predicate function"""
        return [model for model in self._models.values() if predicate(model)]
    
    def count(self) -> int:
        """Get the number of models in the collection"""
        return len(self._models)
    
    def clear(self) -> None:
        """Remove all models from the collection"""
        self._models.clear()
        self.publish_event("collection_cleared", {})