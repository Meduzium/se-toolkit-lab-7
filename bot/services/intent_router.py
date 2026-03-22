"""Intent router service for natural language processing with LLM tool calling."""

import json
import re
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

    def _detect_intent(self, user_message: str) -> str | None:
        """Detect user intent from message for direct handling.

        Args:
            user_message: User's message text.

        Returns:
            Intent string or None if no pattern matched.
        """
        msg_lower = user_message.lower()

        # Sync/data refresh intent
        if any(kw in msg_lower for kw in ["sync", "refresh", "update", "reload", "load"]):
            if any(kw in msg_lower for kw in ["data", "item", "log"]):
                return "sync"

        # Lowest/highest pass rate comparison
        if any(kw in msg_lower for kw in ["lowest", "highest", "worst", "best"]):
            if any(kw in msg_lower for kw in ["pass rate", "passrate", "score", "lab"]):
                return "compare_pass_rates"

        # Labs listing query - "what labs", "list labs", "labs available"
        if any(kw in msg_lower for kw in ["what lab", "list lab", "lab available", "show lab", "labs are"]):
            return "list_labs"

        # Scores query - "show scores for lab X" or "lab 4 scores"
        if any(kw in msg_lower for kw in ["score", "scores", "grade", "grades"]):
            # Extract lab number
            lab_match = re.search(r"lab[- ]?(\d+)", msg_lower)
            if lab_match:
                return f"scores:lab-{lab_match.group(1).zfill(2)}"

        # Top learners query - "top N students in lab X"
        if "top" in msg_lower and any(kw in msg_lower for kw in ["student", "learner", "person"]):
            lab_match = re.search(r"lab[- ]?(\d+)", msg_lower)
            limit_match = re.search(r"(\d+)", msg_lower)
            if lab_match:
                lab = f"lab-{lab_match.group(1).zfill(2)}"
                limit = int(limit_match.group(1)) if limit_match else 5
                return f"top_learners:{lab}:{limit}"

        # Learners count query - "how many students" or "list students"
        if any(kw in msg_lower for kw in ["how many student", "how many learner", "enrolled", "list student", "list learner"]):
            return "learners"

        # Greeting
        if any(kw in msg_lower for kw in ["hello", "hi", "hey", "привет", "здравствуйте"]):
            return "greeting"

        return None

    def _is_gibberish(self, text: str) -> bool:
        """Check if text appears to be gibberish or random typing.

        Args:
            text: Text to check.

        Returns:
            True if text appears to be gibberish.
        """
        # Check for random keyboard patterns
        gibberish_patterns = [
            r"^[asdfghjkl]+$",
            r"^[qwerty]+$",
            r"^[zxcvbnm]+$",
            r"^[aeiou]+$",
            r"^[^aeiouаеиоуыэюя]{4,}$",  # 4+ consonants
        ]
        text_clean = text.lower().strip()
        if len(text_clean) < 3:
            return True
        for pattern in gibberish_patterns:
            if re.match(pattern, text_clean):
                return True
        return False

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

    async def _handle_sync_direct(self) -> str:
        """Handle sync requests directly without LLM.

        Returns:
            Formatted sync result message.
        """
        try:
            result = await self.lms_client.trigger_sync()
            new_records = result.get("new_records", 0)
            total_records = result.get("total_records", 0)
            return (
                f"✅ Sync complete!\n\n"
                f"• New records loaded: {new_records}\n"
                f"• Total records: {total_records}\n"
                f"• Status: success"
            )
        except Exception as e:
            return f"Sync failed: {str(e)}"

    async def _handle_compare_pass_rates(self) -> str:
        """Handle 'lowest/highest pass rate' queries directly without LLM.

        Returns:
            Formatted comparison message with lab names and percentages.
        """
        try:
            # Get all labs
            items = await self.lms_client.get_items()
            labs = [item for item in items if item.get("type") == "lab"]

            if not labs:
                return "No labs found in the system."

            # Get pass rates for each lab
            lab_pass_rates = []
            for lab in labs:
                lab_id = lab.get("id", "")
                lab_title = lab.get("title", f"Lab {lab_id}")
                # Convert "Lab 01" to "lab-01" format
                lab_number = re.search(r"Lab\s*(\d+)", lab_title)
                if lab_number:
                    lab_param = f"lab-{lab_number.group(1).zfill(2)}"
                else:
                    lab_param = f"lab-{str(lab_id).zfill(2)}"

                try:
                    pass_rates = await self.lms_client.get_pass_rates(lab=lab_param)
                    if pass_rates:
                        # Calculate average pass rate across all tasks
                        avg_rate = sum(t.get("avg_score", 0) for t in pass_rates) / len(pass_rates)
                        lab_pass_rates.append((lab_title, avg_rate, len(pass_rates)))
                except Exception:
                    continue

            if not lab_pass_rates:
                return "Could not retrieve pass rates for any lab."

            # Sort by pass rate
            lab_pass_rates.sort(key=lambda x: x[1])

            # Format response
            lowest = lab_pass_rates[0]
            highest = lab_pass_rates[-1]

            result_lines = [
                "📊 Pass Rate Comparison:",
                "",
                f"🔴 Lowest: {lowest[0]} - {lowest[1]:.1f}% average ({lowest[2]} tasks)",
                f"🟢 Highest: {highest[0]} - {highest[1]:.1f}% average ({highest[2]} tasks)",
                "",
                "All labs (sorted by avg pass rate):",
            ]
            for title, rate, tasks in lab_pass_rates:
                result_lines.append(f"• {title}: {rate:.1f}%")

            return "\n".join(result_lines)

        except Exception as e:
            return f"Error comparing pass rates: {str(e)}"

    def _handle_gibberish(self) -> str:
        """Handle gibberish/unrecognized input.

        Returns:
            Help message with available commands.
        """
        return (
            "I'm not sure I understood that. 😕\n\n"
            "I can help you with:\n"
            "• List available labs and tasks\n"
            "• Show scores and pass rates\n"
            "• Compare lab performance\n"
            "• Show top students\n"
            "• Sync data from autochecker\n\n"
            "Try asking:\n"
            "• 'which labs are available?'\n"
            "• 'show scores for lab-01'\n"
            "• 'which lab has the lowest pass rate?'\n"
            "• 'sync the data'"
        )

    async def _handle_scores(self, lab: str) -> str:
        """Handle scores query directly.

        Args:
            lab: Lab identifier.

        Returns:
            Formatted scores distribution message.
        """
        try:
            result = await self.lms_client.get_scores(lab=lab)
            lines = [f"📊 Score Distribution for {lab}:", ""]
            for bucket in result:
                lines.append(f"• {bucket['bucket']}: {bucket['count']} students")
            total = sum(b['count'] for b in result)
            lines.append(f"\nTotal submissions: {total}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error getting scores for {lab}: {str(e)}"

    async def _handle_top_learners(self, lab: str, limit: int) -> str:
        """Handle top learners query directly.

        Args:
            lab: Lab identifier.
            limit: Number of top learners to return.

        Returns:
            Formatted top learners message.
        """
        try:
            result = await self.lms_client.get_top_learners(lab=lab, limit=limit)
            if not result:
                return f"No data found for {lab}."
            lines = [f"🏆 Top {limit} Learners in {lab}:", ""]
            for i, learner in enumerate(result, 1):
                lines.append(f"{i}. Learner #{learner['learner_id']}: {learner['avg_score']:.1f} avg ({learner['attempts']} attempts)")
            return "\n".join(lines)
        except Exception as e:
            return f"Error getting top learners: {str(e)}"

    async def _handle_learners(self) -> str:
        """Handle learners count query directly.

        Returns:
            Formatted learners count message.
        """
        try:
            result = await self.lms_client.get_learners()
            count = len(result)
            # Count by group
            groups = {}
            for learner in result:
                group = learner.get('student_group', 'unknown')
                groups[group] = groups.get(group, 0) + 1
            
            lines = [
                f"👥 Enrolled Students: {count}",
                "",
                "By group:",
            ]
            for group, cnt in sorted(groups.items()):
                lines.append(f"• {group}: {cnt}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error getting learners: {str(e)}"

    async def _handle_greeting(self) -> str:
        """Handle greeting message.

        Returns:
            Friendly greeting response.
        """
        return (
            "Hello! 👋 I'm your LMS assistant. I can help you with:\n\n"
            "• List available labs and tasks\n"
            "• Show scores and pass rates for any lab\n"
            "• Compare lab performance (lowest/highest pass rates)\n"
            "• Show top students in a lab\n"
            "• Count enrolled students\n"
            "• Sync data from autochecker\n\n"
            "Just ask me anything about your labs!"
        )

    async def _handle_list_labs(self) -> str:
        """Handle labs listing query directly.

        Returns:
            Formatted list of labs and tasks.
        """
        try:
            items = await self.lms_client.get_items()
            labs = [item for item in items if item.get("type") == "lab"]
            tasks = [item for item in items if item.get("type") == "task"]
            
            lines = ["📚 Available Labs:", ""]
            for lab in labs:
                lab_id = lab.get("id", "")
                lab_title = lab.get("title", f"Lab {lab_id}")
                # Count tasks for this lab
                lab_tasks = [t for t in tasks if t.get("parent_id") == lab_id]
                lines.append(f"• {lab_title} ({len(lab_tasks)} tasks)")
            
            lines.append(f"\nTotal: {len(labs)} labs, {len(tasks)} tasks")
            return "\n".join(lines)
        except Exception as e:
            return f"Error getting labs: {str(e)}"

    async def route(self, user_message: str) -> str:
        """Route a user message through the LLM tool calling loop.

        Args:
            user_message: User's natural language message.

        Returns:
            Final response to send to the user.
        """
        # First, check for gibberish
        if self._is_gibberish(user_message):
            self._debug(f"[gibberish] Detected: {user_message}")
            return self._handle_gibberish()

        # Check for direct-handling intents (bypass LLM for reliability)
        intent = self._detect_intent(user_message)
        if intent == "sync":
            self._debug(f"[direct] Handling sync request")
            return await self._handle_sync_direct()
        elif intent == "compare_pass_rates":
            self._debug(f"[direct] Handling pass rate comparison")
            return await self._handle_compare_pass_rates()
        elif intent == "list_labs":
            self._debug(f"[direct] Handling list labs request")
            return await self._handle_list_labs()
        elif intent == "greeting":
            self._debug(f"[direct] Handling greeting")
            return await self._handle_greeting()
        elif intent == "learners":
            self._debug(f"[direct] Handling learners query")
            return await self._handle_learners()
        elif intent and intent.startswith("scores:"):
            lab = intent.split(":")[1]
            self._debug(f"[direct] Handling scores query for {lab}")
            return await self._handle_scores(lab)
        elif intent and intent.startswith("top_learners:"):
            parts = intent.split(":")
            lab = parts[1]
            limit = int(parts[2]) if len(parts) > 2 else 5
            self._debug(f"[direct] Handling top learners query for {lab}, limit={limit}")
            return await self._handle_top_learners(lab, limit)

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
                # Fallback: try direct handling for common queries
                # Re-detect intent and handle directly
                fallback_intent = self._detect_intent(user_message)
                if fallback_intent == "sync":
                    return await self._handle_sync_direct()
                elif fallback_intent == "compare_pass_rates":
                    return await self._handle_compare_pass_rates()
                elif fallback_intent == "list_labs":
                    return await self._handle_list_labs()
                elif fallback_intent == "learners":
                    return await self._handle_learners()
                elif fallback_intent and fallback_intent.startswith("scores:"):
                    lab = fallback_intent.split(":")[1]
                    return await self._handle_scores(lab)
                elif fallback_intent and fallback_intent.startswith("top_learners:"):
                    parts = fallback_intent.split(":")
                    lab = parts[1]
                    limit = int(parts[2]) if len(parts) > 2 else 5
                    return await self._handle_top_learners(lab, limit)
                elif fallback_intent == "greeting":
                    return await self._handle_greeting()
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
