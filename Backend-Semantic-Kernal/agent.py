import os
from dotenv import load_dotenv

load_dotenv()

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory

from plugins.ITServiceDeskPlugin import ITServiceDeskPlugin

AGENT_NAME = "IT Service Desk SK-Agent (Native)"

async def run_agent(user_message: str, history: list[dict] = None) -> str:
    kernel = Kernel()

    # 1. Initialize Azure OpenAI
    chat_service = AzureChatCompletion(
        service_id="it_service_desk",
        deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )
    kernel.add_service(chat_service)

    # 2. Add Native Plugin
    kernel.add_plugin(ITServiceDeskPlugin(), plugin_name="ITServiceDesk")

    # 3. Give the kernel permission to use tools
    execution_settings = OpenAIChatPromptExecutionSettings(
        service_id="it_service_desk",
        function_choice_behavior=FunctionChoiceBehavior.Auto()
    )

    # 4. Build strict ChatHistory
    chat_history = ChatHistory()
    chat_history.add_system_message("You are an IT Service Desk Agent. Always search the knowledge base before creating tickets. and Also show ticket number if ticket created")
    
    if history:
        for msg in history:
            if msg["role"] == "user":
                chat_history.add_user_message(msg["content"])
            elif msg["role"] == "assistant":
                chat_history.add_assistant_message(msg["content"])
                
    chat_history.add_user_message(user_message)

    # 5. Execute one manual turn via the chat service
    response = await chat_service.get_chat_message_content(
        chat_history=chat_history,
        settings=execution_settings,
        kernel=kernel
    )
    
    return str(response.content)
