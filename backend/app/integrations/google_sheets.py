"""
Google Sheets integration: log Q&A pairs to a spreadsheet for review.
Uses gspread with service account credentials.
"""
import json
from datetime import datetime
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_worksheet = None


def _get_worksheet():
    global _worksheet
    if _worksheet is not None:
        return _worksheet

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        creds_data = json.loads(settings.google_sheets_credentials_json)
        if not creds_data or creds_data == {}:
            return None

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = Credentials.from_service_account_info(creds_data, scopes=scopes)
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open_by_key(settings.google_sheets_spreadsheet_id)
        _worksheet = spreadsheet.sheet1

        # Ensure headers exist
        existing = _worksheet.row_values(1)
        if not existing:
            _worksheet.update("A1:F1", [["Timestamp", "User", "Question", "Answer", "Confidence", "Feedback"]])

        return _worksheet
    except Exception as e:
        logger.error("Failed to connect to Google Sheets", error=str(e))
        return None


def log_qa_to_sheets(
    user_email: str,
    question: str,
    answer: str,
    confidence: str,
    feedback: str = "",
):
    """Append a Q&A row to the configured Google Sheet."""
    ws = _get_worksheet()
    if ws is None:
        return

    try:
        ws.append_row(
            [
                datetime.utcnow().isoformat(),
                user_email,
                question,
                answer[:500],  # truncate long answers
                confidence,
                feedback,
            ],
            value_input_option="USER_ENTERED",
        )
        logger.info("Logged Q&A to Google Sheets")
    except Exception as e:
        logger.error("Failed to log to Google Sheets", error=str(e))
