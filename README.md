# Script Manager for QGIS

PyQGIS script management plugin that offers an intuitive interface for organizing, monitoring, and executing custom Python scripts within the QGIS environment.

## 🎯 Overview

Script Manager transforms the way you work with PyQGIS scripts by providing:
- **Visual Script Browser** with detailed information and descriptions
- **Quick Access Menu** for rapid script execution
- **Automatic File Monitoring** that detects changes and reloads scripts
- **Enhanced Security and Error Handling** for safe script execution
- **Multi-language Support** (English, Portuguese)
- **Complete Qt5/Qt6 Compatibility** for future-proof operation

## ✨ Key Features

### 📚 Script Browser
- Interactive dialog with detailed script information
- Preview descriptions and file locations
- Execute scripts directly from the browser
- Refresh and folder management tools
- **Console Output Capture**: Displays `print()` statements and error messages from executed scripts
- **Detailed Error Reporting**: Provides clear error messages and traceback for debugging

### ⚡ Quick Access Menu
- Traditional menu structure for fast execution
- Hover tooltips showing script descriptions
- Organized by script categories
- Status bar integration

### 🔄 Automatic Monitoring
- Real-time detection of new scripts
- Automatic reloading when files change
- No manual refresh required
- Efficient file system watching

### 🔒 Safe Script Execution
- **Script Validation**: Performs pre-execution checks to identify potentially risky operations (e.g., `subprocess.call`, `subprocess.run`, `subprocess.Popen`, `os.system`, `eval(`, `exec(`, `__import__`)
- **Isolated Execution Environment**: Scripts run in a controlled namespace with pre-defined QGIS and PyQt imports to prevent unintended side effects and ensure access to necessary modules
- **Crash Prevention**: Robust error handling mechanisms prevent script errors from crashing QGIS, providing a stable environment

### 🌍 Internationalization
- Multi-language interface support
- Automatic language detection from QGIS settings
- **Currently supports**: English (en) and Portuguese Brazil (pt_BR)
- Easy to extend for additional languages by modifying the `Translator` class

### 🔧 Qt Compatibility
- Works seamlessly with both Qt5 and Qt6
- Automatic Qt version detection
- Compatible import handling for various Qt modules (e.g., `QMessageBox`, `QInputDialog`, `QFileDialog`, `QProgressBar`, `QComboBox`, `QCheckBox`)
- Handles differences in Qt API calls:
  - `Qt.UserRole` vs `Qt.ItemDataRole.UserRole`
  - `dialog.exec_()` vs `dialog.exec()`
  - `Qt.RichText` vs `Qt.TextFormat.RichText`
  - `QFont.Bold` vs `QFont.Weight.Bold`
  - `Qt.Horizontal` vs `Qt.Orientation.Horizontal`
- Future-proof architecture

## 🚀 Installation

### From QGIS Plugin Repository (Recommended)
1. Open QGIS
2. Go to **Plugins** → **Manage and Install Plugins**
3. Search for "Script Manager"
4. Click **Install Plugin**

### Manual Installation
1. Download the plugin zip file
2. Extract to your QGIS plugins directory:
   - **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **macOS:** `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins\`
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins\`
3. Restart QGIS
4. Enable the plugin in **Plugins** → **Manage and Install Plugins** → **Installed**

## 📝 Getting Started

### 1. Initial Setup
After installation, the plugin automatically creates a `scripts` folder within the plugin directory and adds an example script to help you get started.

### 2. Adding Your Scripts
1. Access the **Script Manager** menu in QGIS
2. Click **"Open Scripts Folder"** to open the scripts directory
3. Copy your `.py` files into this folder
4. Scripts are automatically detected and loaded

### 3. Script Format
For best results, format your scripts with proper metadata:

```python
# -*- coding: utf-8 -*-
"""
My Custom Tool
Description: This script performs custom GIS operations
"""

# Qt compatibility imports (recommended)
try:
    from PyQt6.QtWidgets import QMessageBox
    QT_VERSION = 6
except ImportError:
    from PyQt5.QtWidgets import QMessageBox
    QT_VERSION = 5

from qgis.core import QgsProject
from qgis.utils import iface

def main():
    """Main script function"""
    layers = QgsProject.instance().mapLayers()
    message = f"Project has {len(layers)} layers (Qt{QT_VERSION})"
    QMessageBox.information(None, "Layer Count", message)

if __name__ == "__main__":
    main()
