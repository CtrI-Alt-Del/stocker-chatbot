from datetime import datetime

from google.genai import types


# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


def __update_interaction_history(session_service, app_name, user_id, session_id, entry):
    try:
        session = session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

        interaction_history = session.state.get("interaction_history", [])

        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        interaction_history.append(entry)

        updated_state = session.state.copy()
        updated_state["interaction_history"] = interaction_history

        session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            state=updated_state,
        )
    except Exception as e:
        # print(f"Error updating interaction history: {e}")
        pass


def __add_user_query_to_history(session_service, app_name, user_id, session_id, query):
    __update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {
            "action": "user_query",
            "query": query,
        },
    )


def __add_agent_response_to_history(
    session_service, app_name, user_id, session_id, agent_name, response
):
    __update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {
            "action": "agent_response",
            "agent": agent_name,
            "response": response,
        },
    )

    async def process_agent_response(event):
        if event.is_final_response():
            if (
                event.content
                and event.content.parts
                and hasattr(event.content.parts[0], "text")
                and event.content.parts[0].text
            ):
                final_response = event.content.parts[0].text.strip()

        return final_response

    async def call_agent_async(self, runner, user_id, session_id, query):
        content = types.Content(role="user", parts=[types.Part(text=query)])
        final_response_text = None
        agent_name = None

        try:
            async for event in runner.run_async(
                user_id=user_id, session_id=session_id, new_message=content
            ):
                if event.author:
                    agent_name = event.author

                response = await self.process_agent_response(event)
                if response:
                    final_response_text = response
        except Exception as e:
            print(
                f"{Colors.BG_RED}{Colors.WHITE}ERROR during agent run: {e}{Colors.RESET}"
            )

        if final_response_text and agent_name:
            self.__add_agent_response_to_history(
                runner.session_service,
                runner.app_name,
                user_id,
                session_id,
                agent_name,
                final_response_text,
            )

            return final_response_text
