# =========================================
# Tools API Dispatcher Router Module
# =========================================
# Central routing hub for all engineering calculation tools and legacy API compatibility.
#
# Purpose: Acts as the main entry point for all engineering calculation tools,
# routing requests to appropriate tool-specific APIs while maintaining backward
# compatibility with legacy endpoint URLs used by existing HTML frontends.
#
# Architecture Overview:
# - Modular tool routing with dedicated prefixes
# - Legacy endpoint preservation for seamless upgrades
# - Unified error handling and response formatting
# - Tool-specific API delegation and orchestration
#
# Tool Integration:
# - Braking calculations (force, distance, performance)
# - Qmax analysis (maximum power optimization)
# - Hydraulic system design and simulation
# - Load distribution analysis
# - Tractive effort calculations
# - Vehicle performance evaluation
#
# API Structure:
# Modern Endpoints (Recommended):
# - POST /braking/calculate - Braking force analysis
# - POST /qmax/calculate - Power optimization
# - POST /hydraulic/calculate - Hydraulic system design
# - POST /load-distribution/calculate - Load analysis
# - POST /tractive-effort/calculate - Traction calculations
# - POST /vehicle-performance/calculate - Performance analysis
#
# Legacy Endpoints (Backward Compatibility):
# - POST /braking_calculate - Old braking endpoint
# - POST /calculate_qmax - Old Qmax endpoint
# - POST /calculate - Old hydraulic endpoint
# - POST /calculate_load_distribution - Old load distribution
# - POST /calculate_tractive_effort - Old tractive effort
# - POST /calculate_performance - Old vehicle performance
#
# Report Generation:
# - POST /download_braking_report - Braking analysis report
# - POST /download_qmax_report - Qmax analysis report
# - POST /download_report - Hydraulic report
# - POST /download_load_distribution_report - Load distribution report
# - POST /download_tractive_effort_report - Tractive effort report
# - POST /download_performance_report - Vehicle performance report
#
# Used by: Main FastAPI application, HTML frontend, external API clients
# Dependencies: Individual tool API modules, Pydantic for validation
# Migration: Legacy endpoints will be deprecated in future versions

from fastapi import APIRouter
from app.tools.braking.api import router as braking_router
from app.tools.qmax.api import router as qmax_router
from app.tools.hydraulic.api import router as hydraulic_router
from app.tools.load_distribution.api import router as load_distribution_router
from app.tools.tractive_effort.api import router as tractive_effort_router
from app.tools.vehicle_performance.api import router as vehicle_performance_router

# Create main tools router
router = APIRouter()

# =========================================
# MODERN TOOL API ROUTING
# =========================================
# Include all tool-specific routers with standardized prefixes
# This provides clean, organized API endpoints for each engineering tool

router.include_router(braking_router, prefix="/braking")
router.include_router(qmax_router, prefix="/qmax")
router.include_router(hydraulic_router, prefix="/hydraulic")
router.include_router(load_distribution_router, prefix="/load-distribution")
router.include_router(tractive_effort_router, prefix="/tractive-effort")
router.include_router(vehicle_performance_router, prefix="/vehicle-performance")

# =========================================
# LEGACY API COMPATIBILITY LAYER
# =========================================
# Backward compatibility endpoints to support existing HTML frontend
# These endpoints maintain the old URL patterns and data formats
# TODO: Deprecate these endpoints in future major version release

# =========================================
# BRAKING TOOL LEGACY ENDPOINTS
# =========================================
# Maintains compatibility with existing braking calculation HTML interface

@router.post("/braking_calculate")
async def legacy_braking_calculate(raw_input: dict):
    """
    Legacy braking calculation endpoint for backward compatibility.

    Preserves the original API contract used by the HTML frontend for braking
    force and distance calculations. Translates legacy input format to modern
    API structure and delegates to the braking tool service.

    Legacy Input Format:
    - Raw dictionary with braking parameters
    - May include inconsistent field names
    - Lacks modern validation and type safety

    Migration Path:
    - New implementations should use: POST /braking/calculate
    - Legacy format will be supported until deprecation notice
    - Frontend should be updated to use modern endpoints

    Braking Calculations:
    - Stopping force analysis
    - Braking distance calculations
    - Brake system performance evaluation
    - Safety factor assessments

    Parameters:
        raw_input (dict): Legacy braking calculation parameters
                         - Expected fields vary by calculation type
                         - May require format translation

    Returns:
        dict: Braking calculation results in legacy format
            {
                "stopping_force": 150000,
                "braking_distance": 45.2,
                "safety_factor": 1.8,
                ...
            }

    Raises:
        HTTPException (400): Invalid input parameters or calculation errors
                            - Missing required fields
                            - Invalid parameter values
                            - Mathematical calculation failures

    Example:
        >>> legacy_input = {
        ...     "vehicle_weight": 50000,
        ...     "initial_speed": 80,
        ...     "brake_efficiency": 0.85
        ... }
        >>> result = await legacy_braking_calculate(legacy_input)
        >>> print(f"Stopping distance: {result['braking_distance']} meters")
        Stopping distance: 45.2 meters

    Note:
        This endpoint performs input format translation to modern API.
        Consider migrating to POST /braking/calculate for new implementations.
        Legacy endpoints may be removed in future major versions.
    """
    from pydantic import BaseModel
    from typing import Optional, Dict
    from pydantic import Field

    # Define legacy input model for validation
    class LegacyBrakingInput(BaseModel):
        # Core braking parameters
        vehicle_weight: Optional[float] = Field(None, description="Vehicle total weight in kg")
        initial_speed: Optional[float] = Field(None, description="Initial speed in km/h")
        brake_efficiency: Optional[float] = Field(None, description="Brake system efficiency (0-1)")

        # Advanced parameters
        gradient: Optional[float] = Field(0, description="Road gradient in percent")
        wind_resistance: Optional[float] = Field(None, description="Wind resistance coefficient")
        rolling_resistance: Optional[float] = Field(None, description="Rolling resistance coefficient")

        # Brake system specifics
        brake_type: Optional[str] = Field("drum", description="Type of brake system")
        num_axles: Optional[int] = Field(None, description="Number of braked axles")

    try:
        # Validate and parse legacy input
        validated_input = LegacyBrakingInput(**raw_input)

        # Import braking service for calculation
        from app.tools.braking.service import BrakingCalculator
        from app.tools.braking.schemas import BrakingInput

        # Convert legacy format to modern schema
        modern_input = BrakingInput(
            vehicle_weight_kg=validated_input.vehicle_weight,
            initial_speed_kmh=validated_input.initial_speed,
            brake_efficiency=validated_input.brake_efficiency,
            gradient_percent=validated_input.gradient,
            wind_resistance=validated_input.wind_resistance,
            rolling_resistance=validated_input.rolling_resistance,
            brake_type=validated_input.brake_type,
            num_axles=validated_input.num_axles
        )

        # Perform calculation using modern service
        calculator = BrakingCalculator(modern_input)
        results = calculator.calculate_braking_force()

        # Return results in legacy format
        return {
            "stopping_force": results.get("stopping_force", 0),
            "braking_distance": results.get("braking_distance", 0),
            "safety_factor": results.get("safety_factor", 1.0),
            "calculation_status": "success"
        }

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Braking calculation failed: {str(e)}")

