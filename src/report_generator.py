"""Report generation module for tunnel stability analysis results."""
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import plotly.graph_objects as go
import pandas as pd
from src.models import MurayamaInput, MurayamaResult


class ReportGenerator:
    """Generate PDF reports for Murayama analysis results."""
    
    def __init__(self, input_params: MurayamaInput, result: MurayamaResult):
        """Initialize report generator."""
        self.input_params = input_params
        self.result = result
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=12
        ))
    
    def generate_pdf(self) -> bytes:
        """Generate PDF report and return as bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        story.append(Paragraph("Murayama Tunnel Stability Analysis Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        
        # Date and project info
        story.append(Paragraph(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Input parameters section
        story.append(Paragraph("1. Input Parameters", self.styles['CustomHeading']))
        story.extend(self._create_input_table())
        story.append(Spacer(1, 20))
        
        # Results section
        story.append(Paragraph("2. Analysis Results", self.styles['CustomHeading']))
        story.extend(self._create_results_summary())
        story.append(Spacer(1, 20))
        
        # Safety assessment
        story.append(Paragraph("3. Safety Assessment", self.styles['CustomHeading']))
        story.extend(self._create_safety_assessment())
        story.append(Spacer(1, 20))
        
        # Data table
        story.append(Paragraph("4. P-B Curve Data", self.styles['CustomHeading']))
        story.extend(self._create_data_table())
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _create_input_table(self):
        """Create input parameters table."""
        data = [
            ['Parameter', 'Value', 'Unit'],
            ['Tunnel height (H)', f'{self.input_params.geometry.height:.1f}', 'm'],
            ['Initial radius (r₀)', f'{self.input_params.geometry.r0:.1f}', 'm'],
            ['Unit weight (γ)', f'{self.input_params.soil.gamma:.1f}', 'kN/m³'],
            ['Cohesion (c)', f'{self.input_params.soil.c:.1f}', 'kPa'],
            ['Friction angle (φ)', f'{self.input_params.soil.phi:.1f}', '°'],
            ['Water pressure (u)', f'{self.input_params.loading.u:.1f}', 'kPa'],
            ['Surcharge (σᵥ)', f'{self.input_params.loading.sigma_v:.1f}', 'kPa'],
        ]
        
        table = Table(data, colWidths=[6*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return [table]
    
    def _create_results_summary(self):
        """Create results summary."""
        elements = []
        
        # Key results
        data = [
            ['Parameter', 'Value'],
            ['Maximum resistance (P_max)', f'{self.result.P_max:.1f} kN/m'],
            ['Critical sliding width (B_critical)', f'{self.result.B_critical:.2f} m'],
        ]
        
        if self.result.safety_factor:
            data.append(['Safety factor', f'{self.result.safety_factor:.2f}'])
        
        table = Table(data, colWidths=[8*cm, 4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        return elements
    
    def _create_safety_assessment(self):
        """Create safety assessment section."""
        elements = []
        
        if self.result.safety_factor:
            fs = self.result.safety_factor
            if fs >= 1.5:
                assessment = "SAFE - The tunnel face is stable with adequate safety margin."
                color = colors.green
            elif fs >= 1.2:
                assessment = "MARGINAL - The tunnel face stability is marginal. Additional support measures recommended."
                color = colors.orange
            else:
                assessment = "UNSAFE - The tunnel face is unstable. Immediate support measures required."
                color = colors.red
            
            para = Paragraph(f"Safety Factor: {fs:.2f}", self.styles['Normal'])
            elements.append(para)
            
            style = ParagraphStyle(
                'Assessment',
                parent=self.styles['Normal'],
                textColor=color,
                fontSize=12,
                spaceAfter=12
            )
            elements.append(Paragraph(assessment, style))
        else:
            elements.append(Paragraph(
                "No external load specified. Safety factor cannot be calculated.",
                self.styles['Normal']
            ))
        
        return elements
    
    def _create_data_table(self):
        """Create P-B curve data table (showing selected points)."""
        elements = []
        
        # Select representative points (every 5th point to keep table manageable)
        indices = list(range(0, len(self.result.B_values), max(1, len(self.result.B_values) // 20)))
        if len(self.result.B_values) - 1 not in indices:
            indices.append(len(self.result.B_values) - 1)
        
        data = [['B [m]', 'P [kN/m]']]
        for i in indices:
            data.append([
                f'{self.result.B_values[i]:.2f}',
                f'{self.result.P_values[i]:.1f}'
            ])
        
        table = Table(data, colWidths=[4*cm, 4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(
            f"Note: Showing {len(data)-1} representative points out of {len(self.result.B_values)} total data points.",
            self.styles['Italic']
        ))
        
        return elements


def generate_markdown_report(input_params: MurayamaInput, result: MurayamaResult) -> str:
    """Generate a markdown report of the analysis results."""
    report = f"""# Murayama Tunnel Stability Analysis Report

## Analysis Date
{datetime.now().strftime('%Y-%m-%d %H:%M')}

## 1. Input Parameters

### Tunnel Geometry
- Height (H): {input_params.geometry.height:.1f} m
- Tunnel depth (D_t): {input_params.geometry.tunnel_depth:.1f} m

### Soil Parameters
- Unit weight (γ): {input_params.soil.gamma:.1f} kN/m³
- Cohesion (c): {input_params.soil.c:.1f} kPa
- Friction angle (φ): {input_params.soil.phi:.1f}°

### Loading Conditions
- Water pressure (u): {input_params.loading.u:.1f} kPa

## 2. Analysis Results

### Key Results
- **Maximum support pressure (P_max)**: {result.P_max:.1f} kN/m²
- **Critical position (x_critical)**: {result.x_critical:.1f} m
"""
    
    if result.safety_factor:
        report += f"- **Safety factor**: {result.safety_factor:.2f}\n"
        
        report += "\n### Safety Assessment\n"
        if result.safety_factor >= 1.5:
            report += "✅ **SAFE** - The tunnel face is stable with adequate safety margin.\n"
        elif result.safety_factor >= 1.2:
            report += "⚠️ **MARGINAL** - The tunnel face stability is marginal. Additional support measures recommended.\n"
        else:
            report += "❌ **UNSAFE** - The tunnel face is unstable. Immediate support measures required.\n"
    
    report += "\n## 3. Recommendations\n"
    report += "Based on the analysis results, the following recommendations are made:\n"
    
    if result.safety_factor and result.safety_factor < 1.5:
        report += "- Consider additional support measures such as face bolting or grouting\n"
        report += "- Monitor face deformation closely during excavation\n"
        report += "- Review and potentially improve soil parameters through additional investigation\n"
    else:
        report += "- Continue with standard excavation procedures\n"
        report += "- Maintain regular monitoring as per standard practice\n"
    
    report += "\n---\n"
    report += "*Generated by Murayama Tunnel Stability Analysis System*\n"
    
    return report