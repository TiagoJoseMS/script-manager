# -*- coding: utf-8 -*-
"""
Layer Statistics Tool
Description: Analyzes project layers and generates comprehensive statistics including feature counts, geometry types, and data summaries
"""

# Qt compatibility imports for PyQt5/PyQt6
try:
    from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QFont
    QT_VERSION = 6
except ImportError:
    from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QFont
    QT_VERSION = 5

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsRasterLayer, 
    QgsWkbTypes, QgsUnitTypes, QgsMessageLog, Qgis
)
from qgis.utils import iface
import time
from datetime import datetime


class LayerStatisticsDialog(QDialog):
    """Dialog to display layer statistics in a formatted window"""
    
    def __init__(self, statistics_text, parent=None):
        super().__init__(parent)
        self.statistics_text = statistics_text
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog user interface"""
        self.setWindowTitle("📊 Layer Statistics Report")
        self.setModal(False)
        self.resize(600, 500)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("📊 Project Layer Statistics")
        title_font = QFont()
        title_font.setPointSize(12)
        if QT_VERSION == 6:
            title_font.setWeight(QFont.Weight.Bold)
        else:
            title_font.setWeight(QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #2E86AB; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Statistics text area
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setPlainText(self.statistics_text)
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.text_area)
        
        # Close button
        close_btn = QPushButton("✅ Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
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
        """)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def exec_dialog(self):
        """Execute dialog with Qt version compatibility"""
        if QT_VERSION == 6:
            return self.exec()
        else:
            return self.exec_()


def get_geometry_type_name(geometry_type):
    """Get human-readable geometry type name"""
    geometry_types = {
        QgsWkbTypes.Point: "Point",
        QgsWkbTypes.LineString: "Line",
        QgsWkbTypes.Polygon: "Polygon",
        QgsWkbTypes.MultiPoint: "MultiPoint",
        QgsWkbTypes.MultiLineString: "MultiLine",
        QgsWkbTypes.MultiPolygon: "MultiPolygon",
        QgsWkbTypes.NoGeometry: "Table (No Geometry)",
        QgsWkbTypes.Unknown: "Unknown"
    }
    return geometry_types.get(geometry_type, f"Type {geometry_type}")


def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"


def analyze_vector_layer(layer):
    """Analyze a vector layer and return statistics"""
    stats = {
        'name': layer.name(),
        'type': 'Vector',
        'feature_count': layer.featureCount(),
        'geometry_type': get_geometry_type_name(layer.wkbType()),
        'crs': layer.crs().authid(),
        'crs_description': layer.crs().description(),
        'provider': layer.dataProvider().name(),
        'source': layer.source(),
        'fields_count': len(layer.fields()),
        'extent': layer.extent()
    }
    
    # Get field information
    fields_info = []
    for field in layer.fields():
        field_info = f"{field.name()} ({field.typeName()})"
        fields_info.append(field_info)
    stats['fields'] = fields_info
    
    return stats


def analyze_raster_layer(layer):
    """Analyze a raster layer and return statistics"""
    stats = {
        'name': layer.name(),
        'type': 'Raster',
        'band_count': layer.bandCount(),
        'width': layer.width(),
        'height': layer.height(),
        'crs': layer.crs().authid(),
        'crs_description': layer.crs().description(),
        'provider': layer.dataProvider().name(),
        'source': layer.source(),
        'extent': layer.extent()
    }
    
    return stats


