import logging

from PyQt6.QtCore import QDate, QDateTime, Qt, QTime
from PyQt6.QtGui import QColor, QIcon, QPixmap  # Dodano QPixmap, QColor
from PyQt6.QtWidgets import (
    QCalendarWidget,  # Dodano QTableWidgetItem
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QTimeEdit,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class UIShowcaseWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("UIShowcaseWidgetItself")
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # --- Grupa: Podstawowe Kontrolki ---
        group_basic = QGroupBox("Podstawowe Kontrolki")
        group_basic.setObjectName("GroupBasic")
        layout_basic = QGridLayout()

        layout_basic.addWidget(QLabel("QLabel:"), 0, 0)
        lbl = QLabel("Przykładowa etykieta")
        lbl.setObjectName("SampleLabel")
        layout_basic.addWidget(lbl, 0, 1)

        layout_basic.addWidget(QLabel("QPushButton:"), 1, 0)
        btn = QPushButton("Zwykły Przycisk")
        btn.setObjectName("SampleButton")
        layout_basic.addWidget(btn, 1, 1)

        layout_basic.addWidget(QLabel("QPushButton (Disabled):"), 2, 0)
        btn_disabled = QPushButton("Wyłączony Przycisk")
        btn_disabled.setEnabled(False)
        btn_disabled.setObjectName("SampleButtonDisabled")
        layout_basic.addWidget(btn_disabled, 2, 1)

        layout_basic.addWidget(QLabel("QToolButton:"), 3, 0)
        tool_btn = QToolButton()
        tool_btn.setText("Tool")
        # Przykładowa ikona (może wymagać dostosowania ścieżki lub użycia zasobów Qt)
        try:
            # Spróbuj załadować standardową ikonę, jeśli dostępna
            icon = self.style().standardIcon(
                self.style().StandardPixmap.SP_DialogOpenButton
            )
            if not icon.isNull():
                tool_btn.setIcon(icon)
            else:  # Fallback na prostą ikonę z QPixmap
                pixmap = QPixmap(16, 16)
                pixmap.fill(QColor("blue"))
                tool_btn.setIcon(QIcon(pixmap))
        except Exception as e:
            logger.error(f"Nie udało się ustawić ikony dla QToolButton: {e}")
            # Można zostawić bez ikony lub dodać tekst zastępczy
        tool_btn.setObjectName("SampleToolButton")
        layout_basic.addWidget(tool_btn, 3, 1)

        layout_basic.addWidget(QLabel("QLineEdit:"), 4, 0)
        le = QLineEdit()
        le.setPlaceholderText("Wpisz tekst...")
        le.setObjectName("SampleLineEdit")
        layout_basic.addWidget(le, 4, 1)

        layout_basic.addWidget(QLabel("QLineEdit (Disabled):"), 5, 0)
        le_disabled = QLineEdit("Tylko do odczytu")
        le_disabled.setEnabled(False)
        le_disabled.setObjectName("SampleLineEditDisabled")
        layout_basic.addWidget(le_disabled, 5, 1)

        group_basic.setLayout(layout_basic)
        main_layout.addWidget(group_basic)

        # --- Grupa: Przyciski Wyboru ---
        group_choices = QGroupBox("Przyciski Wyboru")
        group_choices.setObjectName("GroupChoices")
        layout_choices = QGridLayout()

        layout_choices.addWidget(QLabel("QCheckBox:"), 0, 0)
        cb = QCheckBox("Opcja do zaznaczenia")
        cb.setObjectName("SampleCheckBox")
        layout_choices.addWidget(cb, 0, 1)

        layout_choices.addWidget(QLabel("QCheckBox (Tristate):"), 1, 0)
        cb_tri = QCheckBox("Opcja trójstanowa")
        cb_tri.setTristate(True)
        cb_tri.setCheckState(Qt.CheckState.PartiallyChecked)
        cb_tri.setObjectName("SampleCheckBoxTristate")
        layout_choices.addWidget(cb_tri, 1, 1)

        layout_choices.addWidget(QLabel("QRadioButton (1/2):"), 2, 0)
        rb1 = QRadioButton("Opcja Radio 1")
        rb1.setChecked(True)
        rb1.setObjectName("SampleRadioButton1")
        layout_choices.addWidget(rb1, 2, 1)

        layout_choices.addWidget(QLabel("QRadioButton (2/2):"), 3, 0)
        rb2 = QRadioButton("Opcja Radio 2")
        rb2.setObjectName("SampleRadioButton2")
        layout_choices.addWidget(rb2, 3, 1)

        group_choices.setLayout(layout_choices)
        main_layout.addWidget(group_choices)

        # --- Grupa: Listy i Pola Wyboru ---
        group_lists = QGroupBox("Listy i Pola Wyboru")
        group_lists.setObjectName("GroupLists")
        layout_lists = QGridLayout()

        layout_lists.addWidget(QLabel("QComboBox:"), 0, 0)
        combo = QComboBox()
        combo.addItems(["Element 1", "Element 2", "Dłuższy element 3", "Element 4"])
        combo.setObjectName("SampleComboBox")
        layout_lists.addWidget(combo, 0, 1)

        layout_lists.addWidget(QLabel("QComboBox (Editable):"), 1, 0)
        combo_edit = QComboBox()
        combo_edit.addItems(["Edytowalny 1", "Edytowalny 2"])
        combo_edit.setEditable(True)
        combo_edit.setObjectName("SampleComboBoxEditable")
        layout_lists.addWidget(combo_edit, 1, 1)

        group_lists.setLayout(layout_lists)
        main_layout.addWidget(group_lists)

        # --- Grupa: Elementy numeryczne i zakresy ---
        group_numeric = QGroupBox("Elementy Numeryczne i Zakresy")
        group_numeric.setObjectName("GroupNumeric")
        layout_numeric = QGridLayout()

        layout_numeric.addWidget(QLabel("QSpinBox:"), 0, 0)
        spin = QSpinBox()
        spin.setRange(0, 100)
        spin.setValue(25)
        spin.setObjectName("SampleSpinBox")
        layout_numeric.addWidget(spin, 0, 1)

        layout_numeric.addWidget(QLabel("QDoubleSpinBox:"), 1, 0)
        dspin = QDoubleSpinBox()
        dspin.setRange(0.0, 10.0)
        dspin.setSingleStep(0.1)
        dspin.setValue(2.5)
        dspin.setObjectName("SampleDoubleSpinBox")
        layout_numeric.addWidget(dspin, 1, 1)

        layout_numeric.addWidget(QLabel("QSlider (Horizontal):"), 2, 0)
        slider_h = QSlider(Qt.Orientation.Horizontal)
        slider_h.setObjectName("SampleSliderHorizontal")
        slider_h.setValue(30)
        layout_numeric.addWidget(slider_h, 2, 1)

        layout_numeric.addWidget(
            QLabel("QSlider (Vertical):"), 3, 0, 1, 1, Qt.AlignmentFlag.AlignTop
        )
        slider_v = QSlider(Qt.Orientation.Vertical)
        slider_v.setObjectName("SampleSliderVertical")
        slider_v.setValue(70)
        layout_numeric.addWidget(slider_v, 3, 1, Qt.AlignmentFlag.AlignHCenter)

        layout_numeric.addWidget(
            QLabel("QDial:"), 4, 0, 1, 1, Qt.AlignmentFlag.AlignTop
        )
        dial = QDial()
        dial.setNotchesVisible(True)
        dial.setObjectName("SampleDial")
        dial.setValue(50)
        layout_numeric.addWidget(dial, 4, 1, Qt.AlignmentFlag.AlignHCenter)

        layout_numeric.addWidget(QLabel("QProgressBar:"), 5, 0)
        pbar = QProgressBar()
        pbar.setValue(60)
        pbar.setObjectName("SampleProgressBar")
        layout_numeric.addWidget(pbar, 5, 1)

        layout_numeric.addWidget(QLabel("QLCDNumber:"), 6, 0)
        lcd = QLCDNumber(5)  # 5 cyfr
        lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        lcd.display(12345)
        lcd.setObjectName("SampleLCDNumber")
        layout_numeric.addWidget(lcd, 6, 1)

        group_numeric.setLayout(layout_numeric)
        main_layout.addWidget(group_numeric)

        # --- Grupa: Data i Czas ---
        group_datetime = QGroupBox("Data i Czas")
        group_datetime.setObjectName("GroupDateTime")
        layout_datetime = QGridLayout()

        layout_datetime.addWidget(QLabel("QDateEdit:"), 0, 0)
        date_edit = QDateEdit(QDate.currentDate())
        date_edit.setCalendarPopup(True)
        date_edit.setObjectName("SampleDateEdit")
        layout_datetime.addWidget(date_edit, 0, 1)

        layout_datetime.addWidget(QLabel("QTimeEdit:"), 1, 0)
        time_edit = QTimeEdit(QTime.currentTime())
        time_edit.setObjectName("SampleTimeEdit")
        layout_datetime.addWidget(time_edit, 1, 1)

        layout_datetime.addWidget(QLabel("QDateTimeEdit:"), 2, 0)
        datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        datetime_edit.setCalendarPopup(True)
        datetime_edit.setObjectName("SampleDateTimeEdit")
        layout_datetime.addWidget(datetime_edit, 2, 1)

        layout_datetime.addWidget(QLabel("QCalendarWidget:"), 3, 0, 1, 2)
        calendar = QCalendarWidget()
        calendar.setObjectName("SampleCalendarWidget")
        layout_datetime.addWidget(calendar, 4, 0, 1, 2)

        group_datetime.setLayout(layout_datetime)
        main_layout.addWidget(group_datetime)

        # --- Grupa: Pola Tekstowe ---
        group_text_areas = QGroupBox("Pola Tekstowe")
        group_text_areas.setObjectName("GroupTextAreas")
        layout_text_areas = QGridLayout()

        layout_text_areas.addWidget(
            QLabel("QTextEdit:"), 0, 0, Qt.AlignmentFlag.AlignTop
        )
        text_edit = QTextEdit(
            "To jest <b>QTextEdit</b> z formatowaniem <i>HTML</i>.<br>Można w nim pisać wiele linii."
        )
        text_edit.setObjectName("SampleTextEdit")
        text_edit.setFixedHeight(100)
        layout_text_areas.addWidget(text_edit, 0, 1)

        layout_text_areas.addWidget(
            QLabel("QPlainTextEdit:"), 1, 0, Qt.AlignmentFlag.AlignTop
        )
        plain_text_edit = QPlainTextEdit(
            "To jest QPlainTextEdit.\nObsługuje tylko czysty tekst, ale jest wydajniejszy dla dużych plików."
        )
        plain_text_edit.setObjectName("SamplePlainTextEdit")
        plain_text_edit.setFixedHeight(100)
        layout_text_areas.addWidget(plain_text_edit, 1, 1)

        group_text_areas.setLayout(layout_text_areas)
        main_layout.addWidget(group_text_areas)

        # --- Grupa: Widoki Elementów (Item Views) ---
        group_item_views = QGroupBox("Widoki Elementów (Item Views)")
        group_item_views.setObjectName("GroupItemViews")
        layout_item_views = QGridLayout()

        layout_item_views.addWidget(
            QLabel("QListWidget:"), 0, 0, Qt.AlignmentFlag.AlignTop
        )
        list_widget = QListWidget()
        list_widget.addItems([f"Pozycja {i+1}" for i in range(5)])
        list_widget.setObjectName("SampleListWidget")
        list_widget.setFixedHeight(120)
        layout_item_views.addWidget(list_widget, 0, 1)

        layout_item_views.addWidget(
            QLabel("QTableWidget:"), 1, 0, Qt.AlignmentFlag.AlignTop
        )
        table_widget = QTableWidget(3, 3)
        table_widget.setHorizontalHeaderLabels(["Kolumna A", "Kolumna B", "Kolumna C"])
        table_widget.setVerticalHeaderLabels(["Wiersz 1", "Wiersz 2", "Wiersz 3"])
        for r in range(3):
            for c in range(3):
                table_widget.setItem(r, c, QTableWidgetItem(f"Komórka {r+1},{c+1}"))
        table_widget.setObjectName("SampleTableWidget")
        table_widget.setFixedHeight(140)  # Zwiększono wysokość
        layout_item_views.addWidget(table_widget, 1, 1)

        layout_item_views.addWidget(
            QLabel("QTreeWidget:"), 2, 0, Qt.AlignmentFlag.AlignTop
        )
        tree_widget = QTreeWidget()
        tree_widget.setHeaderLabels(["Nazwa", "Wartość", "Opis"])
        parent_item1 = QTreeWidgetItem(
            tree_widget, ["Element Główny 1", "W1", "Opis G1"]
        )
        QTreeWidgetItem(parent_item1, ["Dziecko 1.1", "W1.1", "Opis D1.1"])
        child1_2 = QTreeWidgetItem(parent_item1, ["Dziecko 1.2", "W1.2", "Opis D1.2"])
        QTreeWidgetItem(child1_2, ["Wnuk 1.2.1", "W1.2.1", "Opis W1.2.1"])
        QTreeWidgetItem(tree_widget, ["Element Główny 2", "W2", "Opis G2"])
        tree_widget.expandAll()
        tree_widget.setObjectName("SampleTreeWidget")
        tree_widget.setFixedHeight(180)  # Zwiększono wysokość
        layout_item_views.addWidget(tree_widget, 2, 1)

        group_item_views.setLayout(layout_item_views)
        main_layout.addWidget(group_item_views)

        # --- Grupa: Kontenery ---
        group_containers = QGroupBox("Kontenery")
        group_containers.setObjectName("GroupContainers")
        layout_containers_main = QVBoxLayout()

        # QFrame
        frame_label = QLabel("QFrame (różne kształty i cienie):")
        layout_containers_main.addWidget(frame_label)
        frame_layout = QHBoxLayout()

        frame_box = QFrame()
        frame_box.setFrameShape(QFrame.Shape.Box)
        frame_box.setFrameShadow(QFrame.Shadow.Raised)
        frame_box.setLineWidth(2)
        frame_box.setMidLineWidth(1)
        frame_box.setFixedSize(60, 60)
        frame_box.setObjectName("SampleFrameBox")
        frame_layout.addWidget(frame_box)

        frame_panel = QFrame()
        frame_panel.setFrameShape(QFrame.Shape.StyledPanel)
        frame_panel.setFrameShadow(QFrame.Shadow.Sunken)
        frame_panel.setFixedSize(60, 60)
        frame_panel.setObjectName("SampleFramePanel")
        frame_layout.addWidget(frame_panel)

        frame_vline = QFrame()  # Zmieniono na VLine dla odmiany
        frame_vline.setFrameShape(QFrame.Shape.VLine)
        frame_vline.setFrameShadow(QFrame.Shadow.Sunken)  # Lepiej widoczne
        frame_vline.setFixedWidth(20)
        frame_vline.setFixedHeight(50)
        frame_vline.setObjectName("SampleFrameVLine")
        frame_layout.addWidget(frame_vline)

        layout_containers_main.addLayout(frame_layout)

        # QTabWidget wewnątrz podglądu
        tabs_label = QLabel("QTabWidget (w podglądzie):")
        layout_containers_main.addWidget(tabs_label)

        preview_tabs = QTabWidget()
        preview_tabs.setObjectName(
            "SampleTabWidgetInShowcase"
        )  # Unikalna nazwa obiektu

        tab_a_content = QWidget()
        tab_a_layout = QVBoxLayout(tab_a_content)
        tab_a_layout.addWidget(QLabel("Zawartość pod-zakładki A"))
        btn_in_tab = QPushButton("Przycisk A")
        btn_in_tab.setObjectName("ButtonInSubTabA")
        tab_a_layout.addWidget(btn_in_tab)
        preview_tabs.addTab(tab_a_content, "Pod-Zakładka A")

        tab_b_content = QWidget()
        tab_b_layout = QVBoxLayout(tab_b_content)
        tab_b_layout.addWidget(QLabel("Zawartość pod-zakładki B"))
        chk_in_tab = QCheckBox("Opcja B")
        chk_in_tab.setObjectName("CheckboxInSubTabB")
        tab_b_layout.addWidget(chk_in_tab)
        preview_tabs.addTab(tab_b_content, "Pod-Zakładka B")

        preview_tabs.setFixedHeight(150)
        layout_containers_main.addWidget(preview_tabs)

        group_containers.setLayout(layout_containers_main)
        main_layout.addWidget(group_containers)

        main_layout.addStretch()
        self.setLayout(main_layout)
