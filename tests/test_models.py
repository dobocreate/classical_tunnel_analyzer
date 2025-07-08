"""Tests for data models."""
import pytest
from src.models import TunnelGeometry, SoilParameters, LoadingConditions, MurayamaInput


class TestTunnelGeometry:
    """Test TunnelGeometry model."""
    
    def test_valid_geometry(self):
        """Test valid geometry parameters."""
        geom = TunnelGeometry(height=10.0, r0=5.0)
        assert geom.height == 10.0
        assert geom.r0 == 5.0
    
    def test_invalid_height(self):
        """Test invalid height validation."""
        with pytest.raises(ValueError):
            TunnelGeometry(height=-1.0, r0=5.0)
        
        with pytest.raises(ValueError):
            TunnelGeometry(height=0, r0=5.0)
    
    def test_invalid_r0(self):
        """Test invalid r0 validation."""
        with pytest.raises(ValueError):
            TunnelGeometry(height=10.0, r0=-1.0)


class TestSoilParameters:
    """Test SoilParameters model."""
    
    def test_valid_parameters(self):
        """Test valid soil parameters."""
        soil = SoilParameters(gamma=20.0, c=30.0, phi=35.0)
        assert soil.gamma == 20.0
        assert soil.c == 30.0
        assert soil.phi == 35.0
        assert abs(soil.phi_rad - 0.6109) < 0.001
    
    def test_phi_range_validation(self):
        """Test friction angle range validation."""
        with pytest.raises(ValueError):
            SoilParameters(gamma=20.0, c=30.0, phi=70.0)
        
        with pytest.raises(ValueError):
            SoilParameters(gamma=20.0, c=30.0, phi=-5.0)
    
    def test_gamma_range(self):
        """Test unit weight range."""
        with pytest.raises(ValueError):
            SoilParameters(gamma=5.0, c=30.0, phi=30.0)
        
        with pytest.raises(ValueError):
            SoilParameters(gamma=35.0, c=30.0, phi=30.0)


class TestLoadingConditions:
    """Test LoadingConditions model."""
    
    def test_default_values(self):
        """Test default loading values."""
        loading = LoadingConditions()
        assert loading.u == 0
        assert loading.sigma_v == 0
    
    def test_custom_values(self):
        """Test custom loading values."""
        loading = LoadingConditions(u=50.0, sigma_v=100.0)
        assert loading.u == 50.0
        assert loading.sigma_v == 100.0


class TestMurayamaInput:
    """Test MurayamaInput model."""
    
    def test_complete_input(self):
        """Test complete input model."""
        geom = TunnelGeometry(height=10.0, r0=5.0)
        soil = SoilParameters(gamma=20.0, c=30.0, phi=35.0)
        loading = LoadingConditions(u=10.0, sigma_v=50.0)
        
        murayama = MurayamaInput(
            geometry=geom,
            soil=soil,
            loading=loading,
            max_B=15.0,
            step_B=0.1
        )
        
        assert murayama.geometry.height == 10.0
        assert murayama.soil.gamma == 20.0
        assert murayama.loading.u == 10.0
        assert murayama.max_B == 15.0
        assert murayama.step_B == 0.1