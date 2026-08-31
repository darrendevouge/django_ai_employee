from anthropic import Anthropic
from decouple import config

client = Anthropic(
    api_key=config('ANTHROPIC_API_KEY'),  
)

message = client.messages.create(
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Provide me with 5 names of mammals",
        }
    ],

    model=config('ANTHROPIC_MODEL'),
)

print(message.content)
