# =========================================
# Load Distribution Tool Package
# =========================================
# Axle and Wheel Load Distribution Analysis Module for Rail Vehicles
#
# Purpose: Analyze load distribution across axles and wheels in rail vehicles
# to ensure safe operation and compliance with railway safety standards.
#
# Engineering Context:
# - Critical for rail vehicle stability and safety
# - Prevents wheel unloading and excessive load concentrations
# - Ensures even wear patterns across wheels and rails
# - Supports vehicle design optimization and safety certification
#
# Package Structure:
# - api.py: FastAPI router endpoints for load distribution calculations and report generation
# - core.py: Pure mathematical functions implementing load distribution algorithms
# - schemas.py: Pydantic models for input validation and type safety
# - service.py: Orchestration layer coordinating calculations and report formatting
# - validation.py: Input processing and validation logic with error handling
# - constants.py: Safety limits, configuration types, and engineering standards
# - reports/pdf_builder.py: Professional DOCX report generation with diagrams
#
# Dependencies:
# - FastAPI: Web framework for API endpoints
# - Pydantic: Data validation and serialization
# - python-docx: Professional document generation
# - Standard library: math, typing, datetime, os
#
# Usage:
# This package provides REST API endpoints for analyzing load distribution
# in rail vehicles and generating detailed engineering reports in DOCX format
# for safety compliance verification and vehicle design validation.