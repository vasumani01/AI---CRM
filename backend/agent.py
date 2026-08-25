import json
import os

from dotenv import load_dotenv
from google import genai

from tools import (
    search_customers,
    search_deals,
    get_customer_history,
    update_deal_status,
    add_customer_note,
    assign_deal,
    get_at_risk_deals,
)

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Add it to backend/.env"
    )

client = genai.Client(api_key=API_KEY)


SYSTEM_INSTRUCTION = """
You are an AI-powered CRM assistant.

Your job is to help sales and support teams query and update CRM data.

IMPORTANT RULES:

1. You MUST ground CRM answers in tool results.
2. Never invent customers, deals, notes, interactions, amounts, statuses, or salespeople.
3. Never claim that an action succeeded unless the corresponding tool returned success=true.
4. For database actions, always use the appropriate tool.
5. Never directly write SQL.
6. If a customer or deal does not exist, clearly tell the user.
7. If a request is ambiguous and multiple records match, do NOT guess.
8. Do not modify data until you have an unambiguous deal/customer ID.
9. Valid deal statuses are:
   New, Contacted, Won, Lost.
10. Keep responses concise but useful.
11. When summarizing customer history, summarize only information returned by the CRM tools.
12. If the user asks for information that is not available in the CRM, say that the CRM does not contain that information.
"""


TOOLS = [
    {
        "type": "function",
        "name": "search_customers",
        "description": (
            "Search the CRM for customers by name or company. "
            "Use this before customer-specific actions when identity "
            "needs to be resolved."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Customer name or company name to search for.",
                }
            },
        },
    },
    {
        "type": "function",
        "name": "search_deals",
        "description": (
            "Search CRM deals using optional customer name, status, "
            "minimum amount, and age in days."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Customer name or company name.",
                },
                "status": {
                    "type": "string",
                    "enum": ["New", "Contacted", "Won", "Lost"],
                },
                "min_amount": {
                    "type": "number",
                    "description": "Only return deals worth more than this amount.",
                },
                "older_than_days": {
                    "type": "integer",
                    "description": "Only return deals not updated within this many days.",
                },
            },
        },
    },
    {
        "type": "function",
        "name": "get_customer_history",
        "description": (
            "Retrieve a customer's deals, notes, and interaction history "
            "for grounded summaries."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Exact or partial customer/company name.",
                }
            },
            "required": ["customer_name"],
        },
    },
    {
        "type": "function",
        "name": "update_deal_status",
        "description": (
            "Update an existing deal's status. Only use this after a "
            "specific deal ID has been identified."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "deal_id": {
                    "type": "integer",
                    "description": "Unique CRM deal ID.",
                },
                "new_status": {
                    "type": "string",
                    "enum": ["New", "Contacted", "Won", "Lost"],
                },
            },
            "required": ["deal_id", "new_status"],
        },
    },
    {
        "type": "function",
        "name": "add_customer_note",
        "description": (
            "Add a note to an existing customer. If the customer name "
            "matches multiple records, the tool will refuse the action."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Customer name or company name.",
                },
                "note": {
                    "type": "string",
                    "description": "The note to save.",
                },
            },
            "required": ["customer_name", "note"],
        },
    },
    {
        "type": "function",
        "name": "assign_deal",
        "description": (
            "Assign an existing deal to a salesperson. Only use this "
            "after a specific deal ID has been identified."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "deal_id": {
                    "type": "integer",
                    "description": "Unique CRM deal ID.",
                },
                "salesperson": {
                    "type": "string",
                    "description": "Salesperson to assign the deal to.",
                },
            },
            "required": ["deal_id", "salesperson"],
        },
    },
    {
        "type": "function",
        "name": "get_at_risk_deals",
        "description": (
            "Find high-value deals worth more than $10,000 that have "
            "not been updated for more than 14 days."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
]


AVAILABLE_FUNCTIONS = {
    "search_customers": search_customers,
    "search_deals": search_deals,
    "get_customer_history": get_customer_history,
    "update_deal_status": update_deal_status,
    "add_customer_note": add_customer_note,
    "assign_deal": assign_deal,
    "get_at_risk_deals": get_at_risk_deals,
}


def run_tool(name, arguments):
    function = AVAILABLE_FUNCTIONS.get(name)

    if not function:
        return {
            "success": False,
            "error": f"Unknown tool: {name}",
        }

    try:
        return function(**arguments)
    except Exception as error:
        return {
            "success": False,
            "error": f"Tool execution failed: {str(error)}",
        }


def chat_with_crm(user_message: str):
    response = client.models.generate_content(
        model="gemini-3.7-flash",
        contents=user_message,
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
            "tools": TOOLS,
        },
    )

    # The Gemini SDK's current function-calling response exposes
    # function calls as structured parts.
    function_calls = []

    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.function_call:
                function_calls.append(part.function_call)

    if not function_calls:
        return {
            "message": response.text,
            "action_performed": False,
        }

    tool_results = []

    for function_call in function_calls:
        name = function_call.name
        arguments = dict(function_call.args)

        result = run_tool(name, arguments)

        tool_results.append(
            {
                "name": name,
                "arguments": arguments,
                "result": result,
            }
        )

    # Send the tool results back to Gemini for the final response.
    tool_response_parts = []

    for item in tool_results:
        tool_response_parts.append(
            {
                "function_response": {
                    "name": item["name"],
                    "response": item["result"],
                }
            }
        )

    final_response = client.models.generate_content(
        model="gemini-3.7-flash",
        contents=[
            user_message,
            response.candidates[0].content,
            {
                "role": "user",
                "parts": tool_response_parts,
            },
        ],
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
            "tools": TOOLS,
        },
    )

    return {
        "message": final_response.text,
        "action_performed": any(
            item["name"] in {
                "update_deal_status",
                "add_customer_note",
                "assign_deal",
            }
            and item["result"].get("success") is True
            for item in tool_results
        ),
        "tool_calls": tool_results,
    }