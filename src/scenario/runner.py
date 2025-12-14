import json
from pathlib import Path
from typing import Any

from src.settings import settings
from src.scenario.nodes import NodeExecutor
from src.core.logging_config import get_logger


logger = get_logger(__name__)

class ScenarioRunner:
    """Выполняет сценарий из JSON файла."""

    def __init__(self, scenario_path: str = None) -> None:
        """
        Инициализирует runner сценария.

        Args:
            scenario_path: Путь к JSON файлу со сценарием
        """
        self.scenario_path = settings.scenario_json_file or scenario_path
        self.scenario_data: dict[str, Any] = {}
        self.load_scenario()

    def load_scenario(self) -> None:
        """Загружает сценарий из JSON файла."""
        path = Path(self.scenario_path)
        if not path.exists():
            raise FileNotFoundError(f"Сценарий не найден: {self.scenario_path}")

        with open(path, "r", encoding="utf-8") as f:
            self.scenario_data = json.load(f)

    def run(self, user_message: str) -> tuple[str, str]:
        """
        Выполняет сценарий для сообщения пользователя.

        Args:
            user_message: Сообщение пользователя

        Returns:
            tuple: (контекст сценария, последняя выполненная нода)
        """

        logger.info(f"Запуск сценария для сообщения: {user_message}")
        executor = NodeExecutor()
        code = self.scenario_data.get("code", [])
        logger.info(f"Загружено {len(code)} нод сценария")

        last_step = ""

        i = 0
        while i < len(code):
            node = code[i]
            node_type = node.get("type")
            node_id = node.get("id", "")
            logger.info(f"Выполнение ноды {node_id} типа {node_type}")

            if node_type == "text":
                executor.execute_text(node, user_message)
                last_step = node_id
                logger.info(f"Выполнена text нода {node_id}")

            elif node_type == "tool":
                executor.execute_tool(node)
                last_step = node_id
                logger.info(f"Выполнена tool нода {node_id}, результат: {executor.tool_results}")

            elif node_type == "if":
                condition_met = executor.execute_if(node, user_message)
                last_step = node_id
                logger.info(f"Выполнена if нода {node_id}, условие выполнено: {condition_met}")

                if condition_met:
                    children = node.get("children", [])
                    logger.info(f"Выполнение {len(children)} дочерних нод для true ветки")
                    for child in children:
                        if child.get("type") == "text":
                            executor.execute_text(child, user_message)
                            last_step = child.get("id", "")
                            logger.info(f"Выполнена дочерняя text нода {child.get('id')}")
                else:
                    else_children = node.get("else_children", [])
                    logger.info(f"Выполнение {len(else_children)} дочерних нод для false ветки")
                    for child in else_children:
                        if child.get("type") == "text":
                            executor.execute_text(child, user_message)
                            last_step = child.get("id", "")
                            logger.info(f"Выполнена дочерняя text нода {child.get('id')}")

            elif node_type == "end":
                executor.execute_end()
                last_step = node_id
                logger.info(f"Выполнена end нода {node_id}")
                break

            i += 1

        context = executor.get_context()
        logger.info(f"Сценарий завершен, last_step={last_step}, контекст длиной {len(context)}")
        return context, last_step
