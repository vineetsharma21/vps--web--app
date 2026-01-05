# =========================================
# Qmax Tool Package
# =========================================
# Maximum Axle Load Calculation Module for Rail Vehicles
#
# Purpose: Calculate maximum permissible axle loads for rail vehicles based on
# wheel diameter, rail bending stress limits, and vehicle speed parameters.
#
# Engineering Context:
# - Qmax calculations ensure rail integrity under dynamic loading conditions
# - Prevents rail bending stress from exceeding allowable limits
# - Critical for rail vehicle design and safety compliance
# - Used in railway engineering for axle load optimization
#
# Package Structure:
# - api.py: FastAPI router endpoints for Qmax calculations and report generation
# - core.py: Pure mathematical functions implementing Qmax engineering formulas
# - schemas.py: Pydantic models for input validation and type safety
# - service.py: Orchestration layer coordinating calculations and report formatting
# - validation.py: Input processing and validation logic with error handling
# - constants.py: Physical constants, conversion factors, and material properties
# - reports/pdf_builder.py: Professional DOCX report generation with formatting
#
# Dependencies:
# - FastAPI: Web framework for API endpoints
# - Pydantic: Data validation and serialization
# - python-docx: Professional document generation
# - Standard library: math, typing, datetime
#
# Usage:
# This package provides REST API endpoints for calculating maximum axle loads
# and generating detailed engineering reports in DOCX format for railway
# vehicle design and compliance verification.