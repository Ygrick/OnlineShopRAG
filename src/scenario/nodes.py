import re
from typing import Any

from src.llm.client import get_llm
from src.llm.prompts import CONDITION_CHECK_PROMPT
from src.scenario.tools import get_user_data


class NodeExecutor:
    """Исполнитель нод сценария."""

    def __init__(self) -> None:
        """
        Инициализирует исполнитель нод.
        """
        self.tool_results: dict[str, Any] = {}
        self.scenario_context: list[str] = []
        self.llm = get_llm()

    def execute_text(self, node: dict[str, Any], user_message: str) -> None:
        """
        Выполняет text ноду с подстановкой переменных.

        Args:
            node: Словарь с данными ноды
            user_message: Сообщение пользователя для контекста
        """
        text = node.get("text", "")
        text = self._substitute_variables(text)
        self.scenario_context.append(text)

    def execute_tool(self, node: dict[str, Any]) -> None:
        """
        Выполняет tool ноду и сохраняет результат.

        Args:
            node: Словарь с данными ноды
        """
        tool_name = node.get("tool", "")
        if tool_name == "get_user_data":
            result = get_user_data()
            self.tool_results[tool_name] = result

    def execute_if(self, node: dict[str, Any], user_message: str) -> bool:
        """
        Выполняет if ноду с проверкой условия через LLM.

        Args:
            node: Словарь с данными ноды
            user_message: Сообщение пользователя

        Returns:
            bool: True если условие выполнено, False иначе
        """
        condition = node.get("condition", "")
        chain = CONDITION_CHECK_PROMPT | self.llm
        response = chain.invoke({"message": user_message, "condition": condition})
        answer = response.content.strip().lower()
        return answer.startswith("да")

    def execute_end(self) -> None:
        """
        Выполняет end ноду (завершение сценария).
        """
        pass

    def _substitute_variables(self, text: str) -> str:
        """
        Подставляет переменные из результатов выполнения tools.

        Args:
            text: Текст с переменными вида {=@tool.variable=}

        Returns:
            str: Текст с подставленными значениями
        """
        pattern = r"\{=@(\w+)\.(\w+)=\}"
        matches = re.findall(pattern, text)

        for tool_name, variable_name in matches:
            if tool_name in self.tool_results:
                value = self.tool_results[tool_name].get(variable_name, "")
                text = text.replace(f"{{=@{tool_name}.{variable_name}=}}", str(value))

        return text

    def get_context(self) -> str:
        """
        Получает накопленный контекст сценария.

        Returns:
            str: Контекст сценария
        """
        return "\n".join(self.scenario_context)

