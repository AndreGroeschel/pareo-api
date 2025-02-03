"""Schemas for an investor with improved type safety and organization."""

from enum import Enum
from typing import Annotated, Any, ClassVar, TypedDict, cast

from pydantic import BaseModel, ConfigDict, Field, NonNegativeFloat, confloat, conint, model_validator


class InvestmentStage(str, Enum):
    """Enumeration of possible investment stages."""

    PRE_SEED = "Pre-Seed"
    SEED = "Seed"
    SERIES_A = "Series A"
    SERIES_B = "Series B"
    SERIES_C = "Series C"
    GROWTH = "Growth"


class InvestorStatus(str, Enum):
    """Enumeration of possible investor statuses."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DOMAIN_INACTIVE = "domain_inactive"


class CheckSize(BaseModel):
    """Financial information about investment check sizes."""

    model_config = ConfigDict(extra="ignore")

    min: float | None = None
    max: float | None = None
    currency: str | None = None
    display: str | None = None


class InvestmentDetails(BaseModel):
    """Details about investment preferences and criteria."""

    stages: list[InvestmentStage] = Field(default_factory=list)
    check_size: CheckSize = Field(default_factory=CheckSize)
    industries: list[str] = Field(default_factory=list)
    geographies: list[str] = Field(default_factory=list)


class FieldConfig(TypedDict, total=False):
    """Configuration for field processing."""

    normalize: bool
    structure_key: str


class StageNormalizer:
    """Handles normalization of investment stage values."""

    _STAGE_MAPPING: ClassVar[dict[str, str]] = {
        "preseed": InvestmentStage.PRE_SEED,
        "pre_seed": InvestmentStage.PRE_SEED,
        "seed": InvestmentStage.SEED,
        "seriesa": InvestmentStage.SERIES_A,
        "series_a": InvestmentStage.SERIES_A,
        "seriesb": InvestmentStage.SERIES_B,
        "series_b": InvestmentStage.SERIES_B,
        "seriesc": InvestmentStage.SERIES_C,
        "series_c": InvestmentStage.SERIES_C,
        "series_b_plus": InvestmentStage.SERIES_C,
        "growth": InvestmentStage.GROWTH,
    }

    _ALLOWED_STAGES: ClassVar[set[str]] = {
        InvestmentStage.PRE_SEED,
        InvestmentStage.SEED,
        InvestmentStage.SERIES_A,
        InvestmentStage.SERIES_B,
        InvestmentStage.GROWTH,
    }

    @classmethod
    def normalize(cls, stages: list[Any]) -> list[str]:
        """Normalize a list of investment stages to standardized values."""
        normalized: list[str] = []

        for stage in stages:
            if isinstance(stage, str):
                clean_stage = cls._clean_stage_string(stage)
                normalized_stage = cls._STAGE_MAPPING.get(clean_stage, stage)
                if normalized_stage in cls._ALLOWED_STAGES:
                    normalized.append(normalized_stage)

        return normalized

    @staticmethod
    def _clean_stage_string(stage: str) -> str:
        """Clean and standardize a stage string for matching."""
        return stage.strip().lower().replace("-", "").replace("_", "").replace(" ", "")


class ListProcessor:
    """Handles processing of list fields with various formats."""

    @staticmethod
    def process_string_value(value: str) -> list[str]:
        """Process a string value into a list."""
        if "," in value:
            return [s.strip() for s in value.split(",")]
        return [value]

    @staticmethod
    def process_structured_data(raw_value: dict[str, list[Any]], structure_key: str) -> list[Any]:
        """Process structured data with a specific key."""
        return raw_value.get(structure_key, [])

    @staticmethod
    def clean_list_items(items: list[Any]) -> list[Any]:
        """Clean list items, handling strings specially."""
        return [item.strip() if isinstance(item, str) else item for item in items if item is not None]


class Investor(BaseModel):
    """Primary investor information model."""

    model_config = ConfigDict(extra="ignore")

    # Basic Information
    id: int | None = None
    name: str = Field(default="Unknown Investor")
    website: str | None = None
    description: str | None = None
    investment_thesis: str | None = None

    # Investment Criteria
    investment_stages: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    geographies: list[str] = Field(default_factory=list)
    check_size: CheckSize | None = None

    # Contact Information
    contact_preference: str | None = None
    contact_form_url: str | None = None
    contact_email: str | None = None

    # Metadata
    last_updated: str | None = None
    status: InvestorStatus = InvestorStatus.ACTIVE
    investment_details: InvestmentDetails = Field(default_factory=InvestmentDetails)

    @model_validator(mode="before")
    def transform_structure(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Transform and normalizes the input data structure."""
        # Handle field aliases
        cls._handle_field_aliases(values)

        # Process list fields
        list_fields: dict[str, FieldConfig] = {
            "investment_stages": {"normalize": True},
            "industries": {},
            "geographies": {},
            "team": {"structure_key": "members"},
            "portfolio": {},
        }

        for field, config in list_fields.items():
            values = cls._process_field(values, field, config)

        return values

    @classmethod
    def _handle_field_aliases(cls, values: dict[str, Any]) -> None:
        """Handle field name aliases in the input data."""
        if "stage" in values:
            values["investment_stages"] = values.pop("stage")
        if "investor_name" in values:
            values["name"] = values.pop("investor_name")

    @classmethod
    def _process_field(
        cls,
        values: dict[str, Any],
        field_name: str,
        config: FieldConfig,
    ) -> dict[str, Any]:
        """Process a single field according to its configuration."""
        raw_value: Any = values.get(field_name)

        # Handle null values
        if raw_value is None:
            values[field_name] = []
            return values

        # Initialize as list
        processed_value: list[Any]

        # Process structured data
        if isinstance(raw_value, dict):
            structure_key = config.get("structure_key")
            if structure_key is not None:
                processed_value = ListProcessor.process_structured_data(
                    cast(dict[str, list[Any]], raw_value), structure_key
                )
            else:
                processed_value = []
        # Process string values
        elif isinstance(raw_value, str):
            processed_value = ListProcessor.process_string_value(raw_value)
        # Handle existing lists
        elif isinstance(raw_value, list):
            processed_value = raw_value
        # Convert any other value to list
        else:
            processed_value = [raw_value] if raw_value is not None else []

        # Normalize stages if required
        normalize = config.get("normalize")
        if normalize and field_name == "investment_stages":
            processed_value = StageNormalizer.normalize(processed_value)

        # Clean and set the final value
        values[field_name] = ListProcessor.clean_list_items(processed_value)
        return values


class CompanyContext(BaseModel):
    """Company information for matching analysis."""

    company_name: str
    value_prop: str
    key_benefits: list[str]
    stage: str
    location: str
    check_request_size: str


class InvestorMatchRequest(BaseModel):
    """Request model for an investor match request."""

    prompt: Annotated[str, Field(..., min_length=3, examples=["Seed stage AI investors in Europe"])]
    threshold: Annotated[float, confloat(ge=0.0, le=1.0)] = Field(
        0.7, description="Similarity threshold between 0.0 and 1.0"
    )
    max_entries: Annotated[int, conint(ge=1, le=100)] = Field(10, description="Maximum number of investors to return")
    company_context: CompanyContext | None = Field(None, description="Optional company context for better matching")


class InvestorMatchResponse(BaseModel):
    """Response model for an investor match request."""

    name: str
    match_score: NonNegativeFloat
    reason: str
    website: str | None
    description: str | None
    stage: list[str]
    industries: list[str]
    check_size: str | None
    geographies: list[str]