@router.post("/download_braking_report")
async def legacy_braking_report(raw_input):
    """
    Legacy braking report generation endpoint for backward compatibility.

    Generates formatted braking analysis reports in DOCX format using the
    legacy input format. Maintains compatibility with existing HTML frontend
    report download functionality.

    Report Contents:
    - Complete braking force analysis
    - Stopping distance calculations
    - Safety factor assessments
    - Brake system performance metrics
    - Engineering recommendations

    File Format:
    - Microsoft Word DOCX format
    - Professional engineering report layout
    - Tables, charts, and formatted text
    - Timestamped and version controlled

    Parameters:
        raw_input (dict): Legacy braking parameters for report generation

    Returns:
        StreamingResponse: DOCX file download
                          - Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
                          - Content-Disposition: attachment; filename=Braking_Report.docx

    Raises:
        HTTPException (400): Invalid input or calculation errors
        HTTPException (500): Report generation failures

    Example:
        >>> input_data = {
        ...     "vehicle_weight": 50000,
        ...     "initial_speed": 80,
        ...     "brake_efficiency": 0.85
        ... }
        >>> # Returns DOCX file download response
        >>> response = await legacy_braking_report(input_data)

    Note:
        Report generation may take several seconds for complex calculations.
        Modern endpoint: POST /braking/download-report
    """
    from fastapi.responses import StreamingResponse

    try:
        # Reuse the calculation logic from legacy endpoint
        calc_result = await legacy_braking_calculate(raw_input)

        # Generate report using modern service
        from app.tools.braking.reports.pdf_builder import create_braking_docx_report

        # Convert legacy input to modern format for report
        modern_input = {
            "vehicle_weight_kg": raw_input.get("vehicle_weight", 0),
            "initial_speed_kmh": raw_input.get("initial_speed", 0),
            "brake_efficiency": raw_input.get("brake_efficiency", 0.8),
            "gradient_percent": raw_input.get("gradient", 0),
            "brake_type": raw_input.get("brake_type", "drum"),
            "num_axles": raw_input.get("num_axles", 2)
        }

        # Create report stream
        report_stream = create_braking_docx_report(modern_input, {"results": calc_result})

        return StreamingResponse(
            report_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=Braking_Report.docx"}
        )

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

# =========================================
# QMAX TOOL LEGACY ENDPOINTS
# =========================================
# Maintains compatibility with existing Qmax analysis HTML interface

@router.post("/calculate_qmax")
async def legacy_qmax_calculate(raw_input: dict):
    """
    Legacy Qmax calculation endpoint for backward compatibility.

    Preserves the original API contract for maximum power optimization analysis.
    Translates legacy input format to modern Qmax tool API structure.

    Qmax Analysis:
    - Maximum power point determination
    - Engine performance optimization
    - Power curve analysis
    - Efficiency calculations

    Parameters:
        raw_input (dict): Legacy Qmax calculation parameters

    Returns:
        dict: Qmax analysis results in legacy format

    Note:
        Modern endpoint: POST /qmax/calculate
    """
    from pydantic import BaseModel
    from typing import Optional

    class LegacyQmaxInput(BaseModel):
        engine_power: Optional[float] = None
        max_rpm: Optional[float] = None
        gear_ratio: Optional[float] = None
        vehicle_weight: Optional[float] = None

    try:
        validated_input = LegacyQmaxInput(**raw_input)

        # Import modern Qmax service
        from app.tools.qmax.service import QmaxCalculator
        from app.tools.qmax.schemas import QmaxInput

        modern_input = QmaxInput(
            engine_power_kw=validated_input.engine_power,
            max_rpm=validated_input.max_rpm,
            gear_ratio=validated_input.gear_ratio,
            vehicle_weight_kg=validated_input.vehicle_weight
        )

        calculator = QmaxCalculator(modern_input)
        results = calculator.calculate_qmax()

        return {
            "qmax_value": results.get("qmax", 0),
            "optimal_rpm": results.get("optimal_rpm", 0),
            "power_output": results.get("power_output", 0),
            "calculation_status": "success"
        }

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Qmax calculation failed: {str(e)}")

