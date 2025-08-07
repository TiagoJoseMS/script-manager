# -*- coding: utf-8 -*-
"""
Script Manager Plugin for QGIS
Monitors and executes PyQGIS scripts automatically
Completely compatible with both Qt5 and Qt6
Author: Tiago José M Silva
"""

import os
import sys
import traceback
from pathlib import Path

# Use QGIS's built-in Qt handling for guaranteed compatibility
from qgis.PyQt.QtCore import QTimer, QFileSystemWatcher, pyqtSignal, QObject, QSettings, QT_VERSION_STR
from qgis.PyQt.QtWidgets import (QApplication, QAction, QMenu, QMessageBox, QDialog, QVBoxLayout, 
                                QHBoxLayout, QListWidget, QListWidgetItem, QLabel, 
                                QPushButton, QTextEdit, QSplitter, QWidget, QScrollArea)
from qgis.PyQt.QtGui import QIcon, QFont
from qgis.PyQt.QtCore import Qt

# Determine Qt version from QGIS environment
QT_VERSION = 6 if QT_VERSION_STR.startswith('6') else 5
print(f"Script Manager: Using Qt{QT_VERSION} (via QGIS PyQt)")

from qgis.core import QgsMessageLog, Qgis
from qgis.utils import iface


class QtCompat:
    """Qt compatibility helper class to handle differences between Qt5 and Qt6"""
    
    @staticmethod
    def get_user_role():
        """Get UserRole constant with Qt6 compatibility"""
        if QT_VERSION == 6:
            return Qt.ItemDataRole.UserRole
        else:
            return Qt.UserRole
    
    @staticmethod
    def get_horizontal():
        """Get Horizontal constant with Qt6 compatibility"""
        if QT_VERSION == 6:
            return Qt.Orientation.Horizontal
        else:
            return Qt.Horizontal
    
    @staticmethod
    def get_rich_text():
        """Get RichText constant with Qt6 compatibility"""
        if QT_VERSION == 6:
            return Qt.TextFormat.RichText
        else:
            return Qt.RichText
    
    @staticmethod
    def get_font_weight_bold():
        """Get QFont Bold weight constant"""
        if QT_VERSION == 6:
            return QFont.Weight.Bold
        else:
            return QFont.Bold
    
    @staticmethod
    def exec_dialog(dialog):
        """Execute dialog with correct method for Qt version"""
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
        """Detect QGIS interface language from settings"""
        try:
            settings = QSettings()
            locale = settings.value('locale/userLocale', 'en_US')
            
            # Extract language code (first 2 characters)
            language = locale[:2].lower()
            
            # Map some common variations
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
        """Load all translation dictionaries"""
        return {
            'en': {
                # Menu items
                'script_manager': 'Script Manager',
                'script_browser': 'Script Browser',
                'quick_access': 'Quick Access',
                'reload_scripts': 'Reload Scripts',
                'open_scripts_folder': 'Open Scripts Folder',
                'about': 'About',
                'no_scripts_found': 'No scripts found',
                
                # Dialog titles and labels
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
                
                # Status messages
                'script_executed': 'Script executed successfully!',
                'error_executing': 'Error executing script',
                'scripts_reloaded': 'Scripts reloaded',
                'browser_opened': 'Browser opened with',
                'no_scripts_warning': 'No scripts found in folder',
                'error_opening_folder': 'Error opening folder',
                
                # About dialog
                'about_title': 'Script Manager v1.0',
                'about_subtitle': 'PyQGIS Script Management Plugin',
                'about_description': 'The Script Manager plugin provides an intuitive interface for organizing and executing PyQGIS scripts within QGIS. It automatically monitors your scripts folder and provides multiple ways to browse and execute your custom tools.',
                'key_features': 'Key Features:',
                'feature_browser': 'Script Browser: Visual interface with detailed descriptions and script information',
                'feature_quick': 'Quick Access: Traditional menu with hover tooltips for fast script execution',
                'feature_monitor': 'Auto-monitoring: Automatically detects new scripts and file changes',
                'feature_management': 'Easy Management: Direct access to scripts folder and reload functionality',
                'scripts_location': 'Scripts Location:',
                'currently_loaded': 'Currently loaded:',
                'getting_started': 'Getting Started:',
                'getting_started_1': 'Place your .py files in the scripts folder above',
                'getting_started_2': 'Add a "Description:" line in your script\'s docstring for better organization',
                'getting_started_3': 'Use the Script Browser for detailed view or Quick Access for fast execution',
                'getting_started_4': 'Scripts are automatically reloaded when files change',
                'script_format': 'Script Format Example:',
                'qt_version_info': 'Qt Version:',
                
                # Error messages
                'error': 'Error',
                'script_error': 'Script Error',
                'check_log': 'Check QGIS log for more details.',
                
                # Tooltips
                'tooltip_browser': 'Open browser with detailed script descriptions',
                'tooltip_reload': 'Reload all scripts from folder',
                'tooltip_folder': 'Open the folder where scripts are stored',
                'tooltip_about': 'Information about Script Manager'
            },
            
            'pt_BR': {
                # Menu items
                'script_manager': 'Gerenciador de Scripts',
                'script_browser': 'Navegador de Scripts',
                'quick_access': 'Acesso Rápido',
                'reload_scripts': 'Recarregar Scripts',
                'open_scripts_folder': 'Abrir Pasta de Scripts',
                'about': 'Sobre',
                'no_scripts_found': 'Nenhum script encontrado',
                
                # Dialog titles and labels
                'available_scripts': 'Scripts Disponíveis',
                'scripts_found': 'scripts encontrados',
                'scripts': 'Scripts',
                'select_script': 'Selecione um script',
                'description': 'Descrição',
                'location': 'Localização',
                'file': 'Arquivo',
                'execute_script': 'Executar Script',
                'refresh_list': 'Atualizar Lista',
                'open_folder': 'Abrir Pasta',
                'close': 'Fechar',
                'no_script_selected': 'Nenhum script selecionado',
                
                # Status messages
                'script_executed': 'Script executado com sucesso!',
                'error_executing': 'Erro ao executar script',
                'scripts_reloaded': 'Scripts recarregados',
                'browser_opened': 'Navegador aberto com',
                'no_scripts_warning': 'Nenhum script encontrado na pasta',
                'error_opening_folder': 'Erro ao abrir pasta',
                
                # About dialog
                'about_title': 'Gerenciador de Scripts v1.0',
                'about_subtitle': 'Plugin de Gerenciamento de Scripts PyQGIS',
                'about_description': 'O plugin Gerenciador de Scripts fornece uma interface intuitiva para organizar e executar scripts PyQGIS dentro do QGIS. Ele monitora automaticamente sua pasta de scripts e oferece várias maneiras de navegar e executar suas ferramentas personalizadas.',
                'key_features': 'Principais Recursos',
                'feature_browser': 'Navegador de Scripts: Interface visual com descrições detalhadas e informações dos scripts',
                'feature_quick': 'Acesso Rápido: Menu tradicional com dicas ao passar o mouse para execução rápida',
                'feature_monitor': 'Monitoramento Automático: Detecta automaticamente novos scripts e mudanças nos arquivos',
                'feature_management': 'Gerenciamento Fácil: Acesso direto à pasta de scripts e funcionalidade de recarregamento',
                'scripts_location': 'Localização dos Scripts',
                'currently_loaded': 'Atualmente carregados',
                'getting_started': 'Começando',
                'getting_started_1': 'Coloque seus arquivos .py na pasta de scripts acima',
                'getting_started_2': 'Adicione uma linha "Description:" ("Descrição:") no docstring do seu script para melhor organização',
                'getting_started_3': 'Use o Navegador de Scripts para visualização detalhada ou Acesso Rápido para execução rápida',
                'getting_started_4': 'Os scripts são recarregados automaticamente quando os arquivos mudam',
                'script_format': 'Exemplo de Formato de Script',
                'qt_version_info': 'Versão Qt:',
                
                # Error messages
                'error': 'Erro',
                'script_error': 'Erro no Script',
                'check_log': 'Verifique o log do QGIS para mais detalhes',
                
                # Tooltips
                'tooltip_browser': 'Abrir navegador com descrições detalhadas dos scripts',
                'tooltip_reload': 'Recarregar todos os scripts da pasta',
                'tooltip_folder': 'Abrir a pasta onde os scripts são armazenados',
                'tooltip_about': 'Informações sobre o Gerenciador de Scripts'
            },
            
            'es_ES': {
                # Menu items
                'script_manager': 'Gestor de Scripts',
                'script_browser': 'Navegador de Scripts',
                'quick_access': 'Acceso Rápido',
                'reload_scripts': 'Recargar Scripts',
                'open_scripts_folder': 'Abrir Carpeta de Scripts',
                'about': 'Acerca de',
                'no_scripts_found': 'No se encontraron scripts',
                
                # Dialog titles and labels
                'available_scripts': 'Scripts Disponibles',
                'scripts_found': 'scripts encontrados',
                'scripts': 'Scripts',
                'select_script': 'Seleccionar un script',
                'description': 'Descripción',
                'location': 'Ubicación',
                'file': 'Archivo',
                'execute_script': 'Ejecutar Script',
                'refresh_list': 'Actualizar Lista',
                'open_folder': 'Abrir Carpeta',
                'close': 'Cerrar',
                'no_script_selected': 'Ningún script seleccionado',
                
                # Status messages
                'script_executed': '¡Script ejecutado con éxito!',
                'error_executing': 'Error al ejecutar script',
                'scripts_reloaded': 'Scripts recargados',
                'browser_opened': 'Navegador abierto con',
                'no_scripts_warning': 'No se encontraron scripts en la carpeta',
                'error_opening_folder': 'Error al abrir carpeta',
                
                # About dialog
                'about_title': 'Gestor de Scripts v1.0',
                'about_subtitle': 'Plugin de Gestión de Scripts PyQGIS',
                'about_description': 'El plugin Gestor de Scripts proporciona una interfaz intuitiva para organizar y ejecutar scripts PyQGIS dentro de QGIS. Monitorea automáticamente tu carpeta de scripts y ofrece múltiples formas de navegar y ejecutar tus herramientas personalizadas.',
                'key_features': 'Características Principales',
                'feature_browser': 'Navegador de Scripts: Interfaz visual con descripciones detalladas e información de scripts',
                'feature_quick': 'Acceso Rápido: Menú tradicional con tooltips al pasar el cursor para ejecución rápida',
                'feature_monitor': 'Monitoreo Automático: Detecta automáticamente nuevos scripts y cambios en archivos',
                'feature_management': 'Gestión Fácil: Acceso directo a la carpeta de scripts y funcionalidad de recarga',
                'scripts_location': 'Ubicación de Scripts',
                'currently_loaded': 'Actualmente cargados',
                'getting_started': 'Comenzando',
                'getting_started_1': 'Coloca tus archivos .py en la carpeta de scripts de arriba',
                'getting_started_2': 'Añade una línea "Description:" (o "Descripción:") en el docstring de tu script para mejor organización',
                'getting_started_3': 'Usa el Navegador de Scripts para vista detallada o Acceso Rápido para ejecución rápida',
                'getting_started_4': 'Los scripts se recargan automáticamente cuando los archivos cambian',
                'script_format': 'Ejemplo de Formato de Script',
                'qt_version_info': 'Versión Qt:',
                
                # Error messages
                'error': 'Error',
                'script_error': 'Error en Script',
                'check_log': 'Revisa el log de QGIS para más detalles',
                
                # Tooltips
                'tooltip_browser': 'Abrir navegador con descripciones detalladas de scripts',
                'tooltip_reload': 'Recargar todos los scripts de la carpeta',
                'tooltip_folder': 'Abrir la carpeta donde se almacenan los scripts',
                'tooltip_about': 'Información sobre el Gestor de Scripts'
            }
        }
    
    def tr(self, key, fallback=None):
        """Translate a key to the current language"""
        if fallback is None:
            fallback = key
        
        # Get translation for current language
        if self.current_language in self.translations:
            return self.translations[self.current_language].get(key, fallback)
        
        # Fallback to English
        if 'en' in self.translations:
            return self.translations['en'].get(key, fallback)
        
        # Ultimate fallback
        return fallback


