import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from .tools import tools
from .state import AgentState

load_dotenv()


_model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0,
)
llm_with_tools = _model.bind_tools(tools, parallel_tool_calls=False)

SYSTEM_PROMPT = """Ти помічник для аналізу реєстру судів України.
Ти можеш виконувати SQL-запити до бази даних для отримання інформації про суди та суддів.
Завжди відповідай українською, якщо не попрошено інакше.
"""


def assistant(state: AgentState):
    sys_msg = SystemMessage(content=SYSTEM_PROMPT)
    return {
        "messages": [llm_with_tools.invoke([sys_msg] + state["messages"])],
    }
