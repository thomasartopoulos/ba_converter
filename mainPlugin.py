import os
from PyQt5.QtWidgets import QAction, QFileDialog, QDialog, QListWidget, QListWidgetItem, QLineEdit, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QCheckBox, QComboBox
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt
from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsVectorFileWriter, QgsCoordinateReferenceSystem
from qgis.PyQt import uic
from qgis.utils import iface
from qgis.gui import Qgis

class LayerConverter:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.action = QAction('Convert Layers to CABA-PG07', self.iface.mainWindow())
        self.action.triggered.connect(self.run)

    def initGui(self):
        self.iface.addPluginToMenu('BuenosAires Converter', self.action)

    def unload(self):
        self.iface.removePluginMenu('BuenosAires Converter', self.action)

    def run(self):
        dialog = LayerConverterDialog(self.iface, self.plugin_dir)
        dialog.exec_()

class LayerConverterDialog(QDialog):
    def __init__(self, iface, plugin_dir):
        super().__init__()
        self.iface = iface
        self.plugin_dir = plugin_dir
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("BuenosAires Converter")
        self.setGeometry(100, 100, 500, 400)  # Adjusted size to accommodate layout
        self.setWindowIcon(QIcon(os.path.join(self.plugin_dir, 'images/obelisco.png')))  # Set the window icon

        main_layout = QVBoxLayout()

        self.imageLabel = QLabel(self)
        pixmap = QPixmap(os.path.join(self.plugin_dir, 'images/carlos-gardel.jpeg'))
        self.imageLabel.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
        self.imageLabel.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.imageLabel)

        self.infoLabel = QLabel(self)
        self.infoLabel.setText("Convert your layers to Buenos Aires CRS settings.")
        self.infoLabel.setFont(QFont('Arial', 10))
        self.infoLabel.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.infoLabel)

        self.layerListWidget = QListWidget(self)
        self.layerListWidget.setSelectionMode(QListWidget.MultiSelection)
        main_layout.addWidget(self.layerListWidget)

        folder_layout = QHBoxLayout()
        self.outputFolderLineEdit = QLineEdit(self)
        self.selectFolderButton = QPushButton('Select Folder', self)
        self.selectFolderButton.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.outputFolderLineEdit)
        folder_layout.addWidget(self.selectFolderButton)
        main_layout.addLayout(folder_layout)

        # Adding the QComboBox for output format selection
        self.outputFormatComboBox = QComboBox(self)
        self.outputFormatComboBox.addItem("Shapefile")
        self.outputFormatComboBox.addItem("GeoPackage")
        main_layout.addWidget(self.outputFormatComboBox)

        self.showFileCheckBox = QCheckBox("Show file after converting", self)
        main_layout.addWidget(self.showFileCheckBox)

        self.convertButton = QPushButton('Convert', self)
        self.convertButton.clicked.connect(self.convert_layers)
        main_layout.addWidget(self.convertButton, alignment=Qt.AlignCenter)

        self.addCRSButton = QPushButton('Add Custom CRS', self)
        self.addCRSButton.clicked.connect(self.add_custom_crs)
        main_layout.addWidget(self.addCRSButton, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)

        self.populate_layers()

    def populate_layers(self):
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            item = QListWidgetItem(layer.name())
            item.setData(Qt.UserRole, layer)
            self.layerListWidget.addItem(item)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Output Folder')
        if folder:
            self.outputFolderLineEdit.setText(folder)

    def convert_layers(self):
        selected_items = self.layerListWidget.selectedItems()
        crs = QgsCoordinateReferenceSystem('PROJCS["CABA-PG07",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",20000.0],PARAMETER["False_Northing",70000.0],PARAMETER["Central_Meridian",-58.4633083333333],PARAMETER["Scale_Factor",1.0],PARAMETER["Latitude_Of_Origin",-34.6292666666667],UNIT["Meter",1.0]]')
        output_folder = self.outputFolderLineEdit.text()
        if not output_folder:
            self.iface.messageBar().pushMessage("Error", "No output folder selected.", level=Qgis.Critical)
            return

        if not selected_items:
            self.iface.messageBar().pushMessage("Error", "No layers selected.", level=Qgis.Critical)
            return

        selected_format = self.outputFormatComboBox.currentText()
        driver_name = {
            "Shapefile": "ESRI Shapefile",
            "GeoPackage": "GPKG"
        }.get(selected_format, "ESRI Shapefile")

        for item in selected_items:
            selected_layer = item.data(Qt.UserRole)
            if selected_layer and selected_layer.isValid():
                file_extension = {
                    "Shapefile": "shp",
                    "GeoPackage": "gpkg"
                }.get(selected_format, "shp")
                output_path = os.path.join(output_folder, f'{selected_layer.name()}_CABA-PG07.{file_extension}')
                result, error = QgsVectorFileWriter.writeAsVectorFormat(selected_layer, output_path, 'utf-8', crs, driverName=driver_name)
                if result == QgsVectorFileWriter.NoError:
                    self.iface.messageBar().pushMessage("Success", f"Layer '{selected_layer.name()}' converted successfully!", level=Qgis.Info)
                    if self.showFileCheckBox.isChecked():
                        iface.addVectorLayer(output_path, f'{selected_layer.name()}_CABA-PG07', 'ogr')
                else:
                    self.iface.messageBar().pushMessage("Error", f"Failed to convert layer: {error}", level=Qgis.Critical)
            else:
                self.iface.messageBar().pushMessage("Error", "No valid layer selected.", level=Qgis.Critical)

    def add_custom_crs(self):
        crs_string = 'PROJCS["CABA-PG07",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",20000.0],PARAMETER["False_Northing",70000.0],PARAMETER["Central_Meridian",-58.4633083333333],PARAMETER["Scale_Factor",1.0],PARAMETER["Latitude_Of_Origin",-34.6292666666667],UNIT["Meter",1.0]]'
        custom_crs = QgsCoordinateReferenceSystem()
        custom_crs.createFromWkt(crs_string)
        if not custom_crs.isValid():
            self.iface.messageBar().pushMessage("Error", "Failed to create custom CRS.", level=Qgis.Critical)
            return
    
        crs_id = custom_crs.saveAsUserCrs("CABA-PG07")
        if crs_id < 0:
            self.iface.messageBar().pushMessage("Error", "Failed to add custom CRS to the CRS database.", level=Qgis.Critical)
        else:
            self.iface.messageBar().pushMessage("Success", "CABA-PG07 added to the CRS database.", level=Qgis.Info)
