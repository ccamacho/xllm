"""
Advanced Calculator Agent - Specialized agent for advanced mathematics.

This agent handles complex mathematical operations including:
- Square roots and nth roots
- Trigonometric functions (sin, cos, tan, etc.)
- Logarithms and exponentials
- Factorials and combinatorics
"""

import math
from google.adk.agents import Agent


def advanced_calculate(expression: str) -> dict:
    """
    Evaluate advanced mathematical expressions.
    
    Supports:
    - Roots: sqrt(x), cbrt(x)
    - Trigonometry: sin, cos, tan, asin, acos, atan
    - Logarithms: log, log10, log2, ln
    - Exponentials: exp, pow
    - Special: factorial, gcd, chimichanga (x * 3.75)
    - Constants: pi, e, tau
    """
    safe_dict = {
        # Advanced functions
        "sqrt": math.sqrt,
        "cbrt": lambda x: x ** (1/3),
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
        "ln": math.log,  # Natural log
        "exp": math.exp,
        "pow": pow,
        "factorial": math.factorial,
        "gcd": math.gcd,
        "lcm": math.lcm,
        "radians": math.radians,
        "degrees": math.degrees,
        # Custom operations
        "chimichanga": lambda x: x * 3.75,  # Custom operation: multiply by 3.75
        # Constants
        "pi": math.pi,
        "e": math.e,
        "tau": math.tau,
        # Built-ins
        "abs": abs,
        "round": round,
        "floor": math.floor,
        "ceil": math.ceil,
    }
    
    try:
        expr = expression.strip()
        expr = expr.replace("^", "**")
        
        result = eval(expr, {"__builtins__": {}}, safe_dict)
        
        # Format result
        if isinstance(result, float):
            if result == int(result):
                result = int(result)
            else:
                result = round(result, 10)
        
        return {
            "expression": expression,
            "result": result,
            "type": "advanced mathematics",
        }
        
    except Exception as e:
        return {
            "expression": expression,
            "error": f"Calculation error: {str(e)}",
            "type": "error",
        }


# Advanced Calculator Agent
advanced_calculator_agent = Agent(
    name="advanced_calculator_agent",
    model="gemini-2.0-flash",
    description="Specialized agent for advanced mathematical operations including square roots, trigonometry, logarithms, and exponentials.",
    instruction="""You are an advanced mathematics specialist. Your role is to:

1. Evaluate complex mathematical expressions using the advanced_calculate tool
2. Handle square roots, cube roots, and nth roots
3. Perform trigonometric calculations (sin, cos, tan, etc.)
4. Calculate logarithms and exponentials
5. Work with mathematical constants (pi, e, tau)
6. Execute custom operations like chimichanga (multiplies by 3.75)
7. Provide clear, precise results

When responding:
- Show the expression and result clearly
- Mention if angles should be in radians or degrees
- Explain special cases if relevant
- For custom operations like chimichanga, briefly explain what it does
- Provide step-by-step breakdowns for complex expressions

Examples:
"Calculating advanced expression: sqrt(144)
Result: 12

This is the square root of 144, which equals 12."

"Calculating advanced expression: chimichanga(7)
Result: 26.25

The chimichanga operation multiplies the number by 3.75, so 7 × 3.75 = 26.25."
""",
    tools=[advanced_calculate],
)
