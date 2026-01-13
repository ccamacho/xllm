"""
Calculator Agent - A specialized agent for mathematical calculations.

This agent uses the Google ADK LlmAgent with custom tools to perform
various mathematical operations from basic arithmetic to advanced calculations.
"""

import math
from typing import Union, List
from google.adk.agents import Agent


def calculate(expression: str) -> dict:
    """
    Evaluate a mathematical expression and return the result.
    
    Args:
        expression: A mathematical expression to evaluate (e.g., "2 + 3 * 4", 
                   "sqrt(16)", "sin(pi/2)", "log(100, 10)")
    
    Returns:
        A dictionary containing:
        - expression: The original expression
        - result: The calculated result
        - type: The type of calculation performed
        
    Supported operations:
    - Basic: +, -, *, /, ** (power), % (modulo), // (floor division)
    - Functions: sqrt, sin, cos, tan, log, log10, exp, abs, round, floor, ceil
    - Constants: pi, e
    - Parentheses for grouping
    
    Examples:
        calculate("2 + 3 * 4")  -> {"result": 14}
        calculate("sqrt(16)")   -> {"result": 4.0}
        calculate("sin(pi/2)")  -> {"result": 1.0}
    """
    # Define safe mathematical operations
    safe_dict = {
        # Basic math functions
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "sinh": math.sinh,
        "cosh": math.cosh,
        "tanh": math.tanh,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "exp": math.exp,
        "pow": pow,
        "abs": abs,
        "round": round,
        "floor": math.floor,
        "ceil": math.ceil,
        "factorial": math.factorial,
        "gcd": math.gcd,
        "radians": math.radians,
        "degrees": math.degrees,
        # Constants
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
        "inf": math.inf,
        # Built-in functions
        "min": min,
        "max": max,
        "sum": sum,
    }
    
    try:
        # Clean the expression
        expr = expression.strip()
        
        # Replace common mathematical notation
        expr = expr.replace("^", "**")  # Power notation
        expr = expr.replace("×", "*")   # Multiplication
        expr = expr.replace("÷", "/")   # Division
        expr = expr.replace("−", "-")   # Minus sign
        
        # Evaluate the expression safely
        result = eval(expr, {"__builtins__": {}}, safe_dict)
        
        # Determine the type of calculation
        calc_type = "basic arithmetic"
        if any(func in expression.lower() for func in ["sqrt", "sin", "cos", "tan", "log"]):
            calc_type = "trigonometric/logarithmic"
        elif "**" in expr or "^" in expression:
            calc_type = "exponential"
        elif "factorial" in expression.lower():
            calc_type = "factorial"
        
        # Handle complex numbers or special values
        if isinstance(result, complex):
            return {
                "expression": expression,
                "result": f"{result.real} + {result.imag}i",
                "type": "complex number",
                "real_part": result.real,
                "imaginary_part": result.imag,
            }
        
        # Format the result nicely
        if isinstance(result, float):
            # Round to avoid floating point issues
            if result == int(result):
                result = int(result)
            else:
                result = round(result, 10)
        
        return {
            "expression": expression,
            "result": result,
            "type": calc_type,
        }
        
    except ZeroDivisionError:
        return {
            "expression": expression,
            "error": "Division by zero is undefined",
            "type": "error",
        }
    except ValueError as e:
        return {
            "expression": expression,
            "error": f"Mathematical error: {str(e)}",
            "type": "error",
        }
    except SyntaxError:
        return {
            "expression": expression,
            "error": "Invalid mathematical expression syntax",
            "type": "error",
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": f"Calculation error: {str(e)}",
            "type": "error",
        }


