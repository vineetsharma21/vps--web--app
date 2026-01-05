# =========================================
# Vehicle Performance Tool Package
# =========================================
# Comprehensive Locomotive and Vehicle Performance Analysis Module
#
# Purpose: Analyze locomotive performance characteristics including tractive effort,
# speed capabilities, gear optimization, and performance curves across various
# operating conditions for railway vehicle design and optimization.
#
# Engineering Context:
# - Critical for locomotive procurement and performance specification
# - Supports gear ratio optimization and transmission design
# - Enables performance prediction across different terrains and loads
# - Essential for train performance simulation and energy optimization
#
# Package Structure:
# - api.py: FastAPI router endpoints for performance calculations and report generation
# - core.py: Pure mathematical functions implementing physics-based performance formulas
# - schemas.py: Pydantic models for input validation and type safety
# - service.py: Orchestration layer coordinating calculations and report formatting
# - validation.py: Input processing and validation logic with error handling
# - constants.py: Physical constants, default values, and conversion factors
# - reports/pdf_builder.py: Professional DOCX report generation with performance curves
#
# Dependencies:
# - FastAPI: Web framework for API endpoints
# - Pydantic: Data validation and serialization
# - python-docx: Professional document generation
# - numpy: Numerical computations and interpolation
# - Standard library: math, typing, datetime, io
#
# Usage:
# This package provides REST API endpoints for comprehensive locomotive performance
# analysis and generates detailed engineering reports in DOCX format for vehicle
# design, procurement specifications, and performance optimization studies.