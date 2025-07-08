"""Data models for tunnel stability analysis using Pydantic."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import numpy as np


class TunnelGeometry(BaseModel):
    """Tunnel geometry parameters."""
    height: float = Field(
        gt=0, 
        le=50, 
        description="Tunnel face height H [m]"
    )
    r0: float = Field(
        gt=0, 
        le=20, 
        description="Initial radius r0 [m]"
    )
    
    @field_validator('height')
    def validate_height(cls, v):
        if v <= 0:
            raise ValueError("Height must be positive")
        return v


class SoilParameters(BaseModel):
    """Soil mechanical parameters."""
    gamma: float = Field(
        ge=10, 
        le=30, 
        description="Effective unit weight γ [kN/m³]"
    )
    c: float = Field(
        ge=0, 
        le=1000, 
        description="Cohesion c [kPa]"
    )
    phi: float = Field(
        ge=0, 
        le=60, 
        description="Internal friction angle φ [degrees]"
    )
    
    @property
    def phi_rad(self) -> float:
        """Convert phi to radians."""
        return np.radians(self.phi)
    
    @field_validator('phi')
    def validate_phi(cls, v):
        if not 0 <= v <= 60:
            raise ValueError("Friction angle must be between 0 and 60 degrees")
        return v


class LoadingConditions(BaseModel):
    """External loading conditions."""
    u: float = Field(
        ge=0, 
        le=1000, 
        description="Water pressure u [kPa]", 
        default=0
    )
    sigma_v: float = Field(
        ge=0, 
        le=5000, 
        description="Surcharge load σ_v [kPa]", 
        default=0
    )


class MurayamaInput(BaseModel):
    """Complete input parameters for Murayama analysis."""
    geometry: TunnelGeometry
    soil: SoilParameters
    loading: LoadingConditions
    max_B: float = Field(
        gt=0, 
        le=50, 
        default=10.0, 
        description="Maximum sliding width B for analysis [m]"
    )
    step_B: float = Field(
        gt=0, 
        le=1, 
        default=0.05, 
        description="Step size for B iteration [m]"
    )
    n_divisions: int = Field(
        ge=10, 
        le=1000, 
        default=100, 
        description="Number of divisions for numerical integration"
    )
    max_iterations: int = Field(
        ge=10, 
        le=1000, 
        default=100, 
        description="Maximum iterations for convergence"
    )
    tolerance: float = Field(
        gt=0, 
        le=0.1, 
        default=1e-6, 
        description="Convergence tolerance"
    )


class MurayamaResult(BaseModel):
    """Results from Murayama analysis."""
    B_values: List[float] = Field(description="Sliding width values [m]")
    P_values: List[float] = Field(description="Resistance force values [kN/m]")
    P_max: float = Field(description="Maximum resistance force [kN/m]")
    B_critical: float = Field(description="Critical sliding width [m]")
    safety_factor: Optional[float] = Field(
        default=None, 
        description="Safety factor (if external load provided)"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            list: lambda v: [round(x, 3) for x in v] if v else []
        }


class DesignPreset(BaseModel):
    """Preset parameters for common soil types."""
    name: str = Field(description="Preset name")
    description: str = Field(description="Description of soil type")
    soil: SoilParameters
    typical_loading: LoadingConditions = Field(
        default_factory=lambda: LoadingConditions(u=0, sigma_v=0)
    )