# Global translator instance
_translator = Translator()

def tr(key, fallback=None):
    """Global translation function"""
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
        """Handle directory change events"""
        self.scripts_changed.emit()
    
    def on_file_changed(self, path):
        """Handle file modification events"""
        # Re-add file to watcher (required after modification)
        if os.path.exists(path) and path not in self.watcher.files():
            self.watcher.addPath(path)
        self.scripts_changed.emit()
    
    def add_file_to_watch(self, file_path):
        """Add a specific file to the file system watcher"""
        if os.path.exists(file_path) and file_path not in self.watcher.files():
            self.watcher.addPath(file_path)


class ScriptBrowserDialog(QDialog):
    """Interactive dialog for browsing and executing scripts with detailed information"""
    
    def __init__(self, scripts_info, execute_callback, parent=None):
        super().__init__(parent)
        self.scripts_info = scripts_info
        self.execute_callback = execute_callback
        self.current_script = None
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(f"📋 {tr('script_browser')}")
        self.setModal(False)  # Allow dialog to stay open
        self.resize(700, 500)
        
        layout = QVBoxLayout()
        
        # Header section
        header_layout = QHBoxLayout()
        title = QLabel(f"📚 {tr('available_scripts')}")
        title.setFont(QFont("", 12, QtCompat.get_font_weight_bold()))
        title.setStyleSheet("color: #2E86AB; margin-bottom: 10px;")
        
        count_label = QLabel(f"({len(self.scripts_info)} {tr('scripts_found')})")
        count_label.setStyleSheet("color: #666; font-style: italic;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(count_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Main content splitter
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
        
        # Right panel - Script details
        details_widget = QWidget()
        details_layout = QVBoxLayout()
        
        self.script_name = QLabel(tr('select_script'))
        self.script_name.setFont(QFont("", 12, QtCompat.get_font_weight_bold()))
        self.script_name.setStyleSheet("color: #2E86AB; margin-bottom: 10px;")
        
        self.script_filename = QLabel("")
        self.script_filename.setStyleSheet("color: #666; font-size: 10px; margin-bottom: 5px;")
        
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
        
        # Execute button
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
        
        details_layout.addWidget(self.script_name)
        details_layout.addWidget(self.script_filename)
        details_layout.addWidget(desc_label)
        details_layout.addWidget(self.script_description)
        details_layout.addWidget(path_label)
        details_layout.addWidget(self.script_path)
        details_layout.addWidget(self.run_button)
        details_layout.addStretch()
        
        details_widget.setLayout(details_layout)
        splitter.addWidget(details_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 400])
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
        
        # Select first item by default
        if self.script_list.count() > 0:
            self.script_list.setCurrentRow(0)
    
    def on_script_selected(self, current, previous):
        """Update details panel when a script is selected"""
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
        """Execute the currently selected script"""
        if self.current_script:
            try:
                self.execute_callback(self.current_script['path'])
                # Show success feedback
                iface.messageBar().pushMessage(
                    tr('script_manager'), 
                    f"✅ {tr('script_executed').replace('!', '')} '{self.current_script['name']}'!",
                    level=3, duration=3
                )
            except Exception as e:
                QMessageBox.critical(
                    self, tr('error'), f"{tr('error_executing')}:\n\n{str(e)}"
                )
    
    def refresh_scripts(self):
        """Refresh the scripts list by closing the dialog"""
        self.accept()  # Close dialog to force recreation
    
    def open_scripts_folder(self):
        """Open the scripts folder in the system file manager"""
        import subprocess
        import platform
        
        try:
            scripts_dir = os.path.dirname(self.current_script['path']) if self.current_script else ""
            if scripts_dir and os.path.exists(scripts_dir):
                if platform.system() == "Windows":
                    os.startfile(scripts_dir)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", scripts_dir])
                else:  # Linux
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
        # Fallback to message bar if status bar is unavailable
        iface.messageBar().pushMessage(
            tr('script_manager'), message, 
            level=1 if is_warning else 0,
            duration=timeout // 1000
        )