def generate_statistics_report():
    """Generate comprehensive project statistics"""
    start_time = time.time()
    
    # Get all layers from project
    project = QgsProject.instance()
    layers = project.mapLayers()
    
    if not layers:
        return "❌ No layers found in the current project."
    
    # Initialize counters
    vector_layers = []
    raster_layers = []
    total_features = 0
    
    # Analyze each layer
    for layer_id, layer in layers.items():
        if isinstance(layer, QgsVectorLayer):
            layer_stats = analyze_vector_layer(layer)
            vector_layers.append(layer_stats)
            total_features += layer_stats['feature_count']
        elif isinstance(layer, QgsRasterLayer):
            layer_stats = analyze_raster_layer(layer)
            raster_layers.append(layer_stats)
    
    # Generate report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("📊 QGIS PROJECT LAYER STATISTICS REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Qt Version: {QT_VERSION}")
    report_lines.append(f"Project: {project.baseName() or 'Untitled Project'}")
    report_lines.append("")
    
    # Summary statistics
    report_lines.append("📋 SUMMARY")
    report_lines.append("-" * 40)
    report_lines.append(f"Total Layers: {len(layers)}")
    report_lines.append(f"Vector Layers: {len(vector_layers)}")
    report_lines.append(f"Raster Layers: {len(raster_layers)}")
    report_lines.append(f"Total Features: {total_features:,}")
    report_lines.append("")
    
    # Vector layers details
    if vector_layers:
        report_lines.append("🗺️ VECTOR LAYERS")
        report_lines.append("-" * 40)
        
        for i, layer_stats in enumerate(vector_layers, 1):
            report_lines.append(f"{i}. {layer_stats['name']}")
            report_lines.append(f"   Geometry: {layer_stats['geometry_type']}")
            report_lines.append(f"   Features: {layer_stats['feature_count']:,}")
            report_lines.append(f"   Fields: {layer_stats['fields_count']}")
            report_lines.append(f"   CRS: {layer_stats['crs']} ({layer_stats['crs_description']})")
            report_lines.append(f"   Provider: {layer_stats['provider']}")
            
            # Show field details for smaller field counts
            if layer_stats['fields_count'] <= 10:
                report_lines.append(f"   Field Details: {', '.join(layer_stats['fields'])}")
            else:
                report_lines.append(f"   Field Details: {layer_stats['fields_count']} fields (too many to display)")
            
            # Extent information
            extent = layer_stats['extent']
            report_lines.append(f"   Extent: X({extent.xMinimum():.2f}, {extent.xMaximum():.2f}) "
                              f"Y({extent.yMinimum():.2f}, {extent.yMaximum():.2f})")
            report_lines.append("")
    
    # Raster layers details
    if raster_layers:
        report_lines.append("🖼️ RASTER LAYERS")
        report_lines.append("-" * 40)
        
        for i, layer_stats in enumerate(raster_layers, 1):
            report_lines.append(f"{i}. {layer_stats['name']}")
            report_lines.append(f"   Dimensions: {layer_stats['width']} x {layer_stats['height']} pixels")
            report_lines.append(f"   Bands: {layer_stats['band_count']}")
            report_lines.append(f"   CRS: {layer_stats['crs']} ({layer_stats['crs_description']})")
            report_lines.append(f"   Provider: {layer_stats['provider']}")
            
            # Extent information
            extent = layer_stats['extent']
            report_lines.append(f"   Extent: X({extent.xMinimum():.2f}, {extent.xMaximum():.2f}) "
                              f"Y({extent.yMinimum():.2f}, {extent.yMaximum():.2f})")
            report_lines.append("")
    
    # Performance information
    processing_time = time.time() - start_time
    report_lines.append("⚡ PERFORMANCE")
    report_lines.append("-" * 40)
    report_lines.append(f"Analysis completed in: {processing_time:.3f} seconds")
    report_lines.append(f"Average processing per layer: {(processing_time/len(layers)):.3f} seconds")
    report_lines.append("")
    
    # Geometry type summary for vector layers
    if vector_layers:
        geometry_summary = {}
        for layer_stats in vector_layers:
            geom_type = layer_stats['geometry_type']
            if geom_type in geometry_summary:
                geometry_summary[geom_type] += 1
            else:
                geometry_summary[geom_type] = 1
        
        report_lines.append("📐 GEOMETRY TYPE SUMMARY")
        report_lines.append("-" * 40)
        for geom_type, count in geometry_summary.items():
            report_lines.append(f"{geom_type}: {count} layer(s)")
        report_lines.append("")
    
    report_lines.append("=" * 80)
    report_lines.append("Report completed successfully! 🎉")
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)


def main():
    """Main function to execute layer statistics analysis"""
    try:
        # Show initial message
        iface.messageBar().pushMessage(
            "Layer Statistics", 
            "🔄 Analyzing project layers...", 
            level=Qgis.Info, 
            duration=2
        )
        
        # Generate statistics
        statistics_report = generate_statistics_report()
        
        # Display results in a dialog
        dialog = LayerStatisticsDialog(statistics_report, iface.mainWindow())
        dialog.exec_dialog()
        
        # Log success
        QgsMessageLog.logMessage(
            "Layer statistics analysis completed successfully", 
            "Layer Statistics", 
            Qgis.Success
        )
        
        # Show completion message
        iface.messageBar().pushMessage(
            "Layer Statistics", 
            "✅ Analysis completed! Report displayed in dialog.", 
            level=Qgis.Success, 
            duration=2
        )
        
    except Exception as e:
        error_msg = f"❌ Error during layer analysis: {str(e)}"
        
        # Show error in message bar
        iface.messageBar().pushMessage(
            "Layer Statistics", 
            error_msg, 
            level=Qgis.Critical, 
            duration=5
        )
        
        # Log detailed error
        QgsMessageLog.logMessage(
            f"Layer Statistics Error: {str(e)}", 
            "Layer Statistics", 
            Qgis.Critical
        )
        
        # Show error dialog
        QMessageBox.critical(
            None, 
            "Layer Statistics Error", 
            f"An error occurred during analysis:\n\n{str(e)}\n\nCheck the QGIS message log for more details."
        )


# Execute main function when script is run
if __name__ == "__main__":
    main()