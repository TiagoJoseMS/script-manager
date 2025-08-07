# -*- coding: utf-8 -*-
"""
Script Manager Plugin for QGIS
Monitors and executes PyQGIS scripts automatically with enhanced error handling
Compatible with both Qt5 and Qt6
Author: Tiago José M Silva
"""

import os
import sys
import traceback
import io
import contextlib
from pathlib import Path

from qgis.PyQt.QtCore import QTimer, QFileSystemWatcher, pyqtSignal, QObject, QSettings, QT_VERSION_STR
from qgis.PyQt.QtWidgets import (QApplication, QAction, QMenu, QMessageBox, QDialog, QVBoxLayout, 
                                QHBoxLayout, QListWidget, QListWidgetItem, QLabel, 
                                QPushButton, QTextEdit, QSplitter, QWidget, QScrollArea,
                                QTabWidget, QPlainTextEdit)
from qgis.PyQt.QtGui import QIcon, QFont, QTextCursor
from qgis.PyQt.QtCore import Qt

QT_VERSION = 6 if QT_VERSION_STR.startswith('6') else 5

from qgis.core import QgsMessageLog, Qgis
from qgis.utils import iface


class SafeScriptExecutor:
    """Script executor with output capture and error handling"""
    
    def __init__(self):
        self.output_buffer = io.StringIO()
        self.error_buffer = io.StringIO()
    
    @contextlib.contextmanager
    def capture_output(self):
        """Context manager to capture stdout and stderr"""
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = self.output_buffer
            sys.stderr = self.error_buffer
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    def get_captured_output(self):
        """Get captured output and errors"""
        output = self.output_buffer.getvalue()
        errors = self.error_buffer.getvalue()
        
        self.output_buffer.truncate(0)
        self.output_buffer.seek(0)
        self.error_buffer.truncate(0)
        self.error_buffer.seek(0)
        
        return output, errors
    
    def validate_script_imports(self, script_content):
        """Validate script imports for security"""
        risky_imports = [
            'subprocess.call',
            'subprocess.run',
            'subprocess.Popen',
            'os.system',
            'eval(',
            'exec(',
            '__import__',
        ]
        
        warnings = []
        for risky in risky_imports:
            if risky in script_content:
                warnings.append(f"⚠️ Potentially risky operation detected: {risky}")
        
        return warnings
    
    def prepare_safe_namespace(self, script_path):
        """Prepare a safe execution namespace with necessary imports"""
        script_globals = {
            '__name__': '__main__',
            '__file__': script_path,
            'QT_VERSION': QT_VERSION,
        }
        
        try:
            from qgis.core import (
                QgsProject, QgsVectorLayer, QgsRasterLayer, QgsMessageLog, 
                Qgis, QgsUnitTypes, QgsWkbTypes, QgsFeature, QgsGeometry,
                QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                QgsMapLayerProxyModel, QgsProcessingContext
            )
            from qgis.gui import QgsMapCanvas, QgsMapTool
            from qgis.utils import iface as qgis_iface
            
            script_globals.update({
                'QgsProject': QgsProject,
                'QgsVectorLayer': QgsVectorLayer,
                'QgsRasterLayer': QgsRasterLayer,
                'QgsFeature': QgsFeature,
                'QgsGeometry': QgsGeometry,
                'QgsCoordinateReferenceSystem': QgsCoordinateReferenceSystem,
                'QgsCoordinateTransform': QgsCoordinateTransform,
                'QgsMessageLog': QgsMessageLog,
                'QgsUnitTypes': QgsUnitTypes,
                'QgsWkbTypes': QgsWkbTypes,
                'QgsMapCanvas': QgsMapCanvas,
                'QgsMapTool': QgsMapTool,
                'QgsMapLayerProxyModel': QgsMapLayerProxyModel,
                'QgsProcessingContext': QgsProcessingContext,
                'iface': qgis_iface,
                'Qgis': Qgis,
            })
        except ImportError as e:
            QgsMessageLog.logMessage(f"Warning: Some QGIS imports failed: {str(e)}", 
                                   "Script Manager", Qgis.Warning)
        
        try:
            from qgis.PyQt.QtWidgets import (QMessageBox, QInputDialog, QFileDialog, 
                                           QProgressBar, QComboBox, QCheckBox)
            from qgis.PyQt.QtCore import Qt, QTimer, QThread, pyqtSignal
            from qgis.PyQt.QtGui import QIcon, QPixmap, QColor
            
            script_globals.update({
                'QMessageBox': QMessageBox,
                'QInputDialog': QInputDialog,
                'QFileDialog': QFileDialog,
                'QProgressBar': QProgressBar,
                'QComboBox': QComboBox,
                'QCheckBox': QCheckBox,
                'Qt': Qt,
                'QTimer': QTimer,
                'QThread': QThread,
                'pyqtSignal': pyqtSignal,
                'QIcon': QIcon,
                'QPixmap': QPixmap,
                'QColor': QColor
            })
        except ImportError as e:
            QgsMessageLog.logMessage(f"Warning: Some Qt imports failed: {str(e)}", 
                                   "Script Manager", Qgis.Warning)
        
        try:
            import json, math, datetime, re
            script_globals.update({
                'json': json,
                'math': math,
                'datetime': datetime,
                're': re,
            })
        except ImportError as e:
            QgsMessageLog.logMessage(f"Warning: Some standard library imports failed: {str(e)}", 
                                   "Script Manager", Qgis.Warning)
        
        return script_globals


