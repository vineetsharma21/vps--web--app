# =========================================
# Tractive Effort Tool Package
# =========================================
# Train Tractive Effort and Power Calculation Module for Railway Vehicles
#
# Purpose: Calculate the force and electrical power required to move trains,
# including rolling resistance, gradient resistance, curvature resistance,
# and overhead electric (OHE) power requirements for railway operations.
#
# Engineering Context:
# - Critical for locomotive sizing and electric power system design
# - Determines minimum tractive effort needed for train movement
# - Supports railway electrification planning and locomotive procurement
# - Essential for train performance optimization and energy efficiency
#
# Package Structure:
# - api.py: FastAPI router endpoints for tractive effort calculations and report generation
# - core.py: Pure mathematical functions implementing physics-based traction formulas
# - schemas.py: Pydantic models for input validation and type safety
# - service.py: Orchestration layer coordinating calculations and report formatting
# - validation.py: Input processing and validation logic with error handling
# - constants.py: Physical constants, resistance coefficients, and electrical parameters
# - reports/pdf_builder.py: Professional DOCX report generation with detailed analysis
#
# Dependencies:
# - FastAPI: Web framework for API endpoints
# - Pydantic: Data validation and serialization
# - python-docx: Professional document generation
# - Standard library: math, typing, datetime
#
# Usage:
# This package provides REST API endpoints for calculating tractive effort
# requirements and generating detailed engineering reports in DOCX format
# for railway design, locomotive specification, and power system planning.