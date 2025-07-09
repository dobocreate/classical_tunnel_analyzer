"""Data models for tunnel stability analysis using Pydantic."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum
import numpy as np


class SurchargeMethod(str, Enum):
    """Surcharge load calculation method."""
    SIMPLE = "簡易法"
    TERZAGHI = "テルツァギーの土圧理論"


class TunnelGeometry(BaseModel):
    """Tunnel geometry parameters."""
    height: float = Field(
        gt=0, 
        le=50, 
        description="Tunnel face height H [m]"
    )
    tunnel_depth: float = Field(
        ge=0,
        le=100,
        default=10.0,
        description="Tunnel crown depth D_t [m]"
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
    x_start: float = Field(
        ge=-20.0,
        le=0.0,
        default=-10.0,
        description="Start position for slip surface search (from tunnel center) [m]"
    )
    x_end: float = Field(
        ge=0.0,
        le=20.0,
        default=10.0,
        description="End position for slip surface search (from tunnel center) [m]"
    )
    x_step: float = Field(
        gt=0,
        le=2.0,
        default=0.5,
        description="Step size for slip surface search [m]"
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
    surcharge_method: SurchargeMethod = Field(
        default=SurchargeMethod.SIMPLE,
        description="Surcharge load calculation method"
    )


class MurayamaResult(BaseModel):
    """Results from Murayama analysis."""
    x_values: List[float] = Field(description="Slip surface start positions [m]")
    P_values: List[float] = Field(description="Required support pressure values [kN/m²]")
    P_max: float = Field(description="Maximum required support pressure [kN/m²]")
    x_critical: float = Field(description="Critical slip surface position [m]")
    critical_slip_surface: dict = Field(
        description="Critical slip surface geometry",
        default_factory=dict
    )
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