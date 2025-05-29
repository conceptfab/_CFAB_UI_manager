# Prosty przykład, można rozbudować o np. tymczasowe wiadomości, progress bar itp.
class StatusBarManager:
    def __init__(self, status_bar):
        self.status_bar = status_bar

    def set_message(self, message, timeout=0):
        """Ustawia wiadomość na pasku statusu.
        Jeśli timeout > 0, wiadomość zniknie po tym czasie (w milisekundach).
        """
        self.status_bar.showMessage(message, timeout)

    def clear_message(self):
        self.status_bar.clearMessage()