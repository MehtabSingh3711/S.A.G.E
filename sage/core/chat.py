"""SAGE chat — interactive chat mode using NotebookLM + GLM-5 formatting."""

from __future__ import annotations

import asyncio
import logging

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from config import OLLAMA_MODEL, OLLAMA_BASE_URL, NOTEBOOKLM_NOTEBOOK_ID
from ui.theme import console, COLORS, print_error
from ui.panels import make_chat_header, make_chat_message

logger = logging.getLogger("sage.chat")

CHAT_FORMAT_PROMPT = """Format this answer beautifully for a student.
Keep all the factual content intact.
Add structure with headers if the answer is long.
Highlight key terms in bold.
Keep citations as [Source: ...] references.

Raw answer: {answer}"""


async def _query_notebook(query: str) -> tuple[str, list[str]]:
    """Query NotebookLM and return (answer, sources)."""
    try:
        from notebooklm import NotebookLMClient
    except ImportError:
        return (
            "NotebookLM client not available. Install with: "
            "pip install notebooklm-py[browser]",
            [],
        )

    notebook_id = NOTEBOOKLM_NOTEBOOK_ID
    if not notebook_id:
        return "Notebook ID not configured. Run: sage init", []

    try:
        async with await NotebookLMClient.from_storage() as client:
            result = await client.chat.ask(notebook_id, query)
            sources = getattr(result, "sources", []) or []
            source_names = [str(s) for s in sources]
            return result.answer, source_names
    except Exception as e:
        logger.error(f"NotebookLM query error: {e}")
        return f"Error querying notebook: {e}", []


async def _format_response(raw_answer: str) -> str:
    """Use GLM-5 to format the raw answer beautifully."""
    try:
        llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.3,
        )
        response = await llm.ainvoke([
            HumanMessage(content=CHAT_FORMAT_PROMPT.format(answer=raw_answer)),
        ])
        return response.content.strip()
    except Exception as e:
        logger.warning(f"GLM-5 formatting failed: {e}, returning raw answer")
        return raw_answer


async def one_shot_query(query: str) -> None:
    """Execute a single query and display the result."""
    console.print(make_chat_header())
    console.print()

    with console.status(
        f"[sage.primary]Querying notebook...[/]",
        spinner="dots",
    ):
        raw_answer, sources = await _query_notebook(query)

    with console.status(
        f"[sage.primary]Formatting response...[/]",
        spinner="dots",
    ):
        formatted = await _format_response(raw_answer)

    # Display
    console.print(make_chat_message("user", query))
    console.print()
    console.print(make_chat_message("sage", formatted, sources))
    console.print()


async def chat_loop() -> None:
    """Interactive chat loop with NotebookLM + GLM-5."""
    console.print(make_chat_header())
    console.print()
    console.print(
        f"  [sage.muted]Type your questions below. "
        f"Press Ctrl+C or type 'exit' to quit.[/]"
    )
    console.print()

    conversation_history: list[tuple[str, str]] = []

    while True:
        try:
            # Prompt
            query = console.input(
                f"  [{COLORS['accent']}]› [/]"
            ).strip()

            if not query:
                continue
            if query.lower() in ("exit", "quit", "q"):
                console.print(
                    f"\n  [sage.muted]Goodbye! Happy studying. 📚[/]\n"
                )
                break

            # Display user message
            console.print(make_chat_message("user", query))
            console.print()

            # Query NotebookLM
            with console.status(
                f"  [sage.primary]Thinking...[/]",
                spinner="dots",
            ):
                raw_answer, sources = await _query_notebook(query)
                formatted = await _format_response(raw_answer)

            # Display response
            console.print(make_chat_message("sage", formatted, sources))
            console.print()

            conversation_history.append((query, formatted))

        except KeyboardInterrupt:
            console.print(
                f"\n  [sage.muted]Goodbye! Happy studying. 📚[/]\n"
            )
            break
        except EOFError:
            break
