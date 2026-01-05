"""
Hydraulic Tool Package
=====================
Purpose:
    Hydraulic motor and pump sizing calculations for rail vehicles.
    Calculates required motor displacement, pump specifications, and achievable speeds
    for hydraulic drive systems in locomotives and railcars.
Layer:
    Backend / Tools / Hydraulic
Features:
    - Displacement calculation: Motor/pump sizing for target speeds
    - Speed calculation: Achievable speeds for given motor/pump specs
    - Resistance calculations: Rolling, gradient, and curve resistances
    - Gear ratio optimization: Engine, PTO, and axle gear considerations
    - DOCX report generation with professional formatting
Components:
    - api.py: FastAPI router endpoints
    - core.py: Pure mathematical calculations
    - service.py: Business logic orchestration
    - schemas.py: Pydantic input validation models
    - validation.py: Input processing and validation
    - constants.py: Physical constants (gravity)
    - reports/pdf_builder.py: DOCX report generation
Calculation Modes:
    - calc_cc: Calculate motor displacement and pump requirements for target speed
    - calc_speed: Calculate achievable speeds for given motor/pump specifications
Units:
    - Weight: tonnes
    - Speed: km/h
    - Pressure: bar
    - Displacement: cc/rev
    - Flow: LPM
    - Efficiency: percentage
"""

# Hydraulic Tool Package Initialization