@router.post("/download_qmax_report")
async def legacy_qmax_report(raw_input: dict):
    """
    Legacy Qmax report generation endpoint.

    Generates DOCX reports for Qmax analysis using legacy input format.

    Parameters:
        raw_input (dict): Legacy Qmax parameters

    Returns:
        StreamingResponse: DOCX file download

    Note:
        Modern endpoint: POST /qmax/download-report
    """
    from fastapi.responses import StreamingResponse

    try:
        calc_result = await legacy_qmax_calculate(raw_input)

        from app.tools.qmax.reports.pdf_builder import create_qmax_docx_report

        modern_input = {
            "engine_power_kw": raw_input.get("engine_power", 0),
            "max_rpm": raw_input.get("max_rpm", 0),
            "gear_ratio": raw_input.get("gear_ratio", 1),
            "vehicle_weight_kg": raw_input.get("vehicle_weight", 0)
        }

        report_stream = create_qmax_docx_report(modern_input, {"results": calc_result})

        return StreamingResponse(
            report_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=Qmax_Report.docx"}
        )

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

# =========================================
# HYDRAULIC TOOL LEGACY ENDPOINTS
# =========================================
# Maintains compatibility with existing hydraulic system HTML interface

@router.post("/calculate")
async def legacy_hydraulic_calculate(raw_input: dict):
    """
    Legacy hydraulic calculation endpoint for backward compatibility.

    Preserves the original API contract for hydraulic system design and analysis.
    Supports pressure, flow, and power calculations for hydraulic systems.

    Hydraulic Analysis:
    - Pump performance calculations
    - Pressure drop analysis
    - Flow rate optimization
    - Power requirements assessment

    Parameters:
        raw_input (dict): Legacy hydraulic calculation parameters

    Returns:
        dict: Hydraulic analysis results in legacy format

    Note:
        Modern endpoint: POST /hydraulic/calculate
    """
    from pydantic import BaseModel
    from typing import Optional

    class LegacyHydraulicInput(BaseModel):
        flow_rate: Optional[float] = None
        pressure: Optional[float] = None
        pump_efficiency: Optional[float] = None
        system_pressure: Optional[float] = None

    try:
        validated_input = LegacyHydraulicInput(**raw_input)

        from app.tools.hydraulic.service import HydraulicCalculator
        from app.tools.hydraulic.schemas import HydraulicInput

        modern_input = HydraulicInput(
            flow_rate_lpm=validated_input.flow_rate,
            pressure_bar=validated_input.pressure,
            pump_efficiency=validated_input.pump_efficiency,
            system_pressure_bar=validated_input.system_pressure
        )

        calculator = HydraulicCalculator(modern_input)
        results = calculator.calculate_hydraulic_performance()

        return {
            "power_requirement": results.get("power_kw", 0),
            "pressure_drop": results.get("pressure_drop", 0),
            "flow_efficiency": results.get("efficiency", 0),
            "calculation_status": "success"
        }

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Hydraulic calculation failed: {str(e)}")

@router.post("/download_report")
async def legacy_hydraulic_report(raw_input: dict):
    """
    Legacy hydraulic report generation endpoint.

    Generates DOCX reports for hydraulic system analysis.

    Parameters:
        raw_input (dict): Legacy hydraulic parameters

    Returns:
        StreamingResponse: DOCX file download

    Note:
        Modern endpoint: POST /hydraulic/download-report
    """
    from fastapi.responses import StreamingResponse

    try:
        calc_result = await legacy_hydraulic_calculate(raw_input)

        from app.tools.hydraulic.reports.pdf_builder import create_hydraulic_docx_report

        modern_input = {
            "flow_rate_lpm": raw_input.get("flow_rate", 0),
            "pressure_bar": raw_input.get("pressure", 0),
            "pump_efficiency": raw_input.get("pump_efficiency", 0.8),
            "system_pressure_bar": raw_input.get("system_pressure", 0)
        }

        report_stream = create_hydraulic_docx_report(modern_input, {"results": calc_result})

        return StreamingResponse(
            report_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=Hydraulic_Report.docx"}
        )

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

# =========================================
# LOAD DISTRIBUTION TOOL LEGACY ENDPOINTS
# =========================================
# Maintains compatibility with existing load distribution HTML interface

@router.post("/calculate_load_distribution")
async def legacy_load_distribution_calculate(raw_input: dict):
    """
    Legacy load distribution calculation endpoint.

    Preserves API contract for axle load analysis and weight distribution
    calculations across vehicle axles.

    Load Distribution Analysis:
    - Axle weight calculations
    - Load balance optimization
    - Center of gravity analysis
    - Weight transfer assessment

    Parameters:
        raw_input (dict): Legacy load distribution parameters

    Returns:
        dict: Load distribution results in legacy format

    Note:
        Modern endpoint: POST /load-distribution/calculate
    """
    from pydantic import BaseModel
    from typing import Optional, List

    class LegacyLoadDistributionInput(BaseModel):
        total_weight: Optional[float] = None
        wheelbase: Optional[float] = None
        cg_position: Optional[float] = None
        num_axles: Optional[int] = None

    try:
        validated_input = LegacyLoadDistributionInput(**raw_input)

        from app.tools.load_distribution.service import LoadDistributionCalculator
        from app.tools.load_distribution.schemas import LoadDistributionInput

        modern_input = LoadDistributionInput(
            total_weight_kg=validated_input.total_weight,
            wheelbase_m=validated_input.wheelbase,
            cg_position_m=validated_input.cg_position,
            num_axles=validated_input.num_axles
        )

        calculator = LoadDistributionCalculator(modern_input)
        results = calculator.calculate_load_distribution()

        return {
            "axle_loads": results.get("axle_loads", []),
            "load_balance": results.get("balance_ratio", 0),
            "cg_height": results.get("cg_height", 0),
            "calculation_status": "success"
        }

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Load distribution calculation failed: {str(e)}")

