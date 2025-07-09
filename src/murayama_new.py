"""Improved Murayama method calculation engine based on gemini specification."""
import numpy as np
from scipy.optimize import fsolve, minimize_scalar
from scipy.integrate import quad
from typing import Tuple, Dict, Optional
from src.models import MurayamaInput, MurayamaResult, SurchargeMethod


class ImprovedMurayamaCalculator:
    """Calculator for improved Murayama's tunnel face stability method."""
    
    def __init__(self, params: MurayamaInput):
        """Initialize calculator with input parameters."""
        self.params = params
        self.g = 9.81  # Gravitational acceleration [m/s²]
        
    def calculate_stability(self) -> MurayamaResult:
        """
        Calculate required support pressure using improved Murayama method.
        
        Returns:
            MurayamaResult containing x values, P values, and critical values
        """
        x_values = []
        P_values = []
        P_max = 0
        x_critical = 0
        critical_slip_surface = {}
        convergence_failures = 0
        
        # Get parameters
        H = self.params.geometry.height
        D_t = self.params.geometry.tunnel_depth
        phi_rad = self.params.soil.phi_rad
        c = self.params.soil.c
        gamma = self.params.soil.gamma
        
        # Loop through slip surface start positions
        x_range = np.arange(
            self.params.x_start,
            self.params.x_end + self.params.x_step,
            self.params.x_step
        )
        
        for x_i in x_range:
            # Step 2: Determine geometric shape
            geometry = self._determine_geometry(x_i, H, D_t, phi_rad)
            
            if geometry is None:
                convergence_failures += 1
                continue
                
            # Step 3: Calculate forces
            forces = self._calculate_forces(geometry, gamma, c, phi_rad, D_t)
            
            # Step 4: Calculate required support pressure P
            P = self._calculate_support_pressure(geometry, forces, c, phi_rad)
            
            if P is not None and P > 0:
                x_values.append(x_i)
                P_values.append(P)
                
                # Step 5: Update maximum
                if P > P_max:
                    P_max = P
                    x_critical = x_i
                    critical_slip_surface = geometry
        
        # Calculate safety factor if needed
        safety_factor = self._calculate_safety_factor(P_max)
        
        # Prepare convergence information
        convergence_info = {
            "total_points": len(x_range),
            "successful_points": len(x_values),
            "convergence_failures": convergence_failures,
            "convergence_rate": len(x_values) / len(x_range) * 100 if len(x_range) > 0 else 0
        }
        
        return MurayamaResult(
            x_values=x_values,
            P_values=P_values,
            P_max=P_max,
            x_critical=x_critical,
            critical_slip_surface=critical_slip_surface,
            safety_factor=safety_factor,
            convergence_info=convergence_info
        )
    
    def _determine_geometry(self, x_i: float, H: float, D_t: float, phi_rad: float) -> Optional[Dict]:
        """
        Determine logarithmic spiral geometry for given slip surface start point.
        
        Args:
            x_i: Horizontal distance from tunnel center to slip surface start
            H: Tunnel height
            D_t: Tunnel depth
            phi_rad: Friction angle in radians
            
        Returns:
            Dictionary containing geometric parameters or None if failed
        """
        try:
            # Slip surface start point i
            i_x = x_i
            i_y = D_t + H
            
            # Initial guess for center O
            # Center is on line through i with angle (180° - φ) from horizontal
            angle = np.pi - phi_rad
            
            # Define equations to solve for center O and radii
            def equations(vars):
                O_x, O_y, r_i, r_d = vars
                
                # Condition 1: Center O is on line through i
                eq1 = (O_y - i_y) - np.tan(angle) * (O_x - i_x)
                
                # Condition 2: Angle at bottom intersection
                # δ = 45° - φ/2 at point d where slip surface meets y = D_t
                delta = np.pi/4 - phi_rad/2
                
                # Point d is at y = D_t
                # For logarithmic spiral, need to find theta values
                theta_i = np.arctan2(i_y - O_y, i_x - O_x)
                
                # Logarithmic spiral equation: r = r_0 * exp(theta * tan(phi))
                # r_i = r_0 * exp(theta_i * tan(phi))
                # r_d = r_0 * exp(theta_d * tan(phi))
                
                # From geometry, find theta_d such that y = D_t
                # This requires iterative solution
                
                # Simplified approach for initial implementation
                # Assume slip surface ends at tunnel bottom
                d_y = D_t
                theta_d = theta_i - np.pi/2  # Approximate
                
                # Radius at point d
                if phi_rad != 0:
                    r_0 = r_i / np.exp(theta_i * np.tan(phi_rad))
                    r_d_calc = r_0 * np.exp(theta_d * np.tan(phi_rad))
                else:
                    r_0 = r_i
                    r_d_calc = r_d
                
                eq2 = r_d - r_d_calc
                
                # Distance from center to point i
                eq3 = r_i - np.sqrt((i_x - O_x)**2 + (i_y - O_y)**2)
                
                # Angle condition at point d
                eq4 = np.tan(delta) - np.tan(phi_rad)  # Simplified
                
                return [eq1, eq2, eq3, eq4]
            
            # Initial guess
            O_x_init = i_x - H * np.cos(angle)
            O_y_init = i_y - H * np.sin(angle)
            r_i_init = H
            r_d_init = H * 1.5
            
            # Solve equations with user-specified parameters
            solution, info, ier, mesg = fsolve(
                equations, 
                [O_x_init, O_y_init, r_i_init, r_d_init],
                xtol=self.params.tolerance,
                maxfev=self.params.max_iterations,
                full_output=True
            )
            
            # Check convergence
            if ier != 1:
                return None
                
            O_x, O_y, r_i, r_d = solution
            
            # Calculate theta values
            theta_i = np.arctan2(i_y - O_y, i_x - O_x)
            theta_d = np.arctan2(D_t - O_y, 0 - O_x)  # Assume d is at x=0 for now
            
            return {
                'x_i': x_i,
                'center': {'x': O_x, 'y': O_y},
                'r_i': r_i,
                'r_d': r_d,
                'theta_i': theta_i,
                'theta_d': theta_d,
                'i': {'x': i_x, 'y': i_y}
            }
            
        except Exception as e:
            return None
    
    def _calculate_forces(self, geometry: Dict, gamma: float, c: float, phi_rad: float, D_t: float) -> Dict:
        """
        Calculate forces acting on the slip mass.
        
        Returns:
            Dictionary containing weight W_h and surcharge load Q
        """
        # Calculate area of slip mass
        # This requires integration along the logarithmic spiral
        # Simplified calculation for initial implementation
        
        # Approximate area as sector
        r_i = geometry['r_i']
        r_d = geometry['r_d']
        theta_i = geometry['theta_i']
        theta_d = geometry['theta_d']
        
        # Area calculation using integration
        if phi_rad != 0:
            # For logarithmic spiral r = r_0 * exp(theta * tan(phi))
            r_0 = r_i / np.exp(theta_i * np.tan(phi_rad))
            
            def integrand(theta):
                r = r_0 * np.exp(theta * np.tan(phi_rad))
                return 0.5 * r**2
            
            area, _ = quad(integrand, theta_d, theta_i)
        else:
            # Circular arc
            area = 0.5 * r_i**2 * (theta_i - theta_d)
        
        # Weight of slip mass
        W_h = area * gamma
        
        # Width at surface (slip surface width)
        B_s = abs(geometry['x_i'])
        
        # Surcharge load calculation based on selected method
        if self.params.surcharge_method == SurchargeMethod.SIMPLE:
            # Simple method: just the weight of overburden
            Q = B_s * D_t * gamma
        else:
            # Terzaghi's earth pressure theory
            Q = self._calculate_terzaghi_surcharge(B_s, gamma, c, phi_rad, D_t)
        
        # Calculate centroids (simplified)
        # For sector, centroid is at 2/3 radius from center
        centroid_r = 2/3 * (r_i + r_d) / 2
        centroid_theta = (theta_i + theta_d) / 2
        
        centroid_x = geometry['center']['x'] + centroid_r * np.cos(centroid_theta)
        centroid_y = geometry['center']['y'] + centroid_r * np.sin(centroid_theta)
        
        return {
            'W_h': W_h,
            'Q': Q,
            'centroid': {'x': centroid_x, 'y': centroid_y},
            'area': area
        }
    
    def _calculate_support_pressure(self, geometry: Dict, forces: Dict, c: float, phi_rad: float) -> Optional[float]:
        """
        Calculate required support pressure P from moment equilibrium.
        """
        try:
            O_x = geometry['center']['x']
            O_y = geometry['center']['y']
            r_i = geometry['r_i']
            r_d = geometry['r_d']
            
            # Moment arms
            # Weight moment arm
            l_w = abs(forces['centroid']['x'] - O_x)
            
            # Surcharge moment arm (simplified)
            l_Q = abs(geometry['x_i'] - O_x)
            
            # Support pressure acts at tunnel center
            # Assume acts at height D_t + H/2
            P_y = self.params.geometry.tunnel_depth + self.params.geometry.height / 2
            l_p = abs(0 - O_x)  # Horizontal distance from O to tunnel centerline
            
            # Driving moment
            M_driving = forces['W_h'] * l_w + forces['Q'] * l_Q
            
            # Resistance moment from cohesion
            if phi_rad != 0:
                M_cohesion = c / (2 * np.tan(phi_rad)) * (r_i**2 - r_d**2)
            else:
                M_cohesion = c * r_i * (geometry['theta_i'] - geometry['theta_d'])
            
            # Required support pressure from moment equilibrium
            if l_p > 0:
                P = (M_driving - M_cohesion) / l_p
                return max(0, P / self.params.geometry.height)  # Convert to pressure (force per unit area)
            else:
                return None
                
        except Exception as e:
            return None
    
    def _calculate_terzaghi_surcharge(self, B_s: float, gamma: float, c: float, 
                                     phi_rad: float, D_t: float) -> float:
        """
        Calculate surcharge load using Terzaghi's earth pressure theory.
        
        Args:
            B_s: Slip surface width at ground surface [m]
            gamma: Unit weight [kN/m³]
            c: Cohesion [kPa]
            phi_rad: Friction angle [rad]
            D_t: Tunnel depth [m]
            
        Returns:
            Total surcharge load Q [kN/m]
        """
        # Convert cohesion to kN/m²
        c_kN = c  # Already in kPa = kN/m²
        
        # Side wall friction angle (assume equal to phi)
        delta_rad = phi_rad
        
        # Earth pressure coefficient (Rankine's active earth pressure)
        # K = tan²(45° - φ/2)
        K = np.tan(np.pi/4 - phi_rad/2) ** 2
        
        # Check for zero denominator
        denominator = 2 * K * np.tan(delta_rad)
        if abs(denominator) < 1e-10:
            # Fall back to simple method if denominator is too small
            return B_s * D_t * gamma
        
        # Terzaghi's formula for vertical pressure
        # p_v = (B_s * γ - 2c) / (2K * tan(δ)) * (1 - exp(-2K * tan(δ) * D_t / B_s))
        exponent_term = -denominator * D_t / B_s
        
        # Ensure numerical stability
        if exponent_term < -20:  # exp(-20) ≈ 2e-9
            exp_term = 0
        else:
            exp_term = np.exp(exponent_term)
        
        p_v = (B_s * gamma - 2 * c_kN) / denominator * (1 - exp_term)
        
        # Ensure non-negative pressure
        p_v = max(0, p_v)
        
        # Total surcharge load
        Q = p_v * B_s
        
        return Q
    
    def _calculate_safety_factor(self, P_max: float) -> Optional[float]:
        """Calculate safety factor if applicable."""
        # If external pressure is provided, calculate safety factor
        # For now, return None as this needs further specification
        return None