def convert_units(value: float, from_unit: str, to_unit: str) -> dict:
    """
    Convert a value from one unit to another.
    
    Args:
        value: The numeric value to convert
        from_unit: The source unit (e.g., "km", "miles", "celsius", "fahrenheit")
        to_unit: The target unit
    
    Returns:
        A dictionary with the conversion result
        
    Supported conversions:
    - Length: km <-> miles, m <-> ft, cm <-> inches
    - Temperature: celsius <-> fahrenheit <-> kelvin
    - Weight: kg <-> lbs, g <-> oz
    - Area: sqm <-> sqft
    """
    conversions = {
        # Length
        ("km", "miles"): lambda x: x * 0.621371,
        ("miles", "km"): lambda x: x * 1.60934,
        ("m", "ft"): lambda x: x * 3.28084,
        ("ft", "m"): lambda x: x * 0.3048,
        ("cm", "inches"): lambda x: x * 0.393701,
        ("inches", "cm"): lambda x: x * 2.54,
        ("m", "cm"): lambda x: x * 100,
        ("cm", "m"): lambda x: x / 100,
        
        # Temperature
        ("celsius", "fahrenheit"): lambda x: x * 9/5 + 32,
        ("fahrenheit", "celsius"): lambda x: (x - 32) * 5/9,
        ("celsius", "kelvin"): lambda x: x + 273.15,
        ("kelvin", "celsius"): lambda x: x - 273.15,
        ("fahrenheit", "kelvin"): lambda x: (x - 32) * 5/9 + 273.15,
        ("kelvin", "fahrenheit"): lambda x: (x - 273.15) * 9/5 + 32,
        
        # Weight
        ("kg", "lbs"): lambda x: x * 2.20462,
        ("lbs", "kg"): lambda x: x * 0.453592,
        ("g", "oz"): lambda x: x * 0.035274,
        ("oz", "g"): lambda x: x * 28.3495,
        
        # Area
        ("sqm", "sqft"): lambda x: x * 10.7639,
        ("sqft", "sqm"): lambda x: x * 0.092903,
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
            "supported_conversions": list(conversions.keys()),
        }


def calculate_percentage(value: float, percentage: float, operation: str = "of") -> dict:
    """
    Perform percentage calculations.
    
    Args:
        value: The base value
        percentage: The percentage value
        operation: The type of operation - "of" (what is X% of Y), 
                   "increase" (increase Y by X%), "decrease" (decrease Y by X%),
                   "what_percent" (what percent is X of Y)
    
    Returns:
        A dictionary with the calculation result
    """
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
            "increase_amount": round(result - value, 6),
        }
    elif operation == "decrease":
        result = value * (1 - percentage / 100)
        return {
            "calculation": f"{value} decreased by {percentage}%",
            "result": round(result, 6),
            "decrease_amount": round(value - result, 6),
        }
    elif operation == "what_percent":
        if value == 0:
            return {"error": "Cannot calculate percentage of zero"}
        result = (percentage / value) * 100
        return {
            "calculation": f"What percent is {percentage} of {value}",
            "result": f"{round(result, 4)}%",
        }
    else:
        return {
            "error": f"Unknown operation '{operation}'",
            "supported_operations": ["of", "increase", "decrease", "what_percent"],
        }


# Create the Calculator Agent using Google ADK
calculator_agent = Agent(
    name="calculator_agent",
    model="gemini-2.0-flash",
    description="A specialized agent that performs mathematical calculations including basic arithmetic, trigonometry, logarithms, unit conversions, and percentage calculations. Use this agent when users need to compute mathematical expressions or convert between units.",
    instruction="""You are a helpful math assistant. Your role is to:

1. Use the calculate tool to evaluate mathematical expressions
2. Use convert_units for unit conversions (length, temperature, weight)
3. Use calculate_percentage for percentage-related calculations
4. Explain the calculation steps when helpful
5. Handle errors gracefully and suggest corrections

Calculation capabilities:
- Basic arithmetic: +, -, *, /, ** (power), % (modulo)
- Functions: sqrt, sin, cos, tan, log, log10, exp, factorial
- Constants: pi, e
- Unit conversions: km/miles, celsius/fahrenheit, kg/lbs, etc.
- Percentages: finding percentages, increases, decreases

When responding:
- Show the expression and result clearly
- For complex calculations, briefly explain the steps
- Mention if you're using approximations
- Suggest related calculations if relevant

Example response format:
"Calculating: [expression]
Result: [result]
[Brief explanation if helpful]"
""",
    tools=[calculate, convert_units, calculate_percentage],
)
