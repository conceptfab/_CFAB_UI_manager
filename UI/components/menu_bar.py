from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenuBar

from UI.about_dialog import AboutDialog
from utils.translation_manager import TranslationManager


def show_about_dialog(main_window):
    dialog = AboutDialog(main_window)
    dialog.exec()


def create_menu_bar(main_window):
    menu_bar = QMenuBar(main_window)
    main_window.setMenuBar(menu_bar)

    # Menu Plik
    file_menu = menu_bar.addMenu(TranslationManager.translate("app.menu.file"))

    new_action = QAction(TranslationManager.translate("app.menu.new"), main_window)
    new_action.setShortcut("Ctrl+N")
    new_action.setStatusTip(TranslationManager.translate("app.menu.new"))
    new_action.triggered.connect(
        lambda: main_window.update_status(TranslationManager.translate("app.menu.new"))
    )
    file_menu.addAction(new_action)

    open_action = QAction(TranslationManager.translate("app.menu.open"), main_window)
    open_action.setShortcut("Ctrl+O")
    open_action.setStatusTip(TranslationManager.translate("app.menu.open"))
    open_action.triggered.connect(
        lambda: main_window.update_status(TranslationManager.translate("app.menu.open"))
    )
    file_menu.addAction(open_action)

    file_menu.addSeparator()

    exit_action = QAction(TranslationManager.translate("app.menu.exit"), main_window)
    exit_action.setShortcut("Ctrl+Q")
    exit_action.setStatusTip(TranslationManager.translate("app.menu.exit"))
    exit_action.triggered.connect(main_window.close)
    file_menu.addAction(exit_action)

    # Menu Edycja
    edit_menu = menu_bar.addMenu(TranslationManager.translate("app.menu.edit"))
    copy_action = QAction(TranslationManager.translate("app.menu.copy"), main_window)
    copy_action.setShortcut("Ctrl+C")
    copy_action.setStatusTip(TranslationManager.translate("app.menu.copy"))
    edit_menu.addAction(copy_action)

    # Dodaj separator i Hardware Profiler
    edit_menu.addSeparator()
    hardware_profiler_action = QAction(
        TranslationManager.translate("app.menu.hardware_profiler"), main_window
    )
    hardware_profiler_action.setStatusTip(
        TranslationManager.translate("app.menu.hardware_profiler_tip")
    )
    hardware_profiler_action.triggered.connect(main_window.show_hardware_profiler)
    edit_menu.addAction(hardware_profiler_action)

    # Separator i Preferencje
    edit_menu.addSeparator()
    preferences_action = QAction(
        TranslationManager.translate("app.menu.preferences"), main_window
    )
    preferences_action.setStatusTip(
        TranslationManager.translate("app.menu.preferences")
    )
    preferences_action.triggered.connect(main_window.show_preferences_dialog)
    edit_menu.addAction(preferences_action)

    # Menu Pomoc
    help_menu = menu_bar.addMenu(TranslationManager.translate("app.menu.help"))
    about_action = QAction(TranslationManager.translate("app.menu.about"), main_window)
    about_action.setStatusTip(TranslationManager.translate("app.menu.about"))
    about_action.triggered.connect(lambda: show_about_dialog(main_window))
    help_menu.addAction(about_action)

    return menu_bar