@router.post("/download_load_distribution_report")
async def legacy_load_distribution_report(raw_input: dict):
    """
    Legacy load distribution report generation endpoint.

    Generates DOCX reports for load distribution analysis.

    Parameters:
        raw_input (dict): Legacy load distribution parameters

    Returns:
        StreamingResponse: DOCX file download

    Note:
        Modern endpoint: POST /load-distribution/download-report
    """
    from fastapi.responses import StreamingResponse

    try:
        calc_result = await legacy_load_distribution_calculate(raw_input)

        from app.tools.load_distribution.reports.pdf_builder import create_load_distribution_docx_report

        modern_input = {
            "total_weight_kg": raw_input.get("total_weight", 0),
            "wheelbase_m": raw_input.get("wheelbase", 0),
            "cg_position_m": raw_input.get("cg_position", 0),
            "num_axles": raw_input.get("num_axles", 2)
        }

        report_stream = create_load_distribution_docx_report(modern_input, {"results": calc_result})

        return StreamingResponse(
            report_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=Load_Distribution_Report.docx"}
        )

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

# =========================================
# TRACTIVE EFFORT TOOL LEGACY ENDPOINTS
# =========================================
# Maintains compatibility with existing tractive effort HTML interface

@router.post("/calculate_tractive_effort")
async def legacy_tractive_effort_calculate(raw_input: dict):
    """
    Legacy tractive effort calculation endpoint.

    Preserves API contract for locomotive tractive force and pulling capacity
    analysis across different operating conditions.

    Tractive Effort Analysis:
    - Maximum pulling force calculations
    - Speed vs tractive effort curves
    - Gear ratio optimization
    - Adhesion limit assessment

    Parameters:
        raw_input (dict): Legacy tractive effort parameters

    Returns:
        dict: Tractive effort results in legacy format

    Note:
        Modern endpoint: POST /tractive-effort/calculate
    """
    from pydantic import BaseModel
    from typing import Optional, List

    class LegacyTractiveEffortInput(BaseModel):
        loco_weight: Optional[float] = None
        power: Optional[float] = None
        gear_ratios: Optional[List[float]] = None
        adhesion: Optional[float] = None

    try:
        validated_input = LegacyTractiveEffortInput(**raw_input)

        from app.tools.tractive_effort.service import TractiveEffortCalculator
        from app.tools.tractive_effort.schemas import TractiveEffortInput

        modern_input = TractiveEffortInput(
            loco_weight_kg=validated_input.loco_weight,
            power_kw=validated_input.power,
            gear_ratios=validated_input.gear_ratios or [1.0],
            adhesion_coefficient=validated_input.adhesion
        )

        calculator = TractiveEffortCalculator(modern_input)
        results = calculator.calculate_tractive_effort()

        return {
            "tractive_effort": results.get("max_tractive_effort", 0),
            "optimal_gear": results.get("optimal_gear", 1),
            "speed_range": results.get("speed_range", []),
            "calculation_status": "success"
        }

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Tractive effort calculation failed: {str(e)}")

@router.post("/download_tractive_effort_report")
async def legacy_tractive_effort_report(raw_input: dict):
    """
    Legacy tractive effort report generation endpoint.

    Generates DOCX reports for tractive effort analysis.

    Parameters:
        raw_input (dict): Legacy tractive effort parameters

    Returns:
        StreamingResponse: DOCX file download

    Note:
        Modern endpoint: POST /tractive-effort/download-report
    """
    from fastapi.responses import StreamingResponse

    try:
        calc_result = await legacy_tractive_effort_calculate(raw_input)

        from app.tools.tractive_effort.reports.pdf_builder import create_tractive_effort_docx_report

        modern_input = {
            "loco_weight_kg": raw_input.get("loco_weight", 0),
            "power_kw": raw_input.get("power", 0),
            "gear_ratios": raw_input.get("gear_ratios", [1.0]),
            "adhesion_coefficient": raw_input.get("adhesion", 0.3)
        }

        report_stream = create_tractive_effort_docx_report(modern_input, {"results": calc_result})

        return StreamingResponse(
            report_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=Tractive_Effort_Report.docx"}
        )

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

# =========================================
# VEHICLE PERFORMANCE TOOL LEGACY ENDPOINTS
# =========================================
# Maintains compatibility with existing vehicle performance HTML interface

