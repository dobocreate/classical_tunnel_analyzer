"""Murayama method calculation engine for tunnel face stability analysis."""
import numpy as np
from typing import Tuple, Optional
from src.models import MurayamaInput, MurayamaResult


class MurayamaCalculator:
    """Calculator for Murayama's tunnel face stability method."""
    
    def __init__(self, params: MurayamaInput):
        """Initialize calculator with input parameters."""
        self.params = params
        self.g = 9.81  # Gravitational acceleration [m/s²]
        
    def calculate_curve(self) -> MurayamaResult:
        """
        Calculate P-B curve using Murayama's method.
        
        Returns:
            MurayamaResult containing B values, P values, and critical values
        """
        B_values = []
        P_values = []
        
        # Iterate through sliding width values
        B_range = np.arange(
            self.params.step_B, 
            self.params.max_B + self.params.step_B, 
            self.params.step_B
        )
        
        for B in B_range:
            P = self._calculate_resistance(B)
            if P is not None and P > 0:
                B_values.append(B)
                P_values.append(P)
        
        # Find maximum resistance
        if P_values:
            P_max = max(P_values)
            max_index = P_values.index(P_max)
            B_critical = B_values[max_index]
        else:
            P_max = 0
            B_critical = 0
        
        # Calculate safety factor if external load is provided
        safety_factor = self._calculate_safety_factor(P_max)
        
        return MurayamaResult(
            B_values=B_values,
            P_values=P_values,
            P_max=P_max,
            B_critical=B_critical,
            safety_factor=safety_factor
        )
    
    def _calculate_resistance(self, B: float) -> Optional[float]:
        """
        Calculate resistance force P for given sliding width B.
        
        Args:
            B: Sliding width [m]
            
        Returns:
            Resistance force P [kN/m] or None if calculation fails
        """
        try:
            # Get parameters
            H = self.params.geometry.height
            r0 = self.params.geometry.r0
            gamma = self.params.soil.gamma
            c = self.params.soil.c
            phi_rad = self.params.soil.phi_rad
            u = self.params.loading.u
            sigma_v = self.params.loading.sigma_v
            
            # Calculate angles
            theta_0 = self._calculate_theta_0(H, r0, phi_rad)
            theta_1 = self._calculate_theta_1(B, r0, phi_rad, theta_0)
            
            if theta_0 is None or theta_1 is None:
                return None
            
            # Calculate sliding mass weight
            W_f = self._calculate_weight(H, B, r0, gamma, phi_rad, theta_0, theta_1)
            
            # Calculate moment arms
            l_w = self._calculate_moment_arm_weight(H, B, r0, phi_rad, theta_0, theta_1)
            l_p = self._calculate_moment_arm_resistance(H, r0, phi_rad, theta_0)
            
            # Calculate friction moment
            friction_moment = self._calculate_friction_moment(r0, c, phi_rad, theta_0, theta_1)
            
            # Calculate water pressure effect
            water_effect = self._calculate_water_pressure_effect(u, H, B, l_w)
            
            # Calculate surcharge effect
            surcharge_effect = sigma_v * B * l_w
            
            # Calculate resistance force P using moment equilibrium
            if l_p > 0:
                P = (W_f * l_w + friction_moment - water_effect + surcharge_effect) / l_p
                return max(0, P)  # Ensure non-negative
            else:
                return None
                
        except Exception as e:
            print(f"Calculation error for B={B}: {e}")
            return None
    
    def _calculate_theta_0(self, H: float, r0: float, phi_rad: float) -> Optional[float]:
        """Calculate initial angle theta_0."""
        try:
            if phi_rad == 0:
                return np.arcsin(H / (2 * r0))
            else:
                # Iterative solution for theta_0
                theta = 0.1  # Initial guess
                for _ in range(self.params.max_iterations):
                    f = r0 * (np.exp(theta * np.tan(phi_rad)) - 1) * np.cos(theta) - H / 2
                    df = r0 * (np.exp(theta * np.tan(phi_rad)) * np.tan(phi_rad) * np.cos(theta) 
                              - np.exp(theta * np.tan(phi_rad)) * np.sin(theta) + np.sin(theta))
                    theta_new = theta - f / df
                    if abs(theta_new - theta) < self.params.tolerance:
                        return theta_new
                    theta = theta_new
                return theta
        except:
            return None
    
    def _calculate_theta_1(self, B: float, r0: float, phi_rad: float, theta_0: float) -> Optional[float]:
        """Calculate terminal angle theta_1."""
        try:
            if phi_rad == 0:
                return np.arcsin((B + r0 * np.sin(theta_0)) / r0)
            else:
                # Iterative solution for theta_1
                theta = theta_0 + 0.5  # Initial guess
                for _ in range(self.params.max_iterations):
                    r_theta = r0 * np.exp(theta * np.tan(phi_rad))
                    r_theta_0 = r0 * np.exp(theta_0 * np.tan(phi_rad))
                    f = r_theta * np.sin(theta) - r_theta_0 * np.sin(theta_0) - B
                    df = r_theta * (np.tan(phi_rad) * np.sin(theta) + np.cos(theta))
                    theta_new = theta - f / df
                    if abs(theta_new - theta) < self.params.tolerance:
                        return theta_new
                    theta = theta_new
                return theta
        except:
            return None
    
    def _calculate_weight(self, H: float, B: float, r0: float, gamma: float, 
                         phi_rad: float, theta_0: float, theta_1: float) -> float:
        """Calculate weight of sliding mass."""
        # Simplified calculation - can be refined with more accurate integration
        volume = H * B  # Simplified rectangular approximation
        return gamma * volume
    
    def _calculate_moment_arm_weight(self, H: float, B: float, r0: float, 
                                   phi_rad: float, theta_0: float, theta_1: float) -> float:
        """Calculate moment arm for weight."""
        # Simplified calculation - assumes centroid at B/2
        return B / 2
    
    def _calculate_moment_arm_resistance(self, H: float, r0: float, 
                                       phi_rad: float, theta_0: float) -> float:
        """Calculate moment arm for resistance force."""
        # Simplified calculation
        return H / 2
    
    def _calculate_friction_moment(self, r0: float, c: float, phi_rad: float,
                                  theta_0: float, theta_1: float) -> float:
        """Calculate friction moment along sliding surface."""
        if phi_rad == 0:
            # For phi = 0, integral simplifies
            arc_length = r0 * (theta_1 - theta_0)
            return c * r0 * arc_length
        else:
            # Integration of friction along logarithmic spiral
            integral = r0**2 * c / np.tan(phi_rad) * \
                      (np.exp(2 * theta_1 * np.tan(phi_rad)) - 
                       np.exp(2 * theta_0 * np.tan(phi_rad))) / 2
            return integral * np.cos(phi_rad)
    
    def _calculate_water_pressure_effect(self, u: float, H: float, B: float, l_w: float) -> float:
        """Calculate water pressure effect on stability."""
        if u == 0:
            return 0
        # Simplified water pressure effect
        water_force = u * H * B
        return water_force * l_w * 0.5  # Simplified moment calculation
    
    def _calculate_safety_factor(self, P_max: float) -> Optional[float]:
        """Calculate safety factor if external load is present."""
        external_load = self.params.loading.sigma_v
        if external_load > 0 and P_max > 0:
            return P_max / external_load
        return None


