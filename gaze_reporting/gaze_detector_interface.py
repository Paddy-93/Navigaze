#!/usr/bin/env python3
"""
Gaze Detector Interface
Abstract base class for gaze detection implementations
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple

class GazeDetectorInterface(ABC):
    """Abstract interface for gaze detection implementations"""
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the gaze detector
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def update(self) -> Optional[Dict[str, Any]]:
        """Update gaze detection and return current gaze state
        Returns:
            Optional[Dict[str, Any]]: Gaze result dictionary with keys:
                - direction: str or None ('UP', 'DOWN', or None for neutral)
                - offset: float (gaze offset value)
                - is_continuous_gaze: bool (whether gaze is continuous)
                - gaze_detected: bool (whether new gaze was detected)
                - pupil_relative: Tuple[float, float] (pupil position)
                - confidence: float (detection confidence)
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources"""
        pass
    
    @abstractmethod
    def is_ready(self) -> bool:
        """Check if the gaze detector is ready for use
        Returns:
            bool: True if ready, False otherwise
        """
        pass
