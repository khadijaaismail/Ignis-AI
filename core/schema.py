"""Pydantic schemas and column definitions for processed NASA PSI data."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Category = Literal[
    "solid_combustion",
    "detection",
    "suppression",
    "gas_phase",
    "liquid_droplet",
    "ground_modeling",
]
SafetyFocus = Literal["prevention", "detection", "suppression"]
GravityRegime = Literal["microgravity", "normal", "partial", "unknown"]
DataStatus = Literal[
    "from_challenge_text",
    "from_psi",
    "from_psi_full_page",
    "from_psi_metadata",
    "from_psi_screenshot",
    "unknown",
]
InvestigationType = Literal["flight", "ground"]
ConditionsStatus = Literal[
    "reported_table",
    "stated_in_text",
    "planned_not_confirmed",
    "unknown",
]


class Experiment(BaseModel):
    """A normalized NASA PSI investigation record."""

    model_config = ConfigDict(extra="forbid")

    id: str
    slug: str
    name: str
    full_name: str | None = None
    psi_ref: str | None = None
    category: Category | None = None
    investigation_type: InvestigationType | None = None
    conditions_basis: str | None = None
    conditions_status: ConditionsStatus = "unknown"
    include_in_ranking: bool = False
    safety_focus: SafetyFocus | None = None
    gravity_regime: GravityRegime = "unknown"
    partial_g_analog: bool = False
    platform: str | None = None
    ambient_gas: str | None = None
    # An empty list means not reported, never zero.
    o2_chamber_values_pct: list[float] = Field(default_factory=list)
    o2_chamber_min_pct: float | None = Field(default=None, ge=0, le=100)
    o2_chamber_max_pct: float | None = Field(default=None, ge=0, le=100)
    o2_stream_values_pct: list[float] = Field(default_factory=list)
    o2_stream_min_pct: float | None = Field(default=None, ge=0, le=100)
    o2_stream_max_pct: float | None = Field(default=None, ge=0, le=100)
    o2_stream_note: str | None = None
    pressure_values_psi: list[float] = Field(default_factory=list)
    pressure_min_psi: float | None = Field(default=None, ge=0)
    pressure_max_psi: float | None = Field(default=None, ge=0)
    pressure_original: str | None = None
    pressure_original_unit: str | None = None
    flow_velocity_min_cm_s: float | None = Field(default=None, ge=0)
    flow_velocity_max_cm_s: float | None = Field(default=None, ge=0)
    ambient_temp_c: float | None = None
    materials: list[str] = Field(default_factory=list)
    fuels: list[str] = Field(default_factory=list)
    suppression_agents: list[str] = Field(default_factory=list)
    objective: str | None = None
    findings_summary: str | None = None
    limitations: str | None = None
    source_url: str | None = None
    data_status: DataStatus = "unknown"
    conditions_discrete: bool = False
    extra_conditions: str = "{}"
    provenance: str = "{}"
    notes: str | None = None

    @field_validator("o2_chamber_values_pct", "o2_stream_values_pct")
    @classmethod
    def validate_o2_values(cls, values: list[float]) -> list[float]:
        if any(value < 0 or value > 100 for value in values):
            raise ValueError("O2 values must be between 0 and 100 percent")
        return values

    @field_validator("pressure_values_psi")
    @classmethod
    def validate_pressure_values(cls, values: list[float]) -> list[float]:
        if any(value < 0 for value in values):
            raise ValueError("Pressure values must not be negative")
        return values

    @model_validator(mode="after")
    def validate_ranges(self) -> "Experiment":
        ranges = (
            ("o2_chamber_min_pct", "o2_chamber_max_pct"),
            ("o2_stream_min_pct", "o2_stream_max_pct"),
            ("pressure_min_psi", "pressure_max_psi"),
            ("flow_velocity_min_cm_s", "flow_velocity_max_cm_s"),
        )
        for minimum_name, maximum_name in ranges:
            minimum = getattr(self, minimum_name)
            maximum = getattr(self, maximum_name)
            if minimum is not None and maximum is not None and minimum > maximum:
                raise ValueError(f"{minimum_name} must not be greater than {maximum_name}")
        return self


EXPERIMENT_COLUMNS = list(Experiment.model_fields)


class Document(BaseModel):
    """A source document associated with one or more investigations."""

    model_config = ConfigDict(extra="forbid")

    id: str
    experiment_slug: str | None = None
    title: str
    doc_type: Literal[
        "challenge_text", "psi_record", "publication", "report", "context", "earth_application"
    ]
    source_url: str | None = None
    content_hash: str
    local_path: str | None = None


DOCUMENT_COLUMNS = list(Document.model_fields)


class Chunk(BaseModel):
    """A retrievable document chunk."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    document_id: str
    experiment_slug: str | None = None
    chunk_index: int
    content: str
    page: int | None = None
    meta: str = "{}"


CHUNK_COLUMNS = list(Chunk.model_fields)


class Scenario(BaseModel):
    """A challenge-provided or explicitly assumed habitat scenario."""

    model_config = ConfigDict(extra="forbid")

    key: str
    name: str
    o2_target_pct: float | None = Field(default=None, ge=0, le=100)
    o2_is_minimum: bool = False
    pressure_max_psi: float | None = Field(default=None, ge=0)
    pressure_target_psi: float | None = Field(default=None, ge=0)
    gravity_regime: GravityRegime = "unknown"
    airflow_note: str | None = None
    material_priorities: list[str] = Field(default_factory=list)
    source_note: str | None = None
    assumptions: str = ""


SCENARIO_COLUMNS = list(Scenario.model_fields)


class Insight(BaseModel):
    """A cached generated insight."""

    model_config = ConfigDict(extra="forbid")

    category: str
    experiment_slugs: list[str] = Field(default_factory=list)
    content: str
    model: str
    created_at: str


class EmbeddingsMeta(BaseModel):
    """Metadata for the row-aligned normalized embedding matrix."""

    model: str
    dimension: int
    row_count: int