class ScriptManager:
    """Main Script Manager plugin class for QGIS"""
    
    def __init__(self, iface):
        """Initialize the plugin with QGIS interface reference"""
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.scripts_dir = os.path.join(self.plugin_dir, 'scripts')
        
        # Create scripts directory if it doesn't exist
        if not os.path.exists(self.scripts_dir):
            os.makedirs(self.scripts_dir)
            self.create_example_script()
        
        self.menu = None
        self.actions = []
        self.scripts = {}
        self.browser_dialog = None
        
        # Setup file system watcher for automatic script reloading
        self.watcher = ScriptWatcher(self.scripts_dir)
        self.watcher.scripts_changed.connect(self.reload_scripts)
        
        # Timer to prevent excessive reloads during rapid file changes
        self.reload_timer = QTimer()
        self.reload_timer.setSingleShot(True)
        self.reload_timer.timeout.connect(self.update_menu)
        
        # Log Qt version information for debugging
        QgsMessageLog.logMessage(f"Script Manager initialized with Qt{QT_VERSION}", 
                                "Script Manager", Qgis.Info)
        
    def initGui(self):
        """Initialize the plugin GUI components"""
        # Create main menu in QGIS menu bar
        self.menu = QMenu(f"📋 {tr('script_manager')}", self.iface.mainWindow().menuBar())
        menubar = self.iface.mainWindow().menuBar()
        menubar.addMenu(self.menu)
        
        # Load scripts and create menu structure
        self.load_scripts()
        self.create_menu()
    
    def unload(self):
        """Clean up plugin resources when unloading"""
        if self.browser_dialog:
            self.browser_dialog.close()
        if self.menu:
            self.menu.clear()
            self.iface.mainWindow().menuBar().removeAction(self.menu.menuAction())
        self.actions.clear()
    
    def create_example_script(self):
        """Create an example script in the detected language"""
        lang = _translator.current_language
        
        # Qt compatibility import template
        qt_import_template = '''# -*- coding: utf-8 -*-
"""
Qt Compatibility Import Example for Script Manager
Demonstrates how to write scripts compatible with both Qt5 and Qt6
"""

# Qt compatibility layer for PyQt5/PyQt6
try:
    from PyQt6.QtWidgets import QMessageBox
    from PyQt6.QtCore import Qt
    QT_VERSION = 6
except ImportError:
    from PyQt5.QtWidgets import QMessageBox
    from PyQt5.QtCore import Qt
    QT_VERSION = 5

print(f"Using Qt{QT_VERSION}")
'''
        
        if lang == 'pt_BR':
            example_script = qt_import_template + '''
"""
Script Exemplo PyQGIS
Descrição: Este é um script exemplo que mostra informações sobre as camadas ativas
"""

from qgis.core import QgsProject
from qgis.utils import iface

def main():
    """Main script function"""
    layers = QgsProject.instance().mapLayers()
    layer_count = len(layers)
    
    if layer_count == 0:
        message = "Nenhuma camada carregada no projeto."
    else:
        layer_names = [layer.name() for layer in layers.values()]
        message = f"Camadas no projeto ({layer_count}):\\n" + "\\n".join(layer_names)
    
    QMessageBox.information(None, "Informações das Camadas", message)

# Execute main function
if __name__ == "__main__":
    main()
'''
        elif lang == 'es_ES':
            example_script = qt_import_template + '''
"""
Script Ejemplo PyQGIS
Descripción: Este es un script ejemplo que muestra información sobre las capas activas
"""

from qgis.core import QgsProject
from qgis.utils import iface

def main():
    """Main script function"""
    layers = QgsProject.instance().mapLayers()
    layer_count = len(layers)
    
    if layer_count == 0:
        message = "No hay capas cargadas en el proyecto."
    else:
        layer_names = [layer.name() for layer in layers.values()]
        message = f"Capas en el proyecto ({layer_count}):\\n" + "\\n".join(layer_names)
    
    QMessageBox.information(None, "Información de Capas", message)

# Execute main function
if __name__ == "__main__":
    main()
'''
        else:  # Default to English
            example_script = qt_import_template + '''
"""
Example PyQGIS Script
Description: This is an example script that shows information about active layers
"""

from qgis.core import QgsProject
from qgis.utils import iface

def main():
    """Main script function"""
    layers = QgsProject.instance().mapLayers()
    layer_count = len(layers)
    
    if layer_count == 0:
        message = "No layers loaded in the project."
    else:
        layer_names = [layer.name() for layer in layers.values()]
        message = f"Layers in project ({layer_count}):\\n" + "\\n".join(layer_names)
    
    QMessageBox.information(None, "Layer Information", message)

# Execute main function
if __name__ == "__main__":
    main()
'''
        
        example_path = os.path.join(self.scripts_dir, 'example_layers.py')
        with open(example_path, 'w', encoding='utf-8') as f:
            f.write(example_script)
    
    def load_scripts(self):
        """Scan and load all Python scripts from the scripts folder"""
        self.scripts.clear()
        
        if not os.path.exists(self.scripts_dir):
            return
        
        for filename in os.listdir(self.scripts_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                script_path = os.path.join(self.scripts_dir, filename)
                script_info = self.get_script_info(script_path)
                if script_info:
                    self.scripts[filename] = script_info
                    # Add file to file system watcher
                    self.watcher.add_file_to_watch(script_path)
    
    def get_script_info(self, script_path):
        """Extract script metadata (name, description) supporting multiple languages"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Default description
            description = "PyQGIS Script"
            
            # Multi-language description patterns
            import re
            
            # Patterns for extracting description from docstrings
            patterns = [
                # English
                r'"""[\s\S]*?Description:\s*([^\n]+)',
                r"'''[\s\S]*?Description:\s*([^\n]+)",
                r'Description:\s*(.+)',
                # Portuguese
                r'"""[\s\S]*?Descrição:\s*([^\n]+)',
                r"'''[\s\S]*?Descrição:\s*([^\n]+)",
                r'Descrição:\s*(.+)',
                # Spanish
                r'"""[\s\S]*?Descripción:\s*([^\n]+)',
                r"'''[\s\S]*?Descripción:\s*([^\n]+)",
                r'Descripción:\s*(.+)',
                # French
                r'"""[\s\S]*?Description:\s*([^\n]+)',
                r"'''[\s\S]*?Description:\s*([^\n]+)",
                # German
                r'"""[\s\S]*?Beschreibung:\s*([^\n]+)',
                r"'''[\s\S]*?Beschreibung:\s*([^\n]+)",
                r'Beschreibung:\s*(.+)',
            ]
            
            # Try each pattern until a match is found
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    description = match.group(1).strip()
                    break
            
            # Clean description text
            description = description.replace('"', '').replace("'", "").strip()
            
            # Generate display name from filename
            script_name = os.path.splitext(os.path.basename(script_path))[0]
            display_name = script_name.replace('_', ' ').title()
            
            return {
                'name': display_name,
                'path': script_path,
                'description': description
            }
        
        except Exception as e:
            QgsMessageLog.logMessage(f"Error reading script {script_path}: {str(e)}", 
                                   "Script Manager", Qgis.Warning)
            return None
    
    def create_menu(self):
        """Create the plugin menu structure with actions and submenus"""
        if not self.menu:
            return
        
        # Clear existing menu items
        self.menu.clear()
        self.actions.clear()
        
        # Script Browser - main feature
        browser_action = QAction(f"🔍 {tr('script_browser')}", self.iface.mainWindow())
        browser_action.setToolTip(tr('tooltip_browser'))
        browser_action.triggered.connect(self.open_script_browser)
        self.menu.addAction(browser_action)
        self.actions.append(browser_action)
        
        self.menu.addSeparator()
        
        if not self.scripts:
            # Show "no scripts found" when folder is empty
            no_scripts_action = QAction(f"❌ {tr('no_scripts_found')}", self.iface.mainWindow())
            no_scripts_action.setEnabled(False)
            self.menu.addAction(no_scripts_action)
            self.actions.append(no_scripts_action)
        else:
            # Quick Access submenu with script list
            quick_menu = self.menu.addMenu(f"⚡ {tr('quick_access')} ({len(self.scripts)} scripts)")
            
            for filename, script_info in sorted(self.scripts.items()):
                action = QAction(script_info['name'], self.iface.mainWindow())
                
                # Show script description in status bar on hover
                action.hovered.connect(
                    lambda desc=script_info['description'], name=script_info['name']: 
                    show_status_message(f"💡 {name}: {desc}", 5000)
                )
                
                action.triggered.connect(lambda checked, path=script_info['path']: self.execute_script(path))
                
                quick_menu.addAction(action)
                self.actions.append(action)
            
            # Clear status bar when leaving submenu
            quick_menu.aboutToHide.connect(lambda: show_status_message("", 1))
        
        self.menu.addSeparator()
        
        # Utility actions
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
    
    def open_script_browser(self):
        """Open the interactive script browser dialog"""
        if not self.scripts:
            show_status_message(f"⚠️ {tr('no_scripts_warning')}", 3000, True)
            return
        
        # Close existing browser dialog
        if self.browser_dialog:
            self.browser_dialog.close()
        
        # Create and show new browser dialog
        self.browser_dialog = ScriptBrowserDialog(self.scripts, self.execute_script, self.iface.mainWindow())
        self.browser_dialog.show()
        
        show_status_message(f"📚 {tr('browser_opened')} {len(self.scripts)} scripts", 2000)
    
    def execute_script(self, script_path):
        """Execute a script with proper Qt compatibility and error handling"""
        try:
            # Save current Python path
            original_path = sys.path.copy()
            
            # Add script directory to Python path
            script_dir = os.path.dirname(script_path)
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
            
            # Read script content
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # Prepare script execution namespace
            script_globals = {
                '__name__': '__main__',
                '__file__': script_path,
                'iface': self.iface,
                'QT_VERSION': QT_VERSION,  # Make Qt version available to scripts
            }
            
            # Add common PyQGIS imports with Qt compatibility
            try:
                from qgis.core import (QgsProject, QgsVectorLayer, QgsRasterLayer, 
                                     QgsMessageLog, Qgis, QgsUnitTypes, QgsWkbTypes)
                from qgis.gui import QgsMapCanvas
                from qgis.utils import iface as qgis_iface
                
                # Import Qt widgets based on available version
                if QT_VERSION == 6:
                    from PyQt6.QtWidgets import QMessageBox, QInputDialog, QFileDialog
                    from PyQt6.QtCore import Qt, QTimer
                    from PyQt6.QtGui import QIcon
                else:
                    from PyQt5.QtWidgets import QMessageBox, QInputDialog, QFileDialog
                    from PyQt5.QtCore import Qt, QTimer
                    from PyQt5.QtGui import QIcon
                
                # Update script namespace with imports
                script_globals.update({
                    'QgsProject': QgsProject,
                    'QgsVectorLayer': QgsVectorLayer,
                    'QgsRasterLayer': QgsRasterLayer,
                    'QgsMessageLog': QgsMessageLog,
                    'QgsUnitTypes': QgsUnitTypes,
                    'QgsWkbTypes': QgsWkbTypes,
                    'QMessageBox': QMessageBox,
                    'QInputDialog': QInputDialog,
                    'QFileDialog': QFileDialog,
                    'iface': qgis_iface,
                    'Qt': Qt,
                    'QTimer': QTimer
                })
            except ImportError as e:
                QgsMessageLog.logMessage(f"Warning: Some imports may not be available: {str(e)}", 
                                       "Script Manager", Qgis.Warning)
            
            # Execute the script
            exec(script_content, script_globals)
            
            # Log successful execution
            script_name = os.path.basename(script_path)
            show_status_message(f"✅ {tr('script_executed').replace('!', '')} '{script_name}'!", 3000)
            QgsMessageLog.logMessage(f"✅ Script executed successfully: {script_name}", 
                                   "Script Manager", Qgis.Success)
        
        except Exception as e:
            # Handle script execution errors
            script_name = os.path.basename(script_path)
            error_msg = f"❌ {tr('error_executing')} {script_name}: {str(e)}"
            detailed_error = f"{error_msg}\n\nDetails:\n{traceback.format_exc()}"
            
            show_status_message(f"❌ {tr('error')} '{script_name}'", 5000, True)
            QgsMessageLog.logMessage(detailed_error, "Script Manager", Qgis.Critical)
            
            # Show user-friendly error dialog
            QMessageBox.critical(None, tr('script_error'), 
                               f"{tr('error_executing')} '{script_name}':\n\n{str(e)}\n\n{tr('check_log')}")
        
        finally:
            # Restore original Python path
            sys.path = original_path
    
    def reload_scripts(self):
        """Reload scripts with debouncing to prevent excessive updates"""
        self.reload_timer.start(500)  # 500ms delay for debouncing
    
    def update_menu(self):
        """Update menu after script reload operation"""
        self.load_scripts()
        self.create_menu()
        show_status_message(f"🔄 {tr('scripts_reloaded')} ({len(self.scripts)} scripts)", 2000)
        QgsMessageLog.logMessage("🔄 Scripts reloaded", "Script Manager", Qgis.Info)
    
    def open_scripts_folder(self):
        """Open the scripts folder in the system file manager"""
        import subprocess
        import platform
        
        try:
            if platform.system() == "Windows":
                os.startfile(self.scripts_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", self.scripts_dir])
            else:  # Linux and other Unix-like systems
                subprocess.run(["xdg-open", self.scripts_dir])
        except Exception as e:
            QMessageBox.information(None, tr('open_scripts_folder'), 
                                  f"{tr('scripts_location')}:\n{self.scripts_dir}\n\n{tr('error_opening_folder')}: {str(e)}")
    
    def show_info(self):
        """Display plugin information and usage instructions"""
        qt_info = f"Qt{QT_VERSION}"
        info_text = f"""
    <h3>📋 {tr('about_title')}</h3>
    <p><b>{tr('about_subtitle')}</b></p>
    <p>{tr('about_description')}</p>
    <p><b>🎯 {tr('key_features')}:</b></p>
    <ul>
    <li><b>📚 {tr('script_browser')}:</b> {tr('feature_browser')}</li>
    <li><b>⚡ {tr('quick_access')}:</b> {tr('feature_quick')}</li>
    <li><b>🔄 {tr('feature_monitor')}</b></li>
    <li><b>🔧 {tr('feature_management')}</b></li>
    </ul>
    <p><b>📁 {tr('scripts_location')}:</b><br>
    <code>{self.scripts_dir}</code></p>
    <p><b>📊 {tr('currently_loaded')}:</b> {len(self.scripts)} script(s)</p>
    <p><b>⚙️ {tr('qt_version_info')}:</b> {qt_info}</p>
    <p><b>🚀 {tr('getting_started')}:</b></p>
    <ul>
    <li>{tr('getting_started_1')}</li>
    <li>{tr('getting_started_2')}</li>
    <li>{tr('getting_started_3')}</li>
    <li>{tr('getting_started_4')}</li>
    </ul>
    <p><b>📝 {tr('script_format')}:</b></p>
    <pre>
    # -*- coding: utf-8 -*-
    \"\"\"
    My Custom Script
    Description: This script does something useful
    \"\"\"
    
    # Qt compatibility imports
    try:
        from PyQt6.QtWidgets import QMessageBox
        QT_VERSION = 6
    except ImportError:
        from PyQt5.QtWidgets import QMessageBox
        QT_VERSION = 5
    
    def main():
        # Your code here
        QMessageBox.information(None, "Hello", f"Running on Qt{{QT_VERSION}}")
        
    if __name__ == "__main__":
        main()
    </pre>
    <p><i>For more information and examples, visit the plugin documentation.</i></p>
        """
    
        dialog = QDialog()
        dialog.setWindowTitle(tr('about'))
        dialog.resize(400, 300)
        dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout()
        
        # Content label with rich text
        label = QLabel(info_text)
        label.setTextFormat(QtCompat.get_rich_text())
        label.setWordWrap(True)
        
        # Scrollable area for content
        scroll = QScrollArea()
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)
        
        # OK button
        ok_button = QPushButton("OK")
        ok_button.setFixedSize(80, 30)
        ok_button.clicked.connect(dialog.accept)
        
        # Center the OK button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        
        layout.addWidget(scroll)
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        # Execute dialog using compatibility method
        QtCompat.exec_dialog(dialog)


# QGIS Plugin entry point
def classFactory(iface):
    """Return the ScriptManager class instance for QGIS plugin system"""
    return ScriptManager(iface)