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

MODEL = "gemini-3.6-flash"

SYSTEM_INSTRUCTION = """
You are an AI-powered CRM assistant.

Your job is to help sales and support teams query and update CRM data.

IMPORTANT RULES:

1. You MUST ground CRM answers in tool results.
2. Never invent customers, deals, notes, interactions, amounts,
   statuses, or salespeople.
3. Never claim that an action succeeded unless the corresponding
   tool returned success=true.
4. For CRM database actions, always use the appropriate tool.
5. Never directly write SQL.
6. If a customer or deal does not exist, clearly tell the user.
7. If a request is ambiguous and multiple records match, do NOT guess.
8. Do not modify data until you have an unambiguous record.
9. Valid deal statuses are:
   New, Contacted, Won, Lost.
10. Keep responses concise but useful.
11. When summarizing customer history, summarize only information
    returned by CRM tools.
12. If the user asks for information that is not available in the CRM,
    say that the CRM does not contain that information.
"""


# Google Gemini function declarations
TOOLS = [
    {
        "function_declarations": [
            {
                "name": "search_customers",
                "description": (
                    "Search the CRM for customers by name or company. "
                    "Use this before customer-specific actions when "
                    "identity needs to be resolved."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {
                            "type": "STRING",
                            "description": (
                                "Customer name or company name to search for."
                            ),
                        }
                    },
                },
            },
            {
                "name": "search_deals",
                "description": (
                    "Search CRM deals using optional customer name, "
                    "status, minimum amount, and age in days."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "customer_name": {
                            "type": "STRING",
                            "description": (
                                "Customer name or company name."
                            ),
                        },
                        "status": {
                            "type": "STRING",
                            "enum": [
                                "New",
                                "Contacted",
                                "Won",
                                "Lost",
                            ],
                        },
                        "min_amount": {
                            "type": "NUMBER",
                            "description": (
                                "Only return deals worth more than "
                                "this amount."
                            ),
                        },
                        "older_than_days": {
                            "type": "INTEGER",
                            "description": (
                                "Only return deals not updated "
                                "within this many days."
                            ),
                        },
                    },
                },
            },
            {
                "name": "get_customer_history",
                "description": (
                    "Retrieve a customer's deals, notes, and interaction "
                    "history for grounded summaries."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "customer_name": {
                            "type": "STRING",
                            "description": (
                                "Exact or partial customer/company name."
                            ),
                        }
                    },
                    "required": ["customer_name"],
                },
            },
            {
                "name": "update_deal_status",
                "description": (
                    "Update an existing deal's status. Only use this "
                    "after a specific deal ID has been identified."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "deal_id": {
                            "type": "INTEGER",
                            "description": "Unique CRM deal ID.",
                        },
                        "new_status": {
                            "type": "STRING",
                            "enum": [
                                "New",
                                "Contacted",
                                "Won",
                                "Lost",
                            ],
                        },
                    },
                    "required": ["deal_id", "new_status"],
                },
            },
            {
                "name": "add_customer_note",
                "description": (
                    "Add a note to an existing customer. If the "
                    "customer name matches multiple records, the "
                    "tool will refuse the action."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "customer_name": {
                            "type": "STRING",
                            "description": (
                                "Customer name or company name."
                            ),
                        },
                        "note": {
                            "type": "STRING",
                            "description": "The note to save.",
                        },
                    },
                    "required": [
                        "customer_name",
                        "note",
                    ],
                },
            },
            {
                "name": "assign_deal",
                "description": (
                    "Assign an existing deal to a salesperson. "
                    "Only use this after a specific deal ID has "
                    "been identified."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "deal_id": {
                            "type": "INTEGER",
                            "description": "Unique CRM deal ID.",
                        },
                        "salesperson": {
                            "type": "STRING",
                            "description": (
                                "Salesperson to assign the deal to."
                            ),
                        },
                    },
                    "required": [
                        "deal_id",
                        "salesperson",
                    ],
                },
            },
            {
                "name": "get_at_risk_deals",
                "description": (
                    "Find high-value deals worth more than $10,000 "
                    "that have not been updated for more than 14 days."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {},
                },
            },
        ]
    }
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
    contents = [
        {
            "role": "user",
            "parts": [
                {
                    "text": user_message
                }
            ],
        }
    ]

    tool_calls_log = []
    action_performed = False

    # Allow Gemini to perform multiple tool calls.
    # Example:
    # search_deals -> update_deal_status -> final answer
    for _ in range(5):

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents,
            config={
                "system_instruction": SYSTEM_INSTRUCTION,
                "tools": TOOLS,
            },
        )

        candidate = response.candidates[0]
        parts = candidate.content.parts

        function_calls = [
            part.function_call
            for part in parts
            if getattr(part, "function_call", None)
        ]

        # Gemini has finished and wants to give the user an answer.
        if not function_calls:
            return {
                "message": response.text,
                "action_performed": action_performed,
                "tool_calls": tool_calls_log,
            }

        # IMPORTANT:
        # Add Gemini's function-call response back into the conversation.
        contents.append(candidate.content)

        tool_response_parts = []

        for function_call in function_calls:

            name = function_call.name
            arguments = dict(function_call.args)

            result = run_tool(name, arguments)

            tool_calls_log.append(
                {
                    "name": name,
                    "arguments": arguments,
                    "result": result,
                }
            )

            # Track successful CRM modifications.
            if (
                name
                in {
                    "update_deal_status",
                    "add_customer_note",
                    "assign_deal",
                }
                and result.get("success") is True
            ):
                action_performed = True

            tool_response_parts.append(
                {
                    "function_response": {
                        "name": name,
                        "response": result,
                    }
                }
            )

        # Send tool results back to Gemini.
        contents.append(
            {
                "role": "user",
                "parts": tool_response_parts,
            }
        )

    # Safety fallback if Gemini keeps requesting tools.
    return {
        "message": (
            "I couldn't complete the request safely because "
            "too many CRM tool steps were required."
        ),
        "action_performed": action_performed,
        "tool_calls": tool_calls_log,
    }