import openai
from foundry_local import FoundryLocalManager

# Load the restaurant information from file
with open('local_assistant_info.md', 'r', encoding='utf-8') as f:
    local_assistant_info = f.read()

# By using an alias, the most suitable model will be downloaded 
# to your end-user's device.
alias = "Phi-4-mini-instruct-cuda-gpu"

# Create a FoundryLocalManager instance. This will start the Foundry 
# Local service if it is not already running and load the specified model.
manager = FoundryLocalManager(alias)

# The remaining code us es the OpenAI Python SDK to interact with the local model.

# Configure the client to use the local Foundry service
client = openai.OpenAI(
    base_url=manager.endpoint,
    api_key=manager.api_key  # API key is not required for local usage
)

# Get user input
user_question = input("Please enter your question: ")

# Create the formatted prompt
prompt = f"""Answer the following question about Scheibmeir's Steaks, Snacks, and Sticks:

{user_question}

Here is the information to use when answering:

{local_assistant_info}"""

# Set the model to use and generate a streaming response
stream = client.chat.completions.create(
    model=manager.get_model_info(alias).id,
    messages=[{"role": "user", "content": prompt}],
    stream=True
)

# Print the streaming response
for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="", flush=True)