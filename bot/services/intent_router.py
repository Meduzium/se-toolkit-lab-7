"""Intent router service for natural language processing with LLM tool calling."""

import json
import sys
from typing import Any

from services.llm_client import LLMClient
from services.lms_client import LMSClient


class IntentRouter:
    """Routes natural language queries to appropriate backend tools via LLM."""

    SYSTEM_PROMPT = (
        "You are an intelligent assistant for a Learning Management System (LMS). "
        "Your job is to help users get information about labs, scores, learners, and analytics.\n\n"
        "You have access to 9 tools that query the backend API. Use them to answer user questions.\n\n"
        "IMPORTANT RULES:\n"
        "1. ALWAYS use tools to get real data - never make up information.\n"
        "2. For questions about 'which lab has the lowest/highest X', first get all labs with get_items, "
        "then call the appropriate analytics tool for EACH lab, then compare and answer.\n"
        "3. After receiving tool results, analyze them and provide a clear, helpful answer.\n"
        "4. If the user's message is a greeting (hello, hi, привет), respond warmly and briefly mention what you can help with.\n"
        "5. If the message is unclear or gibberish, politely say you didn't understand and list what you CAN help with.\n"
        "6. If the user mentions a specific lab (e.g., 'lab 4' or 'lab-04'), ask what they want to know about it "
        "(scores, pass rates, top learners, etc.) unless they already specified.\n"
        "7. Format your answers clearly with bullet points for data.\n\n"
        "Available tools:\n"
        "- get_items: List all labs and tasks\n"
        "- get_learners: List enrolled students\n"
        "- get_scores: Score distribution for a lab (4 buckets)\n"
        "- get_pass_rates: Per-task pass rates for a lab\n"
        "- get_timeline: Submissions per day for a lab\n"
        "- get_groups: Per-group scores for a lab\n"
        "- get_top_learners: Top N learners for a lab\n"
        "- get_completion_rate: Completion percentage for a lab\n"
        "- trigger_sync: Refresh data from autochecker\n\n"
        "Example multi-step reasoning:\n"
        "User: 'which lab has the lowest pass rate?'\n"
        "You: [calls get_items] → [calls get_pass_rates for each lab] → [compares and answers]\n\n"
        "Always think step by step and use tools to get accurate information."
    )

    def __init__(self, llm_client: LLMClient, lms_client: LMSClient) -> None:
        """Initialize the intent router.

        Args:
            llm_client: LLM client for natural language processing.
            lms_client: LMS client for backend API calls.
        """
        self.llm_client = llm_client
        self.lms_client = lms_client
        self.tools = llm_client.get_tool_definitions()

    def _debug(self, message: str) -> None:
        """Print debug message to stderr."""
        print(message, file=sys.stderr)

    async def _execute_tool(self, name: str, args: dict[str, Any]) -> Any:
        """Execute a tool by calling the appropriate LMS API endpoint.

        Args:
            name: Tool name.
            args: Tool arguments.

        Returns:
            Tool execution result.
        """
        self._debug(f"[tool] LLM called: {name}({json.dumps(args)})")

        try:
            if name == "get_items":
                result = await self.lms_client.get_items()
            elif name == "get_learners":
                result = await self.lms_client.get_learners()
            elif name == "get_scores":
                result = await self.lms_client.get_scores(lab=args.get("lab", ""))
            elif name == "get_pass_rates":
                result = await self.lms_client.get_pass_rates(lab=args.get("lab", ""))
            elif name == "get_timeline":
                result = await self.lms_client.get_timeline(lab=args.get("lab", ""))
            elif name == "get_groups":
                result = await self.lms_client.get_groups(lab=args.get("lab", ""))
            elif name == "get_top_learners":
                result = await self.lms_client.get_top_learners(
                    lab=args.get("lab", ""),
                    limit=args.get("limit", 5),
                )
            elif name == "get_completion_rate":
                result = await self.lms_client.get_completion_rate(
                    lab=args.get("lab", "")
                )
            elif name == "trigger_sync":
                result = await self.lms_client.trigger_sync()
            else:
                result = {"error": f"Unknown tool: {name}"}

            self._debug(f"[tool] Result: {self._summarize_result(result)}")
            return result

        except Exception as e:
            error_msg = f"Error executing {name}: {str(e)}"
            self._debug(f"[tool] Error: {error_msg}")
            return {"error": error_msg}

    def _summarize_result(self, result: Any) -> str:
        """Create a brief summary of a tool result for debugging."""
        if isinstance(result, list):
            return f"{len(result)} items"
        elif isinstance(result, dict):
            return f"{len(result)} keys"
        else:
            return str(result)[:100]

    async def route(self, user_message: str) -> str:
        """Route a user message through the LLM tool calling loop.

        Args:
            user_message: User's natural language message.

        Returns:
            Final response to send to the user.
        """
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        max_iterations = 8
        tool_call_count = 0
        seen_tool_calls = set()

        for iteration in range(max_iterations):
            try:
                # Call LLM
                response = await self.llm_client.chat(
                    messages=messages,
                    tools=self.tools,
                )

                # Check if LLM wants to call tools
                if not response["tool_calls"]:
                    # No tool calls - LLM provided final answer
                    return response["content"] or "I couldn't process that request."

                # Execute tool calls
                tool_results = []
                for tool_call in response["tool_calls"]:
                    tool_call_count += 1
                    name = tool_call["name"]
                    try:
                        args = json.loads(tool_call["arguments"])
                    except json.JSONDecodeError as e:
                        self._debug(f"[error] Failed to parse arguments for {name}: {tool_call['arguments']}")
                        args = {}

                    # Detect loops - same tool with same args
                    call_signature = f"{name}:{json.dumps(args, sort_keys=True)}"
                    if call_signature in seen_tool_calls:
                        self._debug(f"[loop] Detected loop: {call_signature}")
                        # Skip duplicate call and provide answer based on existing results
                        if tool_results:
                            break
                    seen_tool_calls.add(call_signature)

                    result = await self._execute_tool(name, args)
                    tool_results.append(result)

                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": name,
                        "content": json.dumps(result, ensure_ascii=False, default=str),
                    })

                self._debug(
                    f"[summary] Feeding {len(tool_results)} tool result(s) back to LLM"
                )

                # If no new results were added (all duplicates), break
                if not tool_results and seen_tool_calls:
                    break

            except Exception as e:
                self._debug(f"[error] LLM call failed: {str(e)}")
                return f"Sorry, I encountered an error: {str(e)}"

        # Max iterations reached or loop detected
        if tool_results:
            # Provide best-effort answer based on collected results
            return f"I've gathered some data. Based on the results:\n\n{json.dumps(tool_results[0] if len(tool_results) == 1 else tool_results, indent=2, ensure_ascii=False, default=str)}"
        return "I'm having trouble processing this request. Please try rephrasing."

    def get_capabilities_text(self) -> str:
        """Get a text describing bot capabilities for fallback messages."""
        return (
            "Я могу помочь вам с:\n\n"
            "• Показать список лабораторных работ\n"
            "• Показать оценки и распределение баллов\n"
            "• Показать проходные баллы по задачам\n"
            "• Показать топ студентов\n"
            "• Сравнить группы\n"
            "• Показать статистику выполнения\n"
            "• Обновить данные из авточекера\n\n"
            "Примеры запросов:\n"
            "• «какие лабораторные есть?»\n"
            "• «покажи оценки за lab-04»\n"
            "• «какая лабораторная самая сложная?»\n"
            "• «топ 5 студентов в lab-03»\n"
            "• «сравни группы в lab-01»"
        )
