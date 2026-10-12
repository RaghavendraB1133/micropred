from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any

class PredictionRunRequest(BaseModel):
    zone_id: int = Field(..., description="Unique ID of the micro-zone", ge=1)
    horizon_hours: int = Field(24, description="Forecasting horizon in hours", ge=1, le=72)

class ZoneCreateRequest(BaseModel):
    zone_code: str = Field(..., min_length=2, max_length=32)
    name: str = Field(..., min_length=2, max_length=128)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    radius_km: Optional[float] = Field(5.0, ge=0.1, le=100.0)
    elevation_m: Optional[float] = Field(25.0, ge=-500.0, le=9000.0)
    topography: Optional[str] = Field("Coastal Plain")
    population_estimate: Optional[int] = Field(50000, ge=0)
    description: Optional[str] = None

class DatasetValidationSummary(BaseModel):
    filename: str
    is_valid: bool
    total_rows: int
    detected_columns: List[str]
    missing_required_columns: List[str]
    missing_value_percentages: Dict[str, float]
    duplicate_rows_count: int
    date_range_start: Optional[str]
    date_range_end: Optional[str]
    coordinate_bounds: Dict[str, Any]
    warnings: List[str]
    errors: List[str]
