# notification_manager.py

from plyer import notification
import logging
from win10toast import ToastNotifier

def show_notification(title, message, app_icon=None, timeout=5):
    """
    Displays a system notification using plyer. Falls back to win10toast if plyer is not supported.

    Args:
        title (str): The title of the notification.
        message (str): The message body of the notification.
        app_icon (str, optional): Path to the icon file. Defaults to None.
        timeout (int, optional): Duration in seconds for which the notification is displayed. Defaults to 5.
    """
    try:
        notification.notify(
            title=title,
            message=message,
            app_icon=app_icon,
            timeout=timeout
        )
    except NotImplementedError:
        try:
            toaster = ToastNotifier()
            toaster.show_toast(title, message, duration=timeout, threaded=True)
        except Exception as e:
            logging.error(f"Failed to show notification: {e}")
