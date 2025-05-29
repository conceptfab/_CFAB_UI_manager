from typing import Dict, List, Optional

from PyQt6.QtWidgets import QWidget

from .translator import Translator


class TranslationManager:
    _instance = None
    _translator: Optional[Translator] = None
    _translatable_widgets: List[QWidget] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TranslationManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, default_language: str = "pl") -> None:
        """
        Inicjalizuje menedżer tłumaczeń.
        """
        if cls._translator is None:
            cls._translator = Translator(default_language)

    @classmethod
    def get_translator(cls) -> Translator:
        """
        Zwraca instancję translatora.
        """
        if cls._translator is None:
            cls.initialize()
        return cls._translator

    @classmethod
    def set_language(cls, language_code: str) -> bool:
        """
        Ustawia język dla całej aplikacji.
        """
        if cls._translator is None:
            cls.initialize()

        if cls._translator.set_language(language_code):
            cls.update_all_widgets()
            return True
        return False

    @classmethod
    def register_widget(cls, widget: QWidget) -> None:
        """
        Rejestruje widget do automatycznej aktualizacji tłumaczeń.
        """
        if widget not in cls._translatable_widgets:
            cls._translatable_widgets.append(widget)

    @classmethod
    def unregister_widget(cls, widget: QWidget) -> None:
        """
        Usuwa widget z listy automatycznej aktualizacji tłumaczeń.
        """
        if widget in cls._translatable_widgets:
            cls._translatable_widgets.remove(widget)

    @classmethod
    def update_all_widgets(cls) -> None:
        """
        Aktualizuje wszystkie zarejestrowane widgety.
        """
        for widget in cls._translatable_widgets:
            if hasattr(widget, "update_translations"):
                widget.update_translations()
