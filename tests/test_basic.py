"""Basic tests for AI Code Detector."""

import pytest
from pathlib import Path
from codebase_csi import AICodeDetector, __version__
from codebase_csi.core.models import ScanConfiguration, ConfidenceLevel


def test_version():
    """Test that version is defined."""
    assert __version__ == "1.0.0"


def test_detector_initialization():
    """Test detector can be initialized."""
    detector = AICodeDetector()
    assert detector is not None
    assert isinstance(detector.config, ScanConfiguration)


def test_detector_with_custom_config():
    """Test detector with custom configuration."""
    config = ScanConfiguration(
        confidence_threshold=0.5,
        max_workers=2
    )
    detector = AICodeDetector(config)
    assert detector.config.confidence_threshold == 0.5
    assert detector.config.max_workers == 2


def test_confidence_level_from_score():
    """Test confidence level calculation."""
    assert ConfidenceLevel.from_score(0.1) == ConfidenceLevel.NONE
    assert ConfidenceLevel.from_score(0.3) == ConfidenceLevel.LOW
    assert ConfidenceLevel.from_score(0.5) == ConfidenceLevel.MEDIUM
    assert ConfidenceLevel.from_score(0.7) == ConfidenceLevel.HIGH
    assert ConfidenceLevel.from_score(0.9) == ConfidenceLevel.VERY_HIGH


def test_scan_configuration_validation():
    """Test configuration validation."""
    # Valid config
    config = ScanConfiguration()
    errors = config.validate()
    assert len(errors) == 0
    
    # Invalid confidence threshold
    config = ScanConfiguration(confidence_threshold=1.5)
    errors = config.validate()
    assert len(errors) > 0
    
    # Invalid max_workers
    config = ScanConfiguration(max_workers=0)
    errors = config.validate()
    assert len(errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
