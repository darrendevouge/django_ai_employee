from anthropic import Anthropic
from django.conf import settings
from .tools import get_order_details, get_refund_history, check_delivery_status
from .models import Conversation, Message, AgentLog

# Initialize Anthropic Agent
client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
anthropic_model = settings.ANTHROPIC_MODEL

# Support system prompt --> Maya's Job Description
SUPPORT_SYSTEM_PROMPT = """
You are Maya, a customer support agent at CoolBreeze AC,
you help customers with issues related to their AC orders

Your Responsibilities:
- Always use your tools to gather facts before responding
- Check order details when customer mentions their order
- Check refund history before making any refund decisions
- Be empathic but honest

Your Personality:
- Be Friendly and professional
- Be patient even when customer is angry
- Be clear and consice in your replies
- No emojis

Important Rules:
- Always check order details first before responding
= Never approve or deny a request yourself
- If refund decesion is needed - tell customer you are checking with your team
"""

# Support Tools --> Tool schemas that AI agents will read
SUPPORT_TOOLS = [
    {
        'name': 'get_order_details',
        'description': 'Fetch complete order details including status, carrier, tracking number and days since order was placed. Use this whenever customer mentions their order or complains about delivery.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'order_id': {
                    'type': 'integer',
                    'description': 'The order ID to look up'
                }
            },
            'required': ['order_id']
        }
    },
    {
        "name": "get_refund_history",
        "description": "Get complete refund history for a user. Use this before making any refund related decisions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "The user ID to check refund history for"
                }
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "check_delivery_status",
        "description": "Check current delivery status using tracking number and carrier. Use this when customer complains about delayed or missing delivery.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tracking_number": {
                    "type": "string",
                    "description": "The shipment tracking number"
                },
                "carrier": {
                    "type": "string",
                    "description": "The carrier name for example BlueDart or Delivery"
                }
            },
            "required": ["tracking_number", "carrier"]
        }
    },    
]

# execute_tool() --> Bridge between Claude and Python functions (tools)
def execute_tool(tool_name, tool_input):
    if tool_name == 'get_order_details':
        return get_order_details(tool_input['order_id'])
    
    if tool_name == 'get_refund_history':
        return get_refund_history(tool_input['user_id'])
    
    if tool_name == 'check_delivery_status':
        return check_delivery_status(tool_input['tracking_number'], tool_input['carrier'])


# Agent Loop --> while loop until task is done
def run_support_agent(user_message, conversation_id, order_id, user_id):
    conv = Conversation.objects.get(id=conversation_id)
    conversation_messages = []
    for msg in conv.messages.order_by('created_at'):
        conversation_messages.append({
            'role': msg.role,
            'content': msg.content
        })

    # Send this conversation to LLM
    response = client.messages.create(
        model=anthropic_model,
        max_tokens=1024, # approx 750 words
        thinking={"type": "disabled"},  # <--- Add this for claude-sonnet-5
        system=SUPPORT_SYSTEM_PROMPT + f'\n\nContext:\n- This conversation is about order id: #{order_id} and user: #{user_id}',
        messages=conversation_messages
    )

    # print('LLM Response==>', response)
    final_text = response.content[0].text

    return final_text