@router.post("/calculate_performance")
async def legacy_vehicle_performance_calculate(raw_input: dict):
    """
    Legacy vehicle performance calculation endpoint.

    Preserves API contract for comprehensive locomotive performance evaluation
    including tractive effort, speed analysis, and gear optimization.

    Vehicle Performance Analysis:
    - Tractive effort vs speed characteristics
    - Maximum speeds across different gears
    - Shunting capacity evaluation
    - Performance optimization recommendations

    Parameters:
        raw_input (dict): Legacy vehicle performance parameters

    Returns:
        dict: Performance analysis results in legacy format

    Note:
        Modern endpoint: POST /vehicle-performance/calculate
    """
    from pydantic import BaseModel
    from typing import Optional, List

    class LegacyVehiclePerformanceInput(BaseModel):
        loco_gvw: Optional[float] = None
        peak_power: Optional[float] = None
        wheel_dia: Optional[float] = None
        num_axles: Optional[int] = None
        gear_ratios: Optional[List[float]] = None
        friction_mu: Optional[float] = None

    try:
        validated_input = LegacyVehiclePerformanceInput(**raw_input)

        from app.tools.vehicle_performance.service import VehiclePerformanceCalculator
        from app.tools.vehicle_performance.schemas import VehiclePerformanceInput

        modern_input = VehiclePerformanceInput(
            loco_gvw=validated_input.loco_gvw,
            peak_power=validated_input.peak_power,
            wheel_dia=validated_input.wheel_dia,
            num_axles=validated_input.num_axles,
            rear_axle_ratio=3.5,  # Default value
            gear_ratios=validated_input.gear_ratios or [1.0],
            friction_mu=validated_input.friction_mu,
            max_speed=100,  # Default value
            max_slope=2.0,  # Default value
            max_curve=6.0,  # Default value
            shunting_load=2000  # Default value
        )

        calculator = VehiclePerformanceCalculator(modern_input)
        results = calculator.run_tractive_calculation()

        return {
            "traction_snapshot": results,
            "performance_data": {
                "max_speed": max([gear.get('max_speed_level_kmh', 0) for gear in results.values()]),
                "optimal_gear": 1,  # Simplified
                "efficiency": 0.85  # Placeholder
            },
            "calculation_status": "success"
        }

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Vehicle performance calculation failed: {str(e)}")

@router.post("/download_performance_report")
async def legacy_vehicle_performance_report(raw_input: dict):
    """
    Legacy vehicle performance report generation endpoint.

    Generates DOCX reports for comprehensive vehicle performance analysis.

    Parameters:
        raw_input (dict): Legacy vehicle performance parameters

    Returns:
        StreamingResponse: DOCX file download

    Note:
        Modern endpoint: POST /vehicle-performance/download-report
    """
    from fastapi.responses import StreamingResponse

    try:
        calc_result = await legacy_vehicle_performance_calculate(raw_input)

        from app.tools.vehicle_performance.reports.pdf_builder import create_vehicle_performance_docx_report

        modern_input = {
            "loco_gvw_kg": raw_input.get("loco_gvw", 0),
            "peak_power_kw": raw_input.get("peak_power", 0),
            "wheel_dia_m": raw_input.get("wheel_dia", 1.0),
            "num_axles": raw_input.get("num_axles", 4),
            "rear_axle_ratio": 3.5,
            "gear_ratios": raw_input.get("gear_ratios", [1.0]),
            "friction_mu": raw_input.get("friction_mu", 0.35),
            "max_speed_kmh": 100,
            "max_slope": 2.0,
            "max_curve": 6.0,
            "shunting_load_t": 2000
        }

        report_stream = create_vehicle_performance_docx_report(modern_input, calc_result)

        return StreamingResponse(
            report_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=Performance_Report.docx"}
        )

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
    """
    Legacy braking calculation endpoint (for backward compatibility).

    Parameters:
        raw_input (dict): Raw input data as expected by the old HTML frontend

    Returns:
        dict: Calculation results in legacy format

    Raises:
        HTTPException: On validation or calculation error
    """
    from pydantic import BaseModel
    from typing import Optional, Dict
    from pydantic import Field

    # Define the legacy BrakingRawInput schema
    class BrakingRawInput(BaseModel):
        mass_kg: float
        reaction_time: float
        num_wheels: int
        calc_mode: str
        rail_speed_input: str
        rail_gradient_input: str
        rail_gradient_type: str
        road_speed_input: Optional[str] = ""
        road_gradient_input: Optional[str] = ""
        road_gradient_type: Optional[str] = "Percentage (%)"
        mu: Optional[float] = 0.7
        doc_no: Optional[str] = ""
        made_by: Optional[str] = ""
        checked_by: Optional[str] = ""
        approved_by: Optional[str] = ""
        wheel_dia: Optional[float] = 0

    try:
        # Convert raw input to BrakingRawInput schema
        raw_schema = BrakingRawInput(**raw_input)
        # Convert to new BrakingInput schema
        from app.tools.braking.schemas import BrakingInput
        from app.tools.braking.validation import validate_braking_inputs
        from app.tools.braking.service import perform_braking_calculation
        new_schema = BrakingInput(**raw_schema.dict())
        inputs, inputs_raw = validate_braking_inputs(new_schema)
        results, context = perform_braking_calculation(inputs)
        return {"rows": results}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, str(e))

@router.post("/download_braking_report")
async def legacy_braking_report(raw_input):
    """
    Legacy braking report download endpoint (not yet implemented in new structure).

    Parameters:
        raw_input: Raw input data (unused)

    Raises:
        HTTPException: Always 501 (not implemented)
    """
    from fastapi import HTTPException
    raise HTTPException(501, "Braking report download not yet implemented in new structure")

# Qmax tool legacy routes
@router.post("/calculate_qmax")
async def legacy_qmax_calculate(raw_input: dict):
    """
    Legacy Qmax calculation endpoint (for backward compatibility).

    Parameters:
        raw_input (dict): Raw input data as expected by the old HTML frontend

    Returns:
        dict: Calculation results and report in legacy format

    Raises:
        HTTPException: On validation or calculation error
    """
    from pydantic import BaseModel
    from typing import Optional

    # Define the legacy QmaxRawInput schema
    class QmaxRawInput(BaseModel):
        d: str
        sigma_b_selection: str
        sigma_b_custom: str
        v_head: str

    try:
        # Convert raw input to QmaxRawInput schema
        raw_schema = QmaxRawInput(**raw_input)
        # Convert to new QmaxInput schema
        from app.tools.qmax.schemas import QmaxInput
        from app.tools.qmax.validation import validate_qmax_inputs
        from app.tools.qmax.service import perform_qmax_calculation
        new_schema = QmaxInput(**raw_schema.dict())
        inputs, inputs_raw = validate_qmax_inputs(new_schema)
        results, report = perform_qmax_calculation(inputs, inputs_raw)
        return {"report": report, "results": results}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, str(e))