class QtCompat:
    """Qt compatibility helper for Qt5/Qt6 differences"""
    
    @staticmethod
    def get_user_role():
        if QT_VERSION == 6:
            return Qt.ItemDataRole.UserRole
        else:
            return Qt.UserRole
    
    @staticmethod
    def get_horizontal():
        if QT_VERSION == 6:
            return Qt.Orientation.Horizontal
        else:
            return Qt.Horizontal
    
    @staticmethod
    def get_rich_text():
        if QT_VERSION == 6:
            return Qt.TextFormat.RichText
        else:
            return Qt.RichText
    
    @staticmethod
    def get_font_weight_bold():
        if QT_VERSION == 6:
            return QFont.Weight.Bold
        else:
            return QFont.Bold
    
    @staticmethod
    def exec_dialog(dialog):
        if QT_VERSION == 6:
            return dialog.exec()
        else:
            return dialog.exec_()


class Translator:
    """Translation manager for the Script Manager plugin"""
    
    def __init__(self):
        self.current_language = self.detect_qgis_language()
        self.translations = self.load_translations()
    
    def detect_qgis_language(self):
        try:
            settings = QSettings()
            locale = settings.value('locale/userLocale', 'en_US')
            language = locale[:2].lower()
            
            language_map = {
                'pt': 'pt_BR',
                'es': 'es_ES',
                'fr': 'fr_FR',
                'de': 'de_DE',
                'it': 'it_IT',
            }
            
            return language_map.get(language, language)
            
        except Exception:
            return 'en'
    
    def load_translations(self):
        return {
            'en': {
                'script_manager': 'Script Manager',
                'script_browser': 'Script Browser',
                'quick_access': 'Quick Access',
                'reload_scripts': 'Reload Scripts',
                'open_scripts_folder': 'Open Scripts Folder',
                'about': 'About',
                'no_scripts_found': 'No scripts found',
                'available_scripts': 'Available Scripts',
                'scripts_found': 'scripts found',
                'scripts': 'Scripts:',
                'select_script': 'Select a script',
                'description': 'Description:',
                'location': 'Location:',
                'file': 'File:',
                'execute_script': 'Execute Script',
                'refresh_list': 'Refresh List',
                'open_folder': 'Open Folder',
                'close': 'Close',
                'no_script_selected': 'No script selected',
                'output': 'Output',
                'console_output': 'Console Output',
                'clear_output': 'Clear Output',
                'warnings': 'Warnings',
                'script_executed': 'Script executed successfully!',
                'script_executed_warnings': 'Script executed with warnings',
                'error_executing': 'Error executing script',
                'scripts_reloaded': 'Scripts reloaded',
                'browser_opened': 'Browser opened with',
                'no_scripts_warning': 'No scripts found in folder',
                'error_opening_folder': 'Error opening folder',
                'output_captured': 'Output captured from script',
                'about_title': 'Script Manager v1.0',
                'about_subtitle': 'PyQGIS Script Management Plugin',
                'about_description': 'The Script Manager plugin provides an intuitive interface for organizing and executing PyQGIS scripts within QGIS.',
                'key_features': 'Key Features:',
                'feature_browser': 'Script Browser with output capture and detailed error reporting',
                'feature_quick': 'Quick Access menu with hover tooltips for fast script execution',
                'feature_monitor': 'Auto-monitoring: Automatically detects new scripts and file changes',
                'feature_management': 'Easy Management: Direct access to scripts folder and reload functionality',
                'feature_safety': 'Safe Execution: Script validation and error handling',
                'feature_output_capture': 'Output Capture: All print statements are captured and displayed',
                'feature_crash_prevention': 'Crash Prevention: Safe execution environment with error handling',
                'feature_script_validation': 'Script Validation: Pre-execution checks for security',
                'scripts_location': 'Scripts Location:',
                'currently_loaded': 'Currently loaded:',
                'getting_started': 'Getting Started:',
                'getting_started_1': '1. Click "Script Browser" to explore available scripts',
                'getting_started_2': '2. Use "Quick Access" for fast script execution',
                'getting_started_3': '3. Place your .py files in the scripts folder',
                'getting_started_4': '4. Use "Reload Scripts" to refresh the list',
                'getting_started_5': '5. Use print() statements in your scripts for output capture',
                'script_format': 'Script Format Example:',
                'error': 'Error',
                'script_error': 'Script Error',
                'validation_warnings': 'Script Validation Warnings',
                'check_log': 'Check QGIS log for more details.',
                'tooltip_browser': 'Open browser with detailed script descriptions and output capture',
                'tooltip_reload': 'Reload all scripts from folder',
                'tooltip_folder': 'Open the folder where scripts are stored',
                'tooltip_about': 'Information about Script Manager'
            },
            
            'pt_BR': {
                'script_manager': 'Gerenciador de Scripts',
                'script_browser': 'Navegador de Scripts',
                'quick_access': 'Acesso Rápido',
                'reload_scripts': 'Recarregar Scripts',
                'open_scripts_folder': 'Abrir Pasta de Scripts',
                'about': 'Sobre',
                'no_scripts_found': 'Nenhum script encontrado',
                'available_scripts': 'Scripts Disponíveis',
                'scripts_found': 'scripts encontrados',
                'scripts': 'Scripts:',
                'select_script': 'Selecione um script',
                'description': 'Descrição:',
                'location': 'Localização:',
                'file': 'Arquivo:',
                'execute_script': 'Executar Script',
                'refresh_list': 'Atualizar Lista',
                'open_folder': 'Abrir Pasta',
                'close': 'Fechar',
                'no_script_selected': 'Nenhum script selecionado',
                'output': 'Saída',
                'console_output': 'Saída do Console',
                'clear_output': 'Limpar Saída',
                'warnings': 'Avisos',
                'script_executed': 'Script executado com sucesso!',
                'script_executed_warnings': 'Script executado com avisos',
                'error_executing': 'Erro ao executar script',
                'scripts_reloaded': 'Scripts recarregados',
                'browser_opened': 'Navegador aberto com',
                'no_scripts_warning': 'Nenhum script encontrado na pasta',
                'error_opening_folder': 'Erro ao abrir pasta',
                'output_captured': 'Saída capturada do script',
                'about_title': 'Gerenciador de Scripts v1.0',
                'about_subtitle': 'Plugin de Gerenciamento de Scripts PyQGIS',
                'about_description': 'O plugin Gerenciador de Scripts fornece uma interface intuitiva para organizar e executar scripts PyQGIS dentro do QGIS.',
                'key_features': 'Principais Recursos:',
                'feature_browser': 'Navegador de Scripts com captura de saída e relatório detalhado de erros',
                'feature_quick': 'Menu de Acesso Rápido com dicas ao passar o mouse para execução rápida',
                'feature_monitor': 'Monitoramento Automático: Detecta automaticamente novos scripts e mudanças',
                'feature_management': 'Gerenciamento Fácil: Acesso direto à pasta de scripts e funcionalidade de recarregamento',
                'feature_safety': 'Execução Segura: Validação de script e tratamento de erros',
                'feature_output_capture': 'Captura de Saída: Todas as mensagens print são capturadas e exibidas',
                'feature_crash_prevention': 'Prevenção de Crashes: Ambiente de execução seguro com tratamento de erros',
                'feature_script_validation': 'Validação de Scripts: Verificações pré-execução para segurança',
                'scripts_location': 'Localização dos Scripts:',
                'currently_loaded': 'Atualmente carregados:',
                'getting_started': 'Como Começar:',
                'getting_started_1': '1. Clique em "Navegador de Scripts" para explorar scripts disponíveis',
                'getting_started_2': '2. Use "Acesso Rápido" para execução rápida de scripts',
                'getting_started_3': '3. Coloque seus arquivos .py na pasta de scripts',
                'getting_started_4': '4. Use "Recarregar Scripts" para atualizar a lista',
                'getting_started_5': '5. Use comandos print() nos seus scripts para captura de saída',
                'script_format': 'Exemplo de Formato de Script:',
                'error': 'Erro',
                'script_error': 'Erro no Script',
                'validation_warnings': 'Avisos de Validação do Script',
                'check_log': 'Verifique o log do QGIS para mais detalhes.',
                'tooltip_browser': 'Abrir navegador com descrições detalhadas dos scripts e captura de saída',
                'tooltip_reload': 'Recarregar todos os scripts da pasta',
                'tooltip_folder': 'Abrir a pasta onde os scripts são armazenados',
                'tooltip_about': 'Informações sobre o Gerenciador de Scripts'
            }
        }
    
    def tr(self, key, fallback=None):
        if fallback is None:
            fallback = key
        
        if self.current_language in self.translations:
            return self.translations[self.current_language].get(key, fallback)
        
        if 'en' in self.translations:
            return self.translations['en'].get(key, fallback)
        
        return fallback


