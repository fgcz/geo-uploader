import logging

import requests


def notify_server(config: dict[str, str], action: str, logger: logging.Logger) -> bool:
    """Notify the server about completed actions.
    action is either md5|upload"""
    if not config:
        logger.error("Missing server notification configuration")
        return False

    session_id = config.get("session_id")
    server_url = config.get("server_url")

    if not session_id or not server_url:
        logger.error("Missing session ID or server URL in configuration")
        return False

    try:
        # Construct the endpoint URL
        endpoint = f"{server_url.rstrip('/')}/sessions/{session_id}/finish/{action}"

        # Send the POST request
        logger.info(f"Notifying server at {endpoint}")
        response = requests.post(endpoint, timeout=300)
        response.raise_for_status()  # Raise an exception for HTTP errors

        logger.info(f"Server notification successful: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to notify the server: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during server notification: {e}")
        return False