```

### 4. Multi-language Descriptions
The plugin supports descriptions in multiple languages:

```python
"""
Ferramenta Personalizada
Descrição: Este script realiza operações GIS personalizadas
"""
```

## 🎮 Usage

### Script Browser
1. Go to **Script Manager** → **Script Browser**
2. Browse through available scripts in the left panel
3. View detailed information in the right panel
4. Click **Execute Script** to run the selected script
5. **Monitor Output**: Check the console output and warnings sections for script execution results

### Quick Access
1. Navigate to **Script Manager** → **Quick Access**
2. Hover over script names to see descriptions
3. Click any script name to execute immediately

### Management Tools
- **Reload Scripts**: Manually refresh the script list
- **Open Scripts Folder**: Quick access to the scripts directory
- **About**: View plugin information and usage instructions

## ⚙️ Configuration

### Scripts Directory
The plugin stores scripts in: `[plugin_directory]/scripts/`

You can access this location through:
- **Script Manager** → **Open Scripts Folder**
- The About dialog shows the exact path

### Automatic Reloading
- Scripts are monitored for changes automatically
- New files are detected when added to the folder
- Modified scripts are reloaded immediately
- No configuration required

## 🔧 Technical Details

### System Requirements
- **QGIS:** 3.0 or higher
- **Python:** 3.6+
- **Qt:** Version 5.x or 6.x (auto-detected)
- **Operating System:** Windows, macOS, Linux

### Safe Script Execution Environment
The plugin executes scripts within a controlled environment using the `SafeScriptExecutor` class, which:
- Captures `stdout` and `stderr` to prevent direct console interference
- Performs security checks for potentially dangerous imports
- Provides a safe namespace with pre-loaded QGIS and PyQt modules including:
  - **QGIS Core**: `QgsProject`, `QgsVectorLayer`, `QgsRasterLayer`, `QgsFeature`, `QgsGeometry`, `QgsCoordinateReferenceSystem`, `QgsCoordinateTransform`, `QgsMessageLog`, `QgsUnitTypes`, `QgsWkbTypes`, `QgsMapLayerProxyModel`, `QgsProcessingContext`
  - **QGIS GUI**: `QgsMapCanvas`, `QgsMapTool`
  - **PyQt Widgets**: `QMessageBox`, `QInputDialog`, `QFileDialog`, `QProgressBar`, `QComboBox`, `QCheckBox`
  - **PyQt Core**: `Qt`, `QTimer`, `QThread`, `pyqtSignal`
  - **PyQt GUI**: `QIcon`, `QPixmap`, `QColor`
  - **Standard Libraries**: `json`, `math`, `datetime`, `re`

### Qt Compatibility Layer
The plugin includes a comprehensive `QtCompat` class to handle differences between Qt5 and Qt6 APIs, ensuring broad compatibility. This includes adapting methods for:
- User roles (`Qt.UserRole` vs `Qt.ItemDataRole.UserRole`)
- Dialog execution (`dialog.exec_()` vs `dialog.exec()`)
- Text formats (`Qt.RichText` vs `Qt.TextFormat.RichText`)
- Font weights (`QFont.Bold` vs `QFont.Weight.Bold`)
- Orientations (`Qt.Horizontal` vs `Qt.Orientation.Horizontal`)

### File System Monitoring
- Uses `QFileSystemWatcher` for efficient monitoring of the scripts directory
- Debounced reloading prevents excessive updates when multiple changes occur rapidly
- Monitors both directory changes and individual file modifications to ensure scripts are always up-to-date

## 🌍 Internationalization

### Supported Languages
- **English** (en)
- **Portuguese Brazil** (pt_BR)

### Language Detection
The plugin automatically detects your QGIS interface language from settings and adjusts accordingly. The detection system maps language codes as follows:
- `pt` → `pt_BR`
- Other languages fall back to English

### Adding New Languages
To contribute translations:
1. Extend the `translations` dictionary in the `Translator` class within `script_manager.py`
2. Add your language code and translated strings
3. Update the `language_map` in the `detect_qgis_language` method if needed
4. Submit a pull request

## 🐛 Troubleshooting

### Common Issues

**Scripts not appearing in menu:**
- Check that files have `.py` extension
- Ensure files are in the correct scripts folder
- Try **Reload Scripts** from the menu

**Qt version errors:**
- The plugin auto-detects Qt version
- Check QGIS log for Qt compatibility messages
- Most scripts should work with both Qt5 and Qt6

**Script execution errors:**
- Check the QGIS message log for detailed error information
- Ensure your script has proper imports
- Verify file permissions and encoding (UTF-8 recommended)
- **Review Console Output**: The Script Browser's output panel will show `print()` statements and error messages from your script, which can help in debugging
- **Validation Warnings**: Pay attention to any warnings about potentially risky operations detected during script validation

### Debug Information
Enable debug logging by checking the QGIS message log:
1. **View** → **Panels** → **Log Messages**
2. Look for "Script Manager" entries
3. Set log level to "Info" for detailed output

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with appropriate tests
4. Update documentation as needed
5. Submit a pull request

### Development Setup
```bash
git clone https://github.com/TiagoJoseMS/script-manager.git
cd script-manager
# Link to QGIS plugins directory for testing
```

## 📄 License

This plugin is licensed under the GNU General Public License v2.0. See the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Tiago José M. Silva**
- Email: tiago.moraessilva@hotmail.com
- GitHub: [@TiagoJoseMS](https://github.com/TiagoJoseMS)

## 🙏 Acknowledgments

- QGIS Development Team for the excellent GIS platform
- PyQt/Qt developers for the robust GUI framework
- The QGIS community for feedback and support

## 📈 Changelog

### Version 1.0 (Initial Release)
- ✅ Script browser with detailed information
- ✅ Quick access menu system
- ✅ Automatic file system monitoring
- ✅ Multi-language support (EN, PT-BR)
- ✅ Complete Qt5/Qt6 compatibility
- ✅ Professional user interface
- ✅ Comprehensive error handling
- ✅ Automatic script reloading
- ✅ Integrated help system
- ✅ Safe script execution environment
- ✅ Console output capture

---