@router.post("/download_qmax_report")
async def legacy_qmax_report(raw_input: dict):
    """
    Legacy Qmax report download endpoint (for backward compatibility).

    Parameters:
        raw_input (dict): Raw input data as expected by the old HTML frontend

    Raises:
        HTTPException: Always 501 (not implemented)
    """
    from pydantic import BaseModel
    from typing import Optional

    # Define the legacy QmaxRawInput schema
    class QmaxRawInput(BaseModel):
        d: str
        sigma_b_selection: str
        sigma_b_custom: str
        v_head: str

    try:
        # Convert raw input to QmaxRawInput schema
        raw_schema = QmaxRawInput(**raw_input)
        # Convert to new QmaxInput schema
        from app.tools.qmax.schemas import QmaxInput
        from app.tools.qmax.validation import validate_qmax_inputs
        from app.tools.qmax.service import perform_qmax_calculation
        from app.tools.qmax.reports.pdf_builder import create_qmax_docx_report
        from fastapi.responses import StreamingResponse
        new_schema = QmaxInput(**raw_schema.dict())
        inputs, inputs_raw = validate_qmax_inputs(new_schema)
        results, _ = perform_qmax_calculation(inputs, inputs_raw)
        stream = create_qmax_docx_report(results, inputs_raw)
        return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": "attachment; filename=Qmax_Report.docx"})
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, str(e))

# Hydraulic tool legacy routes
@router.post("/calculate")
async def legacy_hydraulic_calculate(raw_input: dict):
    """Legacy hydraulic calculation endpoint"""
    from pydantic import BaseModel
    from typing import Optional

    # Define the legacy HydraulicRawInput schema
    class HydraulicRawInput(BaseModel):
        calc_mode: str
        weight: str
        axles: str
        speed: str
        max_vehicle_rpm: str
        pto_gear_ratio: str
        engine_gear_ratio: str
        axle_gear_box_ratio: str
        slope_percent: str
        curve_degree: str
        wheel_diameter: str
        num_motors: str
        per_axle_motor: str
        pressure: str
        mech_eff_motor: str
        vol_eff_motor: str
        motor_disp_in: str
        max_motor_rpm: str
        vol_eff_pump: str
        pump_disp_in: str
        max_pump_rpm: str

    try:
        # Convert raw input to HydraulicRawInput schema
        raw_schema = HydraulicRawInput(**raw_input)
        # Convert to new HydraulicInput schema
        from app.tools.hydraulic.schemas import HydraulicInput
        from app.tools.hydraulic.validation import validate_hydraulic_inputs
        from app.tools.hydraulic.service import perform_hydraulic_calculation
        new_schema = HydraulicInput(**raw_schema.dict())
        inputs, inputs_raw = validate_hydraulic_inputs(new_schema)
        results, report = perform_hydraulic_calculation(inputs, inputs_raw)
        return {"report": report, "results": results}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, str(e))

@router.post("/download_report")
async def legacy_hydraulic_report(raw_input: dict):
    """Legacy hydraulic report download endpoint"""
    from pydantic import BaseModel
    from typing import Optional

    # Define the legacy HydraulicRawInput schema
    class HydraulicRawInput(BaseModel):
        calc_mode: str
        weight: str
        axles: str
        speed: str
        max_vehicle_rpm: str
        pto_gear_ratio: str
        engine_gear_ratio: str
        axle_gear_box_ratio: str
        slope_percent: str
        curve_degree: str
        wheel_diameter: str
        num_motors: str
        per_axle_motor: str
        pressure: str
        mech_eff_motor: str
        vol_eff_motor: str
        motor_disp_in: str
        max_motor_rpm: str
        vol_eff_pump: str
        pump_disp_in: str
        max_pump_rpm: str

    try:
        # Convert raw input to HydraulicRawInput schema
        raw_schema = HydraulicRawInput(**raw_input)
        # Convert to new HydraulicInput schema
        from app.tools.hydraulic.schemas import HydraulicInput
        from app.tools.hydraulic.validation import validate_hydraulic_inputs
        from app.tools.hydraulic.service import perform_hydraulic_calculation
        from app.tools.hydraulic.reports.pdf_builder import create_hydraulic_docx_report
        from fastapi.responses import StreamingResponse
        new_schema = HydraulicInput(**raw_schema.dict())
        inputs, inputs_raw = validate_hydraulic_inputs(new_schema)
        results, _ = perform_hydraulic_calculation(inputs, inputs_raw)
        stream = create_hydraulic_docx_report(inputs, results, inputs_raw)
        fname = "Hydraulic_Report.docx" if inputs['calc_mode'] == "calc_cc" else "Speed_Report.docx"
        return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f"attachment; filename={fname}"})
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, str(e))

