"""Tests for Murayama calculation engine."""
import pytest
import numpy as np
from src.models import TunnelGeometry, SoilParameters, LoadingConditions, MurayamaInput
from src.murayama import MurayamaCalculator


class TestMurayamaCalculator:
    """Test MurayamaCalculator class."""
    
    @pytest.fixture
    def basic_input(self):
        """Create basic input for testing."""
        geom = TunnelGeometry(height=10.0, r0=5.0)
        soil = SoilParameters(gamma=20.0, c=30.0, phi=30.0)
        loading = LoadingConditions(u=0.0, sigma_v=0.0)
        return MurayamaInput(
            geometry=geom,
            soil=soil,
            loading=loading,
            max_B=10.0,
            step_B=0.5
        )
    
    def test_calculator_initialization(self, basic_input):
        """Test calculator initialization."""
        calc = MurayamaCalculator(basic_input)
        assert calc.params == basic_input
        assert calc.g == 9.81
    
    def test_calculate_curve_returns_results(self, basic_input):
        """Test that calculate_curve returns valid results."""
        calc = MurayamaCalculator(basic_input)
        result = calc.calculate_curve()
        
        assert len(result.B_values) > 0
        assert len(result.P_values) > 0
        assert len(result.B_values) == len(result.P_values)
        assert result.P_max > 0
        assert result.B_critical > 0
    
    def test_cohesive_soil(self):
        """Test calculation for purely cohesive soil (phi=0)."""
        geom = TunnelGeometry(height=10.0, r0=5.0)
        soil = SoilParameters(gamma=18.0, c=50.0, phi=0.0)
        loading = LoadingConditions()
        
        murayama = MurayamaInput(
            geometry=geom,
            soil=soil,
            loading=loading,
            max_B=8.0,
            step_B=0.2
        )
        
        calc = MurayamaCalculator(murayama)
        result = calc.calculate_curve()
        
        assert result.P_max > 0
        assert all(p >= 0 for p in result.P_values)
    
    def test_frictional_soil(self):
        """Test calculation for purely frictional soil (c=0)."""
        geom = TunnelGeometry(height=8.0, r0=4.0)
        soil = SoilParameters(gamma=21.0, c=0.0, phi=35.0)
        loading = LoadingConditions()
        
        murayama = MurayamaInput(
            geometry=geom,
            soil=soil,
            loading=loading,
            max_B=10.0,
            step_B=0.5
        )
        
        calc = MurayamaCalculator(murayama)
        result = calc.calculate_curve()
        
        assert result.P_max > 0
        assert result.B_critical > 0
    
    def test_safety_factor_calculation(self):
        """Test safety factor calculation with surcharge."""
        geom = TunnelGeometry(height=10.0, r0=5.0)
        soil = SoilParameters(gamma=20.0, c=30.0, phi=30.0)
        loading = LoadingConditions(u=0.0, sigma_v=100.0)  # With surcharge
        
        murayama = MurayamaInput(
            geometry=geom,
            soil=soil,
            loading=loading,
            max_B=10.0,
            step_B=0.5
        )
        
        calc = MurayamaCalculator(murayama)
        result = calc.calculate_curve()
        
        assert result.safety_factor is not None
        assert result.safety_factor > 0
    
    def test_water_pressure_effect(self):
        """Test that water pressure reduces resistance."""
        geom = TunnelGeometry(height=10.0, r0=5.0)
        soil = SoilParameters(gamma=20.0, c=30.0, phi=30.0)
        
        # Without water pressure
        loading_dry = LoadingConditions(u=0.0, sigma_v=0.0)
        murayama_dry = MurayamaInput(
            geometry=geom,
            soil=soil,
            loading=loading_dry,
            max_B=10.0,
            step_B=0.5
        )
        calc_dry = MurayamaCalculator(murayama_dry)
        result_dry = calc_dry.calculate_curve()
        
        # With water pressure
        loading_wet = LoadingConditions(u=50.0, sigma_v=0.0)
        murayama_wet = MurayamaInput(
            geometry=geom,
            soil=soil,
            loading=loading_wet,
            max_B=10.0,
            step_B=0.5
        )
        calc_wet = MurayamaCalculator(murayama_wet)
        result_wet = calc_wet.calculate_curve()
        
        # Water pressure should reduce maximum resistance
        assert result_wet.P_max < result_dry.P_max