def get_default_presets():
    """Get default soil parameter presets."""
    from src.models import DesignPreset, SoilParameters, LoadingConditions
    
    return [
        DesignPreset(
            name="砂質土（密）",
            description="Dense sand",
            soil=SoilParameters(gamma=20.0, c=0.0, phi=35.0),
            typical_loading=LoadingConditions(u=0, sigma_v=0)
        ),
        DesignPreset(
            name="砂質土（緩）",
            description="Loose sand",
            soil=SoilParameters(gamma=18.0, c=0.0, phi=30.0),
            typical_loading=LoadingConditions(u=0, sigma_v=0)
        ),
        DesignPreset(
            name="粘性土（硬）",
            description="Stiff clay",
            soil=SoilParameters(gamma=19.0, c=50.0, phi=0.0),
            typical_loading=LoadingConditions(u=0, sigma_v=0)
        ),
        DesignPreset(
            name="粘性土（軟）",
            description="Soft clay",
            soil=SoilParameters(gamma=17.0, c=25.0, phi=0.0),
            typical_loading=LoadingConditions(u=0, sigma_v=0)
        ),
        DesignPreset(
            name="砂礫",
            description="Sandy gravel",
            soil=SoilParameters(gamma=21.0, c=0.0, phi=40.0),
            typical_loading=LoadingConditions(u=0, sigma_v=0)
        ),
        DesignPreset(
            name="シルト質砂",
            description="Silty sand",
            soil=SoilParameters(gamma=19.0, c=10.0, phi=28.0),
            typical_loading=LoadingConditions(u=0, sigma_v=0)
        )
    ]