# Load distribution tool legacy routes
@router.post("/calculate_load_distribution")
async def legacy_load_distribution_calculate(raw_input: dict):
    """Legacy load distribution calculation endpoint"""
    from pydantic import BaseModel
    from typing import Optional

    # Define the legacy LoadDistroRawInput schema
    class LoadDistroRawInput(BaseModel):
        config_type: str
        total_load: str
        front_percent: str
        q1_percent: str
        q3_percent: str

    try:
        # Convert raw input to LoadDistroRawInput schema
        raw_schema = LoadDistroRawInput(**raw_input)
        # Convert to new LoadDistributionInput schema
        from app.tools.load_distribution.schemas import LoadDistributionInput
        from app.tools.load_distribution.validation import validate_load_distribution_inputs
        from app.tools.load_distribution.service import perform_load_distro_calc, format_load_distro_steps
        new_schema = LoadDistributionInput(**raw_schema.dict())
        inputs, inputs_raw = validate_load_distribution_inputs(new_schema)
        results = perform_load_distro_calc(inputs['config_type'], inputs['total_load'], inputs['front_percent'], inputs['q1_percent'], inputs['q3_percent'])
        report = format_load_distro_steps(inputs, results)
        return {"report": report, "results": results}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, str(e))

@router.post("/download_load_distribution_report")
async def legacy_load_distribution_report(raw_input: dict):
    """Legacy load distribution report download endpoint"""
    from pydantic import BaseModel
    from typing import Optional

    # Define the legacy LoadDistroRawInput schema
    class LoadDistroRawInput(BaseModel):
        config_type: str
        total_load: str
        front_percent: str
        q1_percent: str
        q3_percent: str

    try:
        # Convert raw input to LoadDistroRawInput schema
        raw_schema = LoadDistroRawInput(**raw_input)
        # Convert to new LoadDistributionInput schema
        from app.tools.load_distribution.schemas import LoadDistributionInput
        from app.tools.load_distribution.validation import validate_load_distribution_inputs
        from app.tools.load_distribution.service import perform_load_distro_calc
        from app.tools.load_distribution.reports.pdf_builder import create_load_distro_docx
        from fastapi.responses import StreamingResponse
        new_schema = LoadDistributionInput(**raw_schema.dict())
        inputs, inputs_raw = validate_load_distribution_inputs(new_schema)
        results = perform_load_distro_calc(inputs['config_type'], inputs['total_load'], inputs['front_percent'], inputs['q1_percent'], inputs['q3_percent'])
        stream = create_load_distro_docx(inputs, results)
        return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": "attachment; filename=Load_Report.docx"})
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, str(e))

# Tractive effort tool legacy routes
@router.post("/calculate_tractive_effort")
async def legacy_tractive_effort_calculate(raw_input: dict):
    """Legacy tractive effort calculation endpoint"""
    from pydantic import BaseModel
    from typing import Optional

    # Define the legacy TractiveEffortRawInput schema
    class TractiveEffortRawInput(BaseModel):
        load: str
        loco_weight: str
        gradient: str
        curvature: str
        speed: str
        mode: str
        grad_type: str
        curvature_unit: str

    try:
        # Convert raw input to TractiveEffortRawInput schema
        raw_schema = TractiveEffortRawInput(**raw_input)
        # Convert to new TractiveEffortInput schema
        from app.tools.tractive_effort.schemas import TractiveEffortInput
        from app.tools.tractive_effort.validation import validate_tractive_effort_inputs
        from app.tools.tractive_effort.service import perform_te_calculation
        new_schema = TractiveEffortInput(**raw_schema.dict())
        inputs, inputs_raw = validate_tractive_effort_inputs(new_schema)
        results, report = perform_te_calculation(inputs, inputs_raw)
        return {"report": report, "results": results}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, str(e))

@router.post("/download_tractive_effort_report")
async def legacy_tractive_effort_report(raw_input: dict):
    """Legacy tractive effort report download endpoint"""
    from pydantic import BaseModel
    from typing import Optional

    # Define the legacy TractiveEffortRawInput schema
    class TractiveEffortRawInput(BaseModel):
        load: str
        loco_weight: str
        gradient: str
        curvature: str
        speed: str
        mode: str
        grad_type: str
        curvature_unit: str

    try:
        # Convert raw input to TractiveEffortRawInput schema
        raw_schema = TractiveEffortRawInput(**raw_input)
        # Convert to new TractiveEffortInput schema
        from app.tools.tractive_effort.schemas import TractiveEffortInput
        from app.tools.tractive_effort.validation import validate_tractive_effort_inputs
        from app.tools.tractive_effort.service import perform_te_calculation
        from app.tools.tractive_effort.reports.pdf_builder import create_te_docx_report
        from fastapi.responses import StreamingResponse
        new_schema = TractiveEffortInput(**raw_schema.dict())
        inputs, inputs_raw = validate_tractive_effort_inputs(new_schema)
        results, _ = perform_te_calculation(inputs, inputs_raw)
        stream = create_te_docx_report(inputs, results, inputs_raw)
        return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": "attachment; filename=TE_Report.docx"})
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, str(e))

