"""
Calculator Agent - Basic mathematical calculations with delegation to Advanced Calculator.

This agent handles basic arithmetic and delegates advanced operations to a specialist.
"""

import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH

load_dotenv()

# Configuration for advanced calculator
ADVANCED_CALC_URL = os.getenv("ADVANCED_CALC_URL", "http://localhost:8003")


def basic_calculate(expression: str) -> dict:
    """
    Evaluate basic arithmetic expressions: +, -, *, /, %.
    
    For advanced operations (sqrt, sin, cos, log, etc.), delegate to advanced_calculator_agent.
    """
    # Check if this is an advanced operation
    advanced_keywords = ['sqrt', 'sin', 'cos', 'tan', 'log', 'exp', 'factorial', 'pi', 'e', 'rampikichu']
    if any(keyword in expression.lower() for keyword in advanced_keywords):
        return {
            "expression": expression,
            "note": "This is an advanced operation - please use the advanced_calculator_agent",
            "type": "requires_delegation",
        }
    
    try:
        expr = expression.strip()
        expr = expr.replace("^", "**")
        
        # Only allow basic operations
        result = eval(expr, {"__builtins__": {}}, {})
        
        if isinstance(result, float):
            if result == int(result):
                result = int(result)
            else:
                result = round(result, 10)
        
        return {
            "expression": expression,
            "result": result,
            "type": "basic arithmetic",
        }
        
    except Exception as e:
        return {
            "expression": expression,
            "error": f"Calculation error: {str(e)}",
            "type": "error",
        }


def convert_units(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert a value from one unit to another."""
    conversions = {
        ("km", "miles"): lambda x: x * 0.621371,
        ("miles", "km"): lambda x: x * 1.60934,
        ("m", "ft"): lambda x: x * 3.28084,
        ("ft", "m"): lambda x: x * 0.3048,
        ("celsius", "fahrenheit"): lambda x: x * 9/5 + 32,
        ("fahrenheit", "celsius"): lambda x: (x - 32) * 5/9,
        ("kg", "lbs"): lambda x: x * 2.20462,
        ("lbs", "kg"): lambda x: x * 0.453592,
    }
    
    from_unit = from_unit.lower().strip()
    to_unit = to_unit.lower().strip()
    key = (from_unit, to_unit)
    
    if key in conversions:
        result = conversions[key](value)
        return {
            "original_value": value,
            "original_unit": from_unit,
            "converted_value": round(result, 6),
            "converted_unit": to_unit,
        }
    else:
        return {
            "error": f"Conversion from '{from_unit}' to '{to_unit}' is not supported",
        }


def calculate_percentage(value: float, percentage: float, operation: str = "of") -> dict:
    """Perform percentage calculations."""
    operation = operation.lower().strip()
    
    if operation == "of":
        result = (percentage / 100) * value
        return {
            "calculation": f"{percentage}% of {value}",
            "result": round(result, 6),
        }
    elif operation == "increase":
        result = value * (1 + percentage / 100)
        return {
            "calculation": f"{value} increased by {percentage}%",
            "result": round(result, 6),
        }
    else:
        return {"error": f"Unknown operation '{operation}'"}


# Remote A2A Agent for advanced calculations
advanced_calc_remote = RemoteA2aAgent(
    name="advanced_calculator_agent",
    description="Specialist for advanced mathematics: square roots, trigonometry, logarithms, exponentials, and complex functions.",
    agent_card=f"{ADVANCED_CALC_URL}{AGENT_CARD_WELL_KNOWN_PATH}",
)


# Calculator Agent with delegation to advanced calculator
calculator_agent = Agent(
    name="calculator_agent",
    model="gemini-2.0-flash",
    description="Calculator agent for basic arithmetic and unit conversions. Delegates advanced mathematics to a specialist sub-agent.",
    instruction="""You are a helpful calculator assistant. Your capabilities:

**BASIC OPERATIONS (use basic_calculate):**
- Addition, subtraction, multiplication, division: 5 + 3, 10 * 2, 20 / 4
- Powers and modulo: 2 ** 3, 17 % 5

**UNIT CONVERSIONS (use convert_units):**
- Length: km ↔ miles, m ↔ ft
- Temperature: celsius ↔ fahrenheit
- Weight: kg ↔ lbs

**PERCENTAGES (use calculate_percentage):**
- Finding percentages: 20% of 100
- Percentage increases/decreases

**ADVANCED OPERATIONS (delegate to advanced_calculator_agent):**
- Square roots, cube roots: sqrt(16), cbrt(27)
- Trigonometry: sin(pi/2), cos(0), tan(45)
- Logarithms: log(100), log10(1000)
- Exponentials: exp(2)
- Factorials: factorial(5)
- Custom operations: rampikichu(7) - multiplies by 3.75
- Constants: pi, e, tau

ROUTING RULES:
1. If query contains sqrt, sin, cos, tan, log, exp, factorial, pi, e, rampikichu → delegate to advanced_calculator_agent
2. If query is basic math (+, -, *, /, %) → use basic_calculate
3. If query is unit conversion → use convert_units
4. If query is percentage → use calculate_percentage

Always return the complete response from the sub-agent when delegating.
""",
    tools=[basic_calculate, convert_units, calculate_percentage],
    sub_agents=[advanced_calc_remote],
)
