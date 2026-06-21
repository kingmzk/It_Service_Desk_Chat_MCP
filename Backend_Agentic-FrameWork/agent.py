import os
from dotenv import load_dotenv

load_dotenv()

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments

from plugins.ITServiceDeskPlugin import ITServiceDeskPlugin

AGENT_NAME = "IT_Service_Desk_SK_Agent_Native"
SYSTEM_PROMPT = "You are an IT Service Desk Agent. Always search the knowledge base before creating tickets. and Also show ticket number if ticket created"

async def run_agent(user_message: str, history: list[dict] = None) -> str:
    kernel = Kernel()

    chat_service = AzureChatCompletion(
        service_id="it_service_desk",
        deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )
    kernel.add_service(chat_service)

    # Add Native Plugin
    kernel.add_plugin(ITServiceDeskPlugin(), plugin_name="ITServiceDesk")

    execution_settings = AzureChatPromptExecutionSettings(
        service_id="it_service_desk",
        function_choice_behavior=FunctionChoiceBehavior.Auto()
    )

    agent = ChatCompletionAgent(
        kernel=kernel,
        name=AGENT_NAME,
        instructions=SYSTEM_PROMPT
    )

    chat_history = ChatHistory()
    if history:
        for msg in history:
            if msg["role"] == "user":
                chat_history.add_user_message(msg["content"])
            elif msg["role"] == "assistant":
                chat_history.add_assistant_message(msg["content"])
                
    chat_history.add_user_message(user_message)

    arguments = KernelArguments(settings=execution_settings)

    response_content = ""
    
    async for message in agent.invoke(chat_history, arguments=arguments):
        if message.content:
            response_content = str(message.content) 
        
    return response_content