# Script Manager for QGIS

PyQGIS script management plugin that offers an intuitive interface for organizing, monitoring, and executing custom Python scripts within the QGIS environment.

## 🎯 Overview

Script Manager transforms the way you work with PyQGIS scripts by providing:
- **Visual Script Browser** with detailed information and descriptions
- **Quick Access Menu** for rapid script execution
- **Automatic File Monitoring** that detects changes and reloads scripts
- **Multi-language Support** (English, Portuguese, Spanish)
- **Complete Qt5/Qt6 Compatibility** for future-proof operation

## ✨ Key Features

### 📚 Script Browser
- Interactive dialog with detailed script information
- Preview descriptions and file locations
- Execute scripts directly from the browser
- Refresh and folder management tools

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

### 🌍 Internationalization
- Multi-language interface support
- Automatic language detection from QGIS settings
- Supports English, Portuguese (Brazil), and Spanish
- Easy to extend for additional languages

### 🔧 Qt Compatibility
- Works seamlessly with both Qt5 and Qt6
- Automatic Qt version detection
- Compatible import handling
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
   - **macOS:** `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
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

```python
"""
Herramienta Personalizada  
Descripción: Este script realiza operaciones GIS personalizadas
"""
```

## 🎮 Usage

### Script Browser
1. Go to **Script Manager** → **Script Browser**
2. Browse through available scripts in the left panel
3. View detailed information in the right panel
4. Click **Execute Script** to run the selected script

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

### Qt Compatibility Layer
The plugin includes a comprehensive Qt compatibility system:
```python
class QtCompat:
    """Qt compatibility helper class"""
    
    @staticmethod
    def get_user_role():
        return Qt.ItemDataRole.UserRole if QT_VERSION == 6 else Qt.UserRole
    
    @staticmethod
    def exec_dialog(dialog):
        return dialog.exec() if QT_VERSION == 6 else dialog.exec_()
```

### File System Monitoring
- Uses `QFileSystemWatcher` for efficient monitoring
- Debounced reloading prevents excessive updates
- Monitors both directory changes and individual file modifications

## 🌍 Internationalization

### Supported Languages
- **English** (en)
- **Portuguese Brazil** (pt_BR) 
- **Spanish** (es_ES)

### Language Detection
The plugin automatically detects your QGIS interface language from settings and adjusts accordingly.

### Adding New Languages
To contribute translations:
1. Extend the `translations` dictionary in the `Translator` class
2. Add your language code and translated strings
3. Submit a pull request

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
- ✅ Multi-language support (EN, PT-BR, ES)
- ✅ Complete Qt5/Qt6 compatibility
- ✅ Professional user interface
- ✅ Comprehensive error handling
- ✅ Automatic script reloading
- ✅ Integrated help system

---

*For more information, bug reports, or feature requests, please visit the [GitHub repository](https://github.com/TiagoJoseMS/script-manager).*