from app.registry import ToolRegistry


def sample_tool(location: str, unit: str = "celsius"):
    return {"location": location, "unit": unit}


def test_registry_registration_and_validation():
    registry = ToolRegistry()

    registry.register(
        "sample_tool",
        sample_tool,
        {
            "type": "function",
            "function": {
                "name": "sample_tool",
                "parameters": {"type": "object"},
            },
        },
    )

    assert "sample_tool" in registry.functions

    valid, error = registry.validate(
        "sample_tool",
        {"location": "Kolkata"},
    )

    assert valid
    assert error is None
