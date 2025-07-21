from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class TestMetadata(BaseModel):
    id: str
    last_modified: str


class Test(BaseModel):
    name: str
    task: str
    expected_result: str
    metadata: TestMetadata
    steps: Optional[list[str]] = None


class Credential(BaseModel):
    id: Optional[str] = None
    username: str
    password: str


class TestPreferences(BaseModel):
    tests: Optional[dict] = Field(
        default=None, description="Test execution preferences"
    )

    @property
    def always_run(self) -> Optional[List[str]]:
        """Get always_run tests from the tests configuration."""
        if self.tests and "always_run" in self.tests:
            return self.tests["always_run"]
        return None

    @property
    def limit(self) -> Optional[int]:
        """Get test limit from the tests configuration."""
        if self.tests and "limit" in self.tests:
            return self.tests["limit"]
        return None

    @property
    def headless(self) -> Optional[bool]:
        """Get headless setting from the tests configuration."""
        if self.tests and "headless" in self.tests:
            return self.tests["headless"]
        return None

    @property
    def silent(self) -> Optional[bool]:
        """Get silent setting from the tests configuration."""
        if self.tests and "silent" in self.tests:
            return self.tests["silent"]
        return None

    @property
    def verbose(self) -> Optional[bool]:
        """Get verbose setting from the tests configuration."""
        if self.tests and "verbose" in self.tests:
            return self.tests["verbose"]
        return None

    @property
    def only_affected(self) -> Optional[bool]:
        """Get only_affected setting from the tests configuration."""
        if self.tests and "only_affected" in self.tests:
            return self.tests["only_affected"]
        return None

    @property
    def parallel(self) -> Optional[int]:
        """Get parallel/max_concurrent setting from the tests configuration."""
        if self.tests and "parallel" in self.tests:
            return self.tests["parallel"]
        return None

    @property
    def output(self) -> Optional[str]:
        """Get output file setting from the tests configuration."""
        if self.tests and "output" in self.tests:
            return self.tests["output"]
        return None


class Config(BaseModel):
    base_url: str
    credentials: list[Credential]
    project_id: str
    project_name: str
    x_vercel_protection_bypass: Optional[str] = Field(
        None, alias="x-vercel-protection-bypass"
    )
    preferences: Optional[TestPreferences] = Field(
        default=None, description="Test execution preferences and configurations"
    )


class WebSocketMessage(BaseModel):
    action: str


class WebSocketInitTestMessage(WebSocketMessage):
    action: Literal["init_test"] = "init_test"
    test: Test
    config: Config


class ToolRequest(BaseModel):
    id: str
    name: str
    args: dict


class WebSocketStepResultMessage(WebSocketMessage):
    action: Literal["step_result"] = "step_result"
    job_id: str
    tool: ToolRequest
    status: Literal["success", "error"]
    output: str


class WebSocketStepRequestMessage(WebSocketMessage):
    action: Literal["step_request"] = "step_request"
    job_id: str
    tool: ToolRequest
    message: str


class TestResult(BaseModel):
    result: Literal["pass", "fail"]
    reason: str


class WebSocketCompleteMessage(WebSocketMessage):
    action: Literal["complete"] = "complete"
    result: TestResult


class NamedTestResult(TestResult):
    name: str
    metadata: TestMetadata
    time: Optional[float] = None


class Bug(BaseModel):
    """Represents a bug found by a destructive agent."""

    name: str
    description: str


class DestructiveResult(BaseModel):
    """Result from a destructive agent execution."""

    bugs: list[Bug]


class WebSocketInitDestructiveMessage(WebSocketMessage):
    """Initialize destructive agent message."""

    action: Literal["init_destructive"] = "init_destructive"
    page: str
    diff: str
    agent: str
    config: Config


class WebSocketDestructiveCompleteMessage(WebSocketMessage):
    """Destructive agent completion message."""

    action: Literal["destructive_complete"] = "destructive_complete"
    result: DestructiveResult


class NamedDestructiveResult(BaseModel):
    """Named destructive result with additional metadata."""

    page: str
    agent: str
    result: DestructiveResult
    time: float = 0


# New types for destructive streaming
class NamedDestructiveResultWithVideo(NamedDestructiveResult):
    """Destructive result with video for streaming."""

    session_id: str  # Unique identifier for this session (page + agent)
    video_url: Optional[str] = None
