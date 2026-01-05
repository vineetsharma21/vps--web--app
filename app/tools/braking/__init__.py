"""
Braking Tool Package
===================
Purpose:
    Rail and road vehicle braking force calculation tool.
    Calculates required braking forces, deceleration, and stopping distances
    according to DIN EN 15746-2:2021-05 standards for rail vehicles.
Layer:
    Backend / Tools / Braking
Features:
    - Rail mode: Calculates braking forces for various speeds and gradients
    - Rail+Road mode: Combined rail and road braking calculations
    - Compliance checking against EN standards
    - PDF report generation with LaTeX templates
    - Unit conversions for gradients (degrees, 1 in G, percentage)
Components:
    - api.py: FastAPI router endpoints
    - core.py: Pure mathematical calculations
    - service.py: Business logic orchestration
    - schemas.py: Pydantic input validation models
    - validation.py: Input validation and processing
    - constants.py: EN standard braking data and limits
    - units.py: Unit conversion utilities
    - reports/pdf_builder.py: PDF report generation
"""

# Braking Tool Package Initialization