_translator = Translator()

def tr(key, fallback=None):
    return _translator.tr(key, fallback)


class ScriptWatcher(QObject):
    """File system watcher for monitoring changes in the scripts folder"""
    
    scripts_changed = pyqtSignal()
    
    def __init__(self, scripts_path):
        super().__init__()
        self.scripts_path = scripts_path
        self.watcher = QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self.on_directory_changed)
        self.watcher.fileChanged.connect(self.on_file_changed)
        
        if os.path.exists(scripts_path):
            self.watcher.addPath(scripts_path)
    
    def on_directory_changed(self, path):
        self.scripts_changed.emit()
    
    def on_file_changed(self, path):
        if os.path.exists(path) and path not in self.watcher.files():
            self.watcher.addPath(path)
        self.scripts_changed.emit()
    
    def add_file_to_watch(self, file_path):
        if os.path.exists(file_path) and file_path not in self.watcher.files():
            self.watcher.addPath(file_path)


class ScriptBrowserDialog(QDialog):
    """Enhanced script browser with output capture and error handling"""
    
    def __init__(self, scripts_info, execute_callback, parent=None):
        super().__init__(parent)
        self.scripts_info = scripts_info
        self.execute_callback = execute_callback
        self.current_script = None
        self.executor = SafeScriptExecutor()
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle(f"📋 {tr('script_browser')}")
        self.setModal(False)
        self.resize(900, 600)
        
        layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 5, 0, 5)
        
        title = QLabel(f"📚 {tr('available_scripts')}")
        title.setFont(QFont("", 11, QtCompat.get_font_weight_bold()))
        title.setStyleSheet("color: #2E86AB; margin: 0px; padding: 0px;")
        
        count_label = QLabel(f"({len(self.scripts_info)} {tr('scripts_found')})")
        count_label.setStyleSheet("color: #666; font-style: italic; margin: 0px; padding: 0px;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(count_label)
        header_layout.addStretch()
        
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setMaximumHeight(30)
        
        layout.addWidget(header_widget)
        
        splitter = QSplitter(QtCompat.get_horizontal())
        
        # Left panel - Script list
        list_widget = QWidget()
        list_layout = QVBoxLayout()
        
        list_label = QLabel(f"{tr('scripts')}:")
        list_label.setFont(QFont("", 9, QtCompat.get_font_weight_bold()))
        list_layout.addWidget(list_label)
        
        self.script_list = QListWidget()
        self.script_list.setMaximumWidth(280)
        
        for filename, script_info in sorted(self.scripts_info.items()):
            item = QListWidgetItem(f"📄 {script_info['name']}")
            item.setData(QtCompat.get_user_role(), (filename, script_info))
            self.script_list.addItem(item)
        
        self.script_list.currentItemChanged.connect(self.on_script_selected)
        list_layout.addWidget(self.script_list)
        list_widget.setLayout(list_layout)
        splitter.addWidget(list_widget)
        
        # Right panel - Script details with tabs
        details_widget = QWidget()
        details_layout = QVBoxLayout()
        
        self.script_name = QLabel(tr('select_script'))
        self.script_name.setFont(QFont("", 12, QtCompat.get_font_weight_bold()))
        self.script_name.setStyleSheet("color: #2E86AB; margin-bottom: 10px;")
        
        self.script_filename = QLabel("")
        self.script_filename.setStyleSheet("color: #666; font-size: 10px; margin-bottom: 5px;")
        
        details_layout.addWidget(self.script_name)
        details_layout.addWidget(self.script_filename)
        
        self.tab_widget = QTabWidget()
        
        # Description tab
        desc_tab = QWidget()
        desc_layout = QVBoxLayout()
        
        desc_label = QLabel(f"{tr('description')}:")
        desc_label.setFont(QFont("", 9, QtCompat.get_font_weight_bold()))
        
        self.script_description = QTextEdit()
        self.script_description.setReadOnly(True)
        self.script_description.setMaximumHeight(120)
        self.script_description.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
            }
        """)
        
        path_label = QLabel(f"{tr('location')}:")
        path_label.setFont(QFont("", 9, QtCompat.get_font_weight_bold()))
        
        self.script_path = QLabel("")
        self.script_path.setWordWrap(True)
        self.script_path.setStyleSheet("color: #666; font-size: 10px; font-family: monospace;")
        
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.script_description)
        desc_layout.addWidget(path_label)
        desc_layout.addWidget(self.script_path)
        desc_layout.addStretch()
        
        desc_tab.setLayout(desc_layout)
        self.tab_widget.addTab(desc_tab, f"📝 {tr('description')}")
        
        # Output tab
        output_tab = QWidget()
        output_layout = QVBoxLayout()
        
        output_controls = QHBoxLayout()
        
        clear_output_btn = QPushButton(f"🗑️ {tr('clear_output')}")
        clear_output_btn.clicked.connect(self.clear_output)
        clear_output_btn.setMaximumWidth(120)
        
        output_controls.addWidget(QLabel(f"{tr('console_output')}:"))
        output_controls.addStretch()
        output_controls.addWidget(clear_output_btn)
        
        output_layout.addLayout(output_controls)
        
        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 10px;
                border: 1px solid #555;
                border-radius: 4px;
            }
        """)
        self.output_text.setPlainText("Console output will appear here after script execution...")
        
        output_layout.addWidget(self.output_text)
        output_tab.setLayout(output_layout)
        self.tab_widget.addTab(output_tab, f"📺 {tr('output')}")
        
        details_layout.addWidget(self.tab_widget)
        
        self.run_button = QPushButton(f"▶️ {tr('execute_script')}")
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self.run_selected_script)
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        
        details_layout.addWidget(self.run_button)
        
        details_widget.setLayout(details_layout)
        splitter.addWidget(details_widget)
        
        splitter.setSizes([280, 620])
        layout.addWidget(splitter)
        
        # Bottom button panel
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton(f"🔄 {tr('refresh_list')}")
        refresh_btn.clicked.connect(self.refresh_scripts)
        
        open_folder_btn = QPushButton(f"📁 {tr('open_folder')}")
        open_folder_btn.clicked.connect(self.open_scripts_folder)
        
        close_btn = QPushButton(f"❌ {tr('close')}")
        close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(open_folder_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        if self.script_list.count() > 0:
            self.script_list.setCurrentRow(0)
    
    def on_script_selected(self, current, previous):
        if current:
            filename, script_info = current.data(QtCompat.get_user_role())
            self.script_name.setText(script_info['name'])
            self.script_filename.setText(f"{tr('file')}: {filename}")
            self.script_description.setText(script_info['description'])
            self.script_path.setText(script_info['path'])
            self.run_button.setEnabled(True)
            self.current_script = script_info
        else:
            self.script_name.setText(tr('no_script_selected'))
            self.script_filename.setText("")
            self.script_description.clear()
            self.script_path.setText("")
            self.run_button.setEnabled(False)
            self.current_script = None
    
    def run_selected_script(self):
        if not self.current_script:
            return
        
        self.tab_widget.setCurrentIndex(1)
        self.clear_output()
        
        self.append_output(f"🚀 Executing: {self.current_script['name']}")
        self.append_output(f"📁 Path: {self.current_script['path']}")
        self.append_output("=" * 60)
        
        try:
            success, output, errors, warnings = self.execute_callback(
                self.current_script['path'], 
                capture_output=True
            )
            
            if output:
                self.append_output("📤 Script Output:")
                self.append_output(output)
                self.append_output("-" * 40)
            
            if errors:
                self.append_output("❌ Script Errors:")
                self.append_output(errors, is_error=True)
                self.append_output("-" * 40)
            
            if warnings:
                self.append_output("⚠️ Validation Warnings:")
                for warning in warnings:
                    self.append_output(warning, is_warning=True)
                self.append_output("-" * 40)
            
            if success:
                if warnings:
                    self.append_output("✅ Script executed successfully with warnings!")
                    iface.messageBar().pushMessage(
                        tr('script_manager'), 
                        f"⚠️ {tr('script_executed_warnings')}: '{self.current_script['name']}'",
                        level=1, duration=3
                    )
                else:
                    self.append_output("✅ Script executed successfully!")
                    iface.messageBar().pushMessage(
                        tr('script_manager'), 
                        f"✅ {tr('script_executed').replace('!', '')} '{self.current_script['name']}'!",
                        level=3, duration=3
                    )
            else:
                self.append_output("❌ Script execution failed!")
                
        except Exception as e:
            self.append_output(f"💥 Critical Error: {str(e)}", is_error=True)
            QMessageBox.critical(
                self, tr('error'), f"{tr('error_executing')}:\n\n{str(e)}"
            )
    
    def append_output(self, text, is_error=False, is_warning=False):
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if is_error:
            formatted_text = f"[{timestamp}] ❌ {text}"
        elif is_warning:
            formatted_text = f"[{timestamp}] ⚠️  {text}"
        else:
            formatted_text = f"[{timestamp}] {text}"
        
        cursor.insertText(formatted_text + "\n")
        self.output_text.setTextCursor(cursor)
        
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        QApplication.processEvents()
    
    def clear_output(self):
        self.output_text.clear()
        self.append_output("Console ready for script execution...")
    
    def refresh_scripts(self):
        self.accept()
    
    def open_scripts_folder(self):
        import subprocess
        import platform
        
        try:
            scripts_dir = os.path.dirname(self.current_script['path']) if self.current_script else ""
            if scripts_dir and os.path.exists(scripts_dir):
                if platform.system() == "Windows":
                    os.startfile(scripts_dir)
                elif platform.system() == "Darwin":
                    subprocess.run(["open", scripts_dir])
                else:
                    subprocess.run(["xdg-open", scripts_dir])
        except Exception as e:
            QMessageBox.information(self, tr('open_scripts_folder'), f"{tr('error_opening_folder')}: {str(e)}")


def show_status_message(message, timeout=3000, is_warning=False):
    """Display a temporary message in the QGIS status bar"""
    try:
        status_bar = iface.mainWindow().statusBar()
        
        if is_warning:
            status_bar.setStyleSheet("QStatusBar { background-color: #FFF3CD; color: #856404; }")
        else:
            status_bar.setStyleSheet("QStatusBar { background-color: #D4EDDA; color: #155724; }")
        
        status_bar.showMessage(message, timeout)
        
        def restore_style():
            status_bar.setStyleSheet("")
        
        QTimer.singleShot(timeout, restore_style)
        
    except Exception:
        iface.messageBar().pushMessage(
            tr('script_manager'), message, 
            level=1 if is_warning else 0,
            duration=timeout // 1000
        )


class ScriptManager:
    """Script Manager plugin class for QGIS"""
    
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.scripts_dir = os.path.join(self.plugin_dir, 'scripts')
        
        if not os.path.exists(self.scripts_dir):
            os.makedirs(self.scripts_dir)
            self.create_example_script()
        
        self.menu = None
        self.actions = []
        self.scripts = {}
        self.browser_dialog = None
        self.executor = SafeScriptExecutor()
        
        self.watcher = ScriptWatcher(self.scripts_dir)
        self.watcher.scripts_changed.connect(self.reload_scripts)
        
        self.reload_timer = QTimer()
        self.reload_timer.setSingleShot(True)
        self.reload_timer.timeout.connect(self.update_menu)
        
        QgsMessageLog.logMessage(f"Script Manager initialized with Qt{QT_VERSION}", 
                                "Script Manager", Qgis.Info)
        
    def initGui(self):
        try:
            self.menu = QMenu(f"📋 {tr('script_manager')}", self.iface.mainWindow().menuBar())
            menubar = self.iface.mainWindow().menuBar()
            menubar.addMenu(self.menu)
            
            self.load_scripts()
            self.create_menu()
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Error initializing GUI: {str(e)}", 
                                   "Script Manager", Qgis.Critical)
            QMessageBox.critical(None, "Script Manager Error", 
                               f"Failed to initialize plugin GUI:\n{str(e)}")
    
    def unload(self):
        try:
            if self.browser_dialog:
                self.browser_dialog.close()
            if self.menu:
                self.menu.clear()
                self.iface.mainWindow().menuBar().removeAction(self.menu.menuAction())
            self.actions.clear()
            QgsMessageLog.logMessage("Script Manager unloaded successfully", 
                                   "Script Manager", Qgis.Info)
        except Exception as e:
            QgsMessageLog.logMessage(f"Error during unload: {str(e)}", 
                                   "Script Manager", Qgis.Warning)
    
    def create_example_script(self):
        lang = _translator.current_language
        
        qt_import_template = '''# -*- coding: utf-8 -*-
"""
Qt Compatibility Example for Script Manager
Demonstrates safe script writing with output capture
"""

try:
    from qgis.PyQt.QtWidgets import QMessageBox
    from qgis.PyQt.QtCore import Qt
    QT_VERSION = 6
    print(f"Using Qt6 via QGIS PyQt")
except ImportError:
    try:
        from PyQt6.QtWidgets import QMessageBox
        from PyQt6.QtCore import Qt
        QT_VERSION = 6
        print(f"Using Qt6 directly")
    except ImportError:
        from PyQt5.QtWidgets import QMessageBox
        from PyQt5.QtCore import Qt
        QT_VERSION = 5
        print(f"Using Qt5")

print(f"Qt Version: {QT_VERSION}")
'''
        
        if lang == 'pt_BR':
            example_script = qt_import_template + '''
"""
Script Exemplo PyQGIS
Descrição: Script exemplo que demonstra uso de print e informações das camadas
"""

from qgis.core import QgsProject
from qgis.utils import iface

def main():
    """Função principal do script"""
    print("🚀 Iniciando script exemplo...")
    
    project = QgsProject.instance()
    layers = project.mapLayers()
    layer_count = len(layers)
    
    print(f"📊 Analisando projeto: {project.baseName()}")
    print(f"📁 Número de camadas encontradas: {layer_count}")
    
    if layer_count == 0:
        message = "❌ Nenhuma camada carregada no projeto."
        print(message)
    else:
        print("📋 Lista de camadas:")
        layer_names = []
        for i, (layer_id, layer) in enumerate(layers.items(), 1):
            layer_name = layer.name()
            layer_type = "Vetor" if hasattr(layer, 'geometryType') else "Raster"
            print(f"  {i}. {layer_name} ({layer_type})")
            layer_names.append(f"{layer_name} ({layer_type})")
        
        message = f"✅ Camadas no projeto ({layer_count}):\\n" + "\\n".join(layer_names)
        print(f"📤 Exibindo resultado para o usuário...")
    
    QMessageBox.information(None, "Informações das Camadas", message)
    print("✅ Script executado com sucesso!")

if __name__ == "__main__":
    main()
'''
        else:
            example_script = qt_import_template + '''
"""
PyQGIS Example Script
Description: Example script demonstrating print usage and layer information
"""

from qgis.core import QgsProject
from qgis.utils import iface

def main():
    """Main script function"""
    print("🚀 Starting example script...")
    
    project = QgsProject.instance()
    layers = project.mapLayers()
    layer_count = len(layers)
    
    print(f"📊 Analyzing project: {project.baseName()}")
    print(f"📁 Number of layers found: {layer_count}")
    
    if layer_count == 0:
        message = "❌ No layers loaded in the project."
        print(message)
    else:
        print("📋 Layer list:")
        layer_names = []
        for i, (layer_id, layer) in enumerate(layers.items(), 1):
            layer_name = layer.name()
            layer_type = "Vector" if hasattr(layer, 'geometryType') else "Raster"
            print(f"  {i}. {layer_name} ({layer_type})")
            layer_names.append(f"{layer_name} ({layer_type})")
        
        message = f"✅ Layers in project ({layer_count}):\\n" + "\\n".join(layer_names)
        print(f"📤 Displaying result to user...")
    
    QMessageBox.information(None, "Layer Information", message)
    print("✅ Script executed successfully!")

if __name__ == "__main__":
    main()
'''
        
        example_path = os.path.join(self.scripts_dir, 'layers_example.py')
        with open(example_path, 'w', encoding='utf-8') as f:
            f.write(example_script)
    
    def load_scripts(self):
        self.scripts.clear()
        
        if not os.path.exists(self.scripts_dir):
            return
        
        loaded_count = 0
        error_count = 0
        
        for filename in os.listdir(self.scripts_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                script_path = os.path.join(self.scripts_dir, filename)
                try:
                    script_info = self.get_script_info(script_path)
                    if script_info:
                        self.scripts[filename] = script_info
                        self.watcher.add_file_to_watch(script_path)
                        loaded_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    error_count += 1
                    QgsMessageLog.logMessage(f"Error loading script {filename}: {str(e)}", 
                                           "Script Manager", Qgis.Warning)
        
        QgsMessageLog.logMessage(f"Loaded {loaded_count} scripts, {error_count} errors", 
                               "Script Manager", Qgis.Info)
    
    def get_script_info(self, script_path):
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            try:
                compile(content, script_path, 'exec')
            except SyntaxError as e:
                QgsMessageLog.logMessage(f"Syntax error in {script_path}: {str(e)}", 
                                       "Script Manager", Qgis.Warning)
                return None
            
            description = "PyQGIS Script"
            
            import re
            
            patterns = [
                r'"""[\s\S]*?Description:\s*([^\n]+)',
                r"'''[\s\S]*?Description:\s*([^\n]+)",
                r'Description:\s*(.+)',
                r'"""[\s\S]*?Descrição:\s*([^\n]+)',
                r"'''[\s\S]*?Descrição:\s*([^\n]+)",
                r'Descrição:\s*(.+)',
                r'"""[\s\S]*?Descripción:\s*([^\n]+)',
                r"'''[\s\S]*?Descripción:\s*([^\n]+)",
                r'Descripción:\s*(.+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    description = match.group(1).strip()
                    break
            
            description = description.replace('"', '').replace("'", "").strip()
            if not description:
                description = "PyQGIS Script"
            
            script_name = os.path.splitext(os.path.basename(script_path))[0]
            display_name = script_name.replace('_', ' ').title()
            
            return {
                'name': display_name,
                'path': script_path,
                'description': description,
                'content': content
            }
        
        except Exception as e:
            QgsMessageLog.logMessage(f"Error reading script {script_path}: {str(e)}", 
                                   "Script Manager", Qgis.Warning)
            return None
    
    def create_menu(self):
        if not self.menu:
            return
        
        try:
            self.menu.clear()
            self.actions.clear()
            
            browser_action = QAction(f"🔍 {tr('script_browser')}", self.iface.mainWindow())
            browser_action.setToolTip(tr('tooltip_browser'))
            browser_action.triggered.connect(self.open_script_browser)
            self.menu.addAction(browser_action)
            self.actions.append(browser_action)
            
            self.menu.addSeparator()
            
            if not self.scripts:
                no_scripts_action = QAction(f"❌ {tr('no_scripts_found')}", self.iface.mainWindow())
                no_scripts_action.setEnabled(False)
                self.menu.addAction(no_scripts_action)
                self.actions.append(no_scripts_action)
            else:
                quick_menu = self.menu.addMenu(f"⚡ {tr('quick_access')} ({len(self.scripts)} scripts)")
                
                for filename, script_info in sorted(self.scripts.items()):
                    action = QAction(script_info['name'], self.iface.mainWindow())
                    
                    action.hovered.connect(
                        lambda desc=script_info['description'], name=script_info['name']: 
                        show_status_message(f"💡 {name}: {desc}", 5000)
                    )
                    
                    action.triggered.connect(
                        lambda checked, path=script_info['path']: 
                        self.execute_script(path, capture_output=False)
                    )
                    
                    quick_menu.addAction(action)
                    self.actions.append(action)
                
                quick_menu.aboutToHide.connect(lambda: show_status_message("", 1))
            
            self.menu.addSeparator()
            
            reload_action = QAction(f"🔄 {tr('reload_scripts')}", self.iface.mainWindow())
            reload_action.setToolTip(tr('tooltip_reload'))
            reload_action.triggered.connect(self.reload_scripts)
            self.menu.addAction(reload_action)
            self.actions.append(reload_action)
            
            open_folder_action = QAction(f"📁 {tr('open_scripts_folder')}", self.iface.mainWindow())
            open_folder_action.setToolTip(tr('tooltip_folder'))
            open_folder_action.triggered.connect(self.open_scripts_folder)
            self.menu.addAction(open_folder_action)
            self.actions.append(open_folder_action)
            
            info_action = QAction(f"ℹ️ {tr('about')}", self.iface.mainWindow())
            info_action.setToolTip(tr('tooltip_about'))
            info_action.triggered.connect(self.show_info)
            self.menu.addAction(info_action)
            self.actions.append(info_action)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Error creating menu: {str(e)}", 
                                   "Script Manager", Qgis.Critical)
    
    def open_script_browser(self):
        try:
            if not self.scripts:
                show_status_message(f"⚠️ {tr('no_scripts_warning')}", 3000, True)
                return
            
            if self.browser_dialog:
                self.browser_dialog.close()
            
            self.browser_dialog = ScriptBrowserDialog(
                self.scripts, self.execute_script, self.iface.mainWindow()
            )
            self.browser_dialog.show()
            
            show_status_message(f"📚 {tr('browser_opened')} {len(self.scripts)} scripts", 2000)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Error opening script browser: {str(e)}", 
                                   "Script Manager", Qgis.Critical)
            QMessageBox.critical(None, "Error", f"Failed to open script browser:\n{str(e)}")
    
    def execute_script(self, script_path, capture_output=False):
        success = False
        captured_output = ""
        captured_errors = ""
        validation_warnings = []
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            validation_warnings = self.executor.validate_script_imports(script_content)
            
            if validation_warnings and not capture_output:
                warning_text = "\n".join(validation_warnings)
                reply = QMessageBox.question(
                    None, tr('validation_warnings'),
                    f"{tr('validation_warnings')}:\n\n{warning_text}\n\nContinue execution?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return False, "", "", validation_warnings
            
            script_globals = self.executor.prepare_safe_namespace(script_path)
            
            original_path = sys.path.copy()
            
            try:
                script_dir = os.path.dirname(script_path)
                if script_dir not in sys.path:
                    sys.path.insert(0, script_dir)
                
                if capture_output:
                    with self.executor.capture_output():
                        exec(script_content, script_globals)
                    captured_output, captured_errors = self.executor.get_captured_output()
                else:
                    exec(script_content, script_globals)
                
                success = True
                
                script_name = os.path.basename(script_path)
                if not capture_output:
                    show_status_message(f"✅ {tr('script_executed').replace('!', '')} '{script_name}'!", 3000)
                    
                QgsMessageLog.logMessage(f"✅ Script executed successfully: {script_name}", 
                                       "Script Manager", Qgis.Success)
                
                if captured_output.strip():
                    QgsMessageLog.logMessage(f"📤 {tr('output_captured')}:\n{captured_output}", 
                                           "Script Manager", Qgis.Info)
            
            finally:
                sys.path = original_path
        
        except Exception as e:
            script_name = os.path.basename(script_path)
            error_msg = f"❌ {tr('error_executing')} {script_name}: {str(e)}"
            detailed_error = f"{error_msg}\n\nDetails:\n{traceback.format_exc()}"
            
            captured_errors = detailed_error
            
            if not capture_output:
                show_status_message(f"❌ {tr('error')} '{script_name}'", 5000, True)
                QMessageBox.critical(None, tr('script_error'), 
                                   f"{tr('error_executing')} '{script_name}':\n\n{str(e)}\n\n{tr('check_log')}")
            
            QgsMessageLog.logMessage(detailed_error, "Script Manager", Qgis.Critical)
        
        if capture_output:
            return success, captured_output, captured_errors, validation_warnings
        else:
            return success
    
    def reload_scripts(self):
        self.reload_timer.start(500)
    
    def update_menu(self):
        try:
            self.load_scripts()
            self.create_menu()
            show_status_message(f"🔄 {tr('scripts_reloaded')} ({len(self.scripts)} scripts)", 2000)
            QgsMessageLog.logMessage("🔄 Scripts reloaded successfully", "Script Manager", Qgis.Info)
        except Exception as e:
            QgsMessageLog.logMessage(f"Error updating menu: {str(e)}", 
                                   "Script Manager", Qgis.Critical)
    
    def open_scripts_folder(self):
        import subprocess
        import platform
        
        try:
            if platform.system() == "Windows":
                os.startfile(self.scripts_dir)
            elif platform.system() == "Darwin":
                subprocess.run(["open", self.scripts_dir])
            else:
                subprocess.run(["xdg-open", self.scripts_dir])
                
        except Exception as e:
            QMessageBox.information(
                None, tr('open_scripts_folder'), 
                f"{tr('scripts_location')}:\n{self.scripts_dir}\n\n{tr('error_opening_folder')}: {str(e)}"
            )
    
    def show_info(self):
        lang = _translator.current_language
        
        info_text = f"""
<h3>📋 {tr('about_title')}</h3>
<p><b>{tr('about_subtitle')}</b></p>
<p>{tr('about_description')}</p>

<p><b>🎯 {tr('key_features')}:</b></p>
<ul>
<li><b>📚 {tr('script_browser')}:</b> {tr('feature_browser')}</li>
<li><b>⚡ {tr('quick_access')}:</b> {tr('feature_quick')}</li>
<li><b>🔄 Auto-monitoring:</b> {tr('feature_monitor')}</li>
<li><b>🔧 Easy Management:</b> {tr('feature_management')}</li>
<li><b>🖥️ Output Capture:</b> {tr('feature_output_capture')}</li>
<li><b>🛡️ Safe Execution:</b> {tr('feature_crash_prevention')}</li>
<li><b>⚠️ Script Validation:</b> {tr('feature_script_validation')}</li>
</ul>

<p><b>📁 {tr('scripts_location')}:</b><br>
<code>{self.scripts_dir}</code></p>
<p><b>📊 {tr('currently_loaded')}:</b> {len(self.scripts)} script(s)</p>

<p><b>🚀 {tr('getting_started')}:</b></p>
<ul>
<li>{tr('getting_started_1')}</li>
<li>{tr('getting_started_2')}</li>
<li>{tr('getting_started_3')}</li>
<li>{tr('getting_started_4')}</li>
<li>{tr('getting_started_5')}</li>
</ul>

<p><b>📝 {tr('script_format')}:</b></p>
<pre>
# -*- coding: utf-8 -*-
\"\"\"
My Custom Script
{'Descrição' if lang == 'pt_BR' else 'Description'}: This script does something useful
\"\"\"

from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsProject

def main():
    print("🚀 {'Iniciando script...' if lang == 'pt_BR' else 'Starting script...'}")
    
    project = QgsProject.instance()
    layer_count = len(project.mapLayers())
    
    QMessageBox.information(
        None, 
        "Script Info", 
        f"Project has {{layer_count}} layers"
    )
    
    print("✅ {'Concluído!' if lang == 'pt_BR' else 'Completed!'}")
        
if __name__ == "__main__":
    main()
</pre>
<p><i>For more information and examples, visit the plugin documentation.</i></p>
        """
    
        dialog = QDialog()
        dialog.setWindowTitle(tr('about'))
        dialog.resize(650, 550)
        dialog.setMinimumSize(650, 550)
        
        layout = QVBoxLayout()
        
        label = QLabel(info_text)
        label.setTextFormat(QtCompat.get_rich_text())
        label.setWordWrap(True)
        
        scroll = QScrollArea()
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)
        
        ok_button = QPushButton("OK")
        ok_button.setFixedSize(80, 30)
        ok_button.clicked.connect(dialog.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        
        layout.addWidget(scroll)
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        QtCompat.exec_dialog(dialog)


def classFactory(iface):
    """Return the ScriptManager class instance"""
    return ScriptManager(iface)