# ui/tab_export.py
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QLineEdit, QPushButton, QMessageBox, QLabel, QFileDialog)
from PySide6.QtCore import QSettings
from bundle_packer import update_bundle_with_card_data
import config
import i18n


class TabExport(QWidget):
    def __init__(self, project_manager):
        super().__init__()
        self.pm = project_manager
        self.settings = QSettings("ModdingTool", "PvZHeroesEditor")
        self._setup_ui()
        self._load_settings()
        self.retranslate_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)

        self.export_group = QGroupBox()
        export_layout = QVBoxLayout(self.export_group)
        export_layout.setContentsMargins(30, 40, 30, 40)
        export_layout.setSpacing(25)

        self.info = QLabel()
        self.info.setStyleSheet("color: #aaa; font-size: 14px;")
        export_layout.addWidget(self.info)

        b_src_layout = QHBoxLayout()
        self.lbl_src = QLabel()
        b_src_layout.addWidget(self.lbl_src)
        self.bundle_src_input = QLineEdit()
        self.bundle_src_input.setMinimumHeight(35)
        b_src_layout.addWidget(self.bundle_src_input)
        self.btn_browse_src = QPushButton()
        self.btn_browse_src.clicked.connect(self._browse_src)
        b_src_layout.addWidget(self.btn_browse_src)
        export_layout.addLayout(b_src_layout)

        b_out_layout = QHBoxLayout()
        self.lbl_out = QLabel()
        b_out_layout.addWidget(self.lbl_out)
        self.bundle_out_input = QLineEdit()
        self.bundle_out_input.setMinimumHeight(35)
        b_out_layout.addWidget(self.bundle_out_input)
        self.btn_browse_out = QPushButton()
        self.btn_browse_out.clicked.connect(self._browse_out)
        b_out_layout.addWidget(self.btn_browse_out)
        export_layout.addLayout(b_out_layout)

        self.btn_pack_bundle = QPushButton()
        self.btn_pack_bundle.setMinimumHeight(45)
        self.btn_pack_bundle.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.btn_pack_bundle.clicked.connect(self.pack_to_bundle)
        export_layout.addWidget(self.btn_pack_bundle)

        main_layout.addWidget(self.export_group)
        main_layout.addStretch()

    def retranslate_ui(self):
        self.export_group.setTitle(i18n.t("export.group"))
        self.info.setText(i18n.t("export.info"))
        self.lbl_src.setText(i18n.t("export.src"))
        self.lbl_out.setText(i18n.t("export.out"))
        self.btn_browse_src.setText(i18n.t("common.browse"))
        self.btn_browse_out.setText(i18n.t("common.browse"))
        self.btn_pack_bundle.setText(i18n.t("export.pack"))

    def _browse_src(self):
        path, _ = QFileDialog.getOpenFileName(
            self, i18n.t("export.pick_src"), config.DATA_DIR, "All Files (*.*)"
        )
        if path:
            self.bundle_src_input.setText(path)

    def _browse_out(self):
        path, _ = QFileDialog.getSaveFileName(
            self, i18n.t("export.pick_out"), config.OUT_DIR, "All Files (*.*)"
        )
        if path:
            self.bundle_out_input.setText(path)

    def _load_settings(self):
        default_src = os.path.join(config.DATA_DIR, config.DEFAULT_CARD_BUNDLE)
        default_out = os.path.join(config.OUT_DIR, config.DEFAULT_CARD_BUNDLE)
        self.bundle_src_input.setText(self.settings.value("bundle_src_path", default_src))
        self.bundle_out_input.setText(self.settings.value("bundle_out_path", default_out))

    def _save_settings(self):
        self.settings.setValue("bundle_src_path", self.bundle_src_input.text().strip())
        self.settings.setValue("bundle_out_path", self.bundle_out_input.text().strip())

    def export_card(self):
        self.pack_to_bundle()

    def pack_to_bundle(self):
        self._save_settings()

        if not self.pm.current_project_name:
            QMessageBox.warning(self, i18n.t("common.warning"), i18n.t("export.no_project"))
            return

        if not self.pm.project_cards:
            QMessageBox.warning(self, i18n.t("common.warning"), i18n.t("export.empty"))
            return

        bundle_src = self.bundle_src_input.text().strip()
        bundle_out = self.bundle_out_input.text().strip()
        if not bundle_src or not bundle_out:
            QMessageBox.warning(self, i18n.t("common.warning"), i18n.t("export.path_missing"))
            return

        try:
            success, msg = update_bundle_with_card_data(
                bundle_in_path=bundle_src,
                bundle_out_path=bundle_out,
                modded_card_dict=self.pm.project_cards,
                target_asset_name="cards",
            )
            if success:
                QMessageBox.information(
                    self,
                    i18n.t("export.ok_title"),
                    i18n.t("export.ok_body", name=self.pm.current_project_name, msg=msg),
                )
            else:
                QMessageBox.critical(self, i18n.t("export.fail_title"), msg)
        except Exception as e:
            QMessageBox.critical(
                self, i18n.t("export.err_title"), i18n.t("export.err_body", err=str(e))
            )