# Vehicle performance tool legacy routes
@router.post("/calculate_performance")
async def legacy_vehicle_performance_calculate(raw_input: dict):
    """Legacy vehicle performance calculation endpoint"""
    from pydantic import BaseModel
    from typing import Optional, List

    # Define the legacy VehiclePerformanceRawInput schema
    class VehiclePerformanceRawInput(BaseModel):
        max_curve: str
        max_slope: str
        loco_gvw_kg: str
        max_speed_kmh: str
        num_axles: str
        rear_axle_ratio: str
        gear_ratios: str
        shunting_load_t: str
        peak_power_kw: str
        friction_mu: str
        wheel_dia_m: str
        min_rpm: str
        max_rpm: Optional[str] = None
        torque_curve: Optional[dict] = None

    try:
        # Map HTML field names to legacy schema field names
        mapped_input = {
            'max_curve': raw_input.get('max_curve'),
            'max_slope': raw_input.get('max_slope'),
            'loco_gvw_kg': raw_input.get('loco_gvw'),
            'max_speed_kmh': raw_input.get('max_speed'),
            'num_axles': raw_input.get('num_axles'),
            'rear_axle_ratio': raw_input.get('rear_axle_ratio'),
            'gear_ratios': raw_input.get('gear_ratios'),
            'shunting_load_t': raw_input.get('shunting_load'),
            'peak_power_kw': raw_input.get('peak_power'),
            'friction_mu': raw_input.get('friction_mu'),
            'wheel_dia_m': raw_input.get('wheel_dia'),
            'min_rpm': raw_input.get('min_rpm'),
            'max_rpm': raw_input.get('max_rpm'),
            'torque_curve': raw_input.get('torque_curve')
        }

        # Convert raw input to VehiclePerformanceRawInput schema
        raw_schema = VehiclePerformanceRawInput(**mapped_input)
        # Convert to new VehiclePerformanceInput schema
        from app.tools.vehicle_performance.schemas import VehiclePerformanceInput
        from app.tools.vehicle_performance.validation import validate_vehicle_performance_inputs
        from app.tools.vehicle_performance.service import VehiclePerformanceCalculator

        # Convert string inputs to proper types
        processed_input = {
            'max_curve': float(raw_schema.max_curve),
            'max_slope': float(raw_schema.max_slope),
            'loco_gvw': float(raw_schema.loco_gvw_kg),
            'max_speed': float(raw_schema.max_speed_kmh),
            'num_axles': int(raw_schema.num_axles),
            'rear_axle_ratio': float(raw_schema.rear_axle_ratio),
            'gear_ratios': [float(x.strip()) for x in raw_schema.gear_ratios.split(',')],
            'shunting_load': float(raw_schema.shunting_load_t),
            'peak_power': float(raw_schema.peak_power_kw),
            'friction_mu': float(raw_schema.friction_mu),
            'wheel_dia': float(raw_schema.wheel_dia_m),
            'min_rpm': int(raw_schema.min_rpm),
            'max_rpm': int(raw_schema.max_rpm) if raw_schema.max_rpm else None,
            'torque_curve': raw_schema.torque_curve
        }

        new_schema = VehiclePerformanceInput(**processed_input)
        inputs, inputs_raw = validate_vehicle_performance_inputs(new_schema)
        calculator = VehiclePerformanceCalculator(inputs)

        results = {
            'traction_snapshot': calculator.run_tractive_calculation(),
            'tractive_effort_graph': calculator.calculate_plot_data()['tractive_effort_plot'],
            'shunting_capability_graph': calculator.calculate_plot_data()['shunting_capability_plot'],
            'speed_vs_slope_table': calculator.calculate_speed_for_shunting_load()
        }

        return results
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, str(e))

@router.post("/download_performance_report")
async def legacy_vehicle_performance_report(raw_input: dict):
    """Legacy vehicle performance report download endpoint"""
    from pydantic import BaseModel
    from typing import Optional, List

    # Define the legacy VehiclePerformanceRawInput schema
    class VehiclePerformanceRawInput(BaseModel):
        max_curve: str
        max_slope: str
        loco_gvw_kg: str
        max_speed_kmh: str
        num_axles: str
        rear_axle_ratio: str
        gear_ratios: str
        shunting_load_t: str
        peak_power_kw: str
        friction_mu: str
        wheel_dia_m: str
        min_rpm: str
        max_rpm: Optional[str] = None
        torque_curve: Optional[dict] = None

    try:
        # Convert raw input to VehiclePerformanceRawInput schema
        raw_schema = VehiclePerformanceRawInput(**raw_input)
        # Convert to new VehiclePerformanceInput schema
        from app.tools.vehicle_performance.schemas import VehiclePerformanceInput
        from app.tools.vehicle_performance.validation import validate_vehicle_performance_inputs
        from app.tools.vehicle_performance.service import VehiclePerformanceCalculator
        from app.tools.vehicle_performance.reports.pdf_builder import create_vehicle_performance_docx_report
        from fastapi.responses import StreamingResponse

        # Convert string inputs to proper types
        processed_input = {
            'max_curve': float(raw_schema.max_curve),
            'max_slope': float(raw_schema.max_slope),
            'loco_gvw_kg': float(raw_schema.loco_gvw_kg),
            'max_speed_kmh': float(raw_schema.max_speed_kmh),
            'num_axles': int(raw_schema.num_axles),
            'rear_axle_ratio': float(raw_schema.rear_axle_ratio),
            'gear_ratios': [float(x.strip()) for x in raw_schema.gear_ratios.split(',')],
            'shunting_load_t': float(raw_schema.shunting_load_t),
            'peak_power_kw': float(raw_schema.peak_power_kw),
            'friction_mu': float(raw_schema.friction_mu),
            'wheel_dia_m': float(raw_schema.wheel_dia_m),
            'min_rpm': int(raw_schema.min_rpm),
            'max_rpm': int(raw_schema.max_rpm) if raw_schema.max_rpm else None,
            'torque_curve': raw_schema.torque_curve
        }

        new_schema = VehiclePerformanceInput(**processed_input)
        inputs, inputs_raw = validate_vehicle_performance_inputs(new_schema)
        calculator = VehiclePerformanceCalculator(inputs)

        # Get all results for the report
        results = {
            'traction_snapshot': calculator.run_tractive_calculation(),
            'plot_data': calculator.calculate_plot_data(),
            'speed_slope_table': calculator.calculate_speed_for_shunting_load()
        }

        stream = create_vehicle_performance_docx_report(inputs, results)
        return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": "attachment; filename=Performance_Report.docx"})
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, str(e))