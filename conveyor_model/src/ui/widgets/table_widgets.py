from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QHBoxLayout, QHeaderView, QComboBox,
                             QSpinBox, QDoubleSpinBox, QItemDelegate, QGroupBox,
                             QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import List
from ...models.silo import Silo

class MaterialTable(QWidget):
    """Widget for managing materials"""
    
    materials_changed = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # Default materials
        self.default_materials = ["Lump Ore", "Sinter", "Pellet", "Dolomite", "Limestone","Nut Coke", "Quartz"]
        self.set_materials(self.default_materials)
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Group box
        group = QGroupBox("Materials")
        group_layout = QVBoxLayout()
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(['Material Name'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        group_layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("Add Material")
        add_button.clicked.connect(self.add_material)
        button_layout.addWidget(add_button)
        
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_material)
        button_layout.addWidget(remove_button)
        
        group_layout.addLayout(button_layout)
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        self.setLayout(layout)
    
    def add_material(self):
        """Add a new material row"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        item = QTableWidgetItem(f"Material_{row+1}")
        self.table.setItem(row, 0, item)
        self.emit_materials_changed()
    
    def remove_material(self):
        """Remove selected material"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)
            self.emit_materials_changed()
    
    def get_materials(self) -> List[str]:
        """Get list of material names"""
        materials = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text().strip():
                materials.append(item.text().strip())
        return materials
    
    def set_materials(self, materials: List[str]):
        """Set material list"""
        self.table.setRowCount(0)
        for material in materials:
            row = self.table.rowCount()
            self.table.insertRow(row)
            item = QTableWidgetItem(material)
            self.table.setItem(row, 0, item)
        self.emit_materials_changed()
    
    def clear(self):
        """Clear all materials"""
        self.table.setRowCount(0)
        self.emit_materials_changed()
    
    def emit_materials_changed(self):
        """Emit signal when materials change"""
        self.materials_changed.emit(self.get_materials())

class SiloTableDelegate(QItemDelegate):
    """Custom delegate for silo table editing"""
    
    def __init__(self, materials=None):
        super().__init__()
        self.materials = materials or []
    
    def createEditor(self, parent, option, index):
        column = index.column()
        
        if column == 0:  # Material dropdown
            combo = QComboBox(parent)
            combo.addItems(self.materials)
            return combo
        elif column == 1:  # Capacity
            spinbox = QDoubleSpinBox(parent)
            spinbox.setRange(1.0, 999999.0)
            spinbox.setSuffix(" kg")
            spinbox.setDecimals(2)
            return spinbox
        elif column == 2:  # Flow rate
            spinbox = QDoubleSpinBox(parent)
            spinbox.setRange(0.01, 1000.0)
            spinbox.setSuffix(" kg/s")
            spinbox.setDecimals(3)
            return spinbox
        elif column == 3:  # Material position
            spinbox = QSpinBox(parent)
            spinbox.setRange(0, max(len(self.materials)-1, 0))
            return spinbox
        elif column == 4:  # Silo position
            spinbox = QSpinBox(parent)
            spinbox.setRange(0, 1000)
            return spinbox
        elif column == 5:  # Start time
            spinbox = QDoubleSpinBox(parent)
            spinbox.setRange(0.0, 86400.0)
            spinbox.setSuffix(" s")
            spinbox.setDecimals(1)
            return spinbox
        
        return super().createEditor(parent, option, index)
    
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        
        if isinstance(editor, QComboBox):
            text = str(value) if value else ""
            idx = editor.findText(text)
            if idx >= 0:
                editor.setCurrentIndex(idx)
        elif isinstance(editor, QDoubleSpinBox):
            # Handle QDoubleSpinBox (accepts float values)
            try:
                editor.setValue(float(value) if value else 0.0)
            except (ValueError, TypeError):
                editor.setValue(0.0)
        elif isinstance(editor, QSpinBox):
            # Handle QSpinBox (accepts only integer values)
            try:
                editor.setValue(int(float(value)) if value else 0)
            except (ValueError, TypeError):
                editor.setValue(0)
        else:
            super().setEditorData(editor, index)
    
    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentText(), Qt.EditRole)
        elif isinstance(editor, (QSpinBox, QDoubleSpinBox)):
            model.setData(index, editor.value(), Qt.EditRole)
        else:
            super().setModelData(editor, model, index)
    
    def update_materials(self, materials):
        """Update available materials"""
        self.materials = materials

class SiloTable(QWidget):
    """Widget for managing silos"""
    
    def __init__(self):
        super().__init__()
        self.delegate = SiloTableDelegate()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Group box
        group = QGroupBox("Silos")
        group_layout = QVBoxLayout()
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        headers = ['Material', 'Capacity [kg]', 'Flow [kg/s]', 
                  'Material Position', 'Silo Position', 'Start Time [s]']
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setItemDelegate(self.delegate)
        group_layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("Add Silo")
        add_button.clicked.connect(self.add_silo)
        button_layout.addWidget(add_button)
        
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_silo)
        button_layout.addWidget(remove_button)
        
        group_layout.addLayout(button_layout)
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        self.setLayout(layout)
    
    def add_silo(self):
        """Add a new silo row"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Default values
        defaults = ['', '1000.0', '5.0', '0', '0', '0.0']
        for col, value in enumerate(defaults):
            item = QTableWidgetItem(value)
            self.table.setItem(row, col, item)
    
    def remove_silo(self):
        """Remove selected silo"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)
    
    def get_silos(self) -> List[Silo]:
        """Get list of configured silos"""
        silos = []
        for row in range(self.table.rowCount()):
            try:
                material = self.table.item(row, 0)
                material = material.text() if material else ""
                
                capacity = self.table.item(row, 1)
                capacity = float(capacity.text()) if capacity and capacity.text() else 0.0
                
                flow_rate = self.table.item(row, 2)
                flow_rate = float(flow_rate.text()) if flow_rate and flow_rate.text() else 0.0
                
                mat_pos = self.table.item(row, 3)
                mat_pos = int(mat_pos.text()) if mat_pos and mat_pos.text() else 0
                
                silo_pos = self.table.item(row, 4)
                silo_pos = int(silo_pos.text()) if silo_pos and silo_pos.text() else 0
                
                start_time = self.table.item(row, 5)
                start_time = float(start_time.text()) if start_time and start_time.text() else 0.0
                
                if material and capacity > 0 and flow_rate > 0:
                    silo = Silo(
                        material=material,
                        capacity=capacity,
                        flow_rate=flow_rate,
                        material_position=mat_pos,
                        silo_position=silo_pos,
                        start_time=start_time
                    )
                    silos.append(silo)
            except (ValueError, TypeError) as e:
                QMessageBox.warning(self, "Invalid Data", 
                                  f"Row {row+1} has invalid data: {str(e)}")
        
        return silos
    
    def set_silos(self, silo_data: List[dict]):
        """Set silo data from dictionary list"""
        self.table.setRowCount(0)
        for data in silo_data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            values = [
                data.get('material', ''),
                str(data.get('capacity', '0')),
                str(data.get('flow_rate', '0')),
                str(data.get('material_position', '0')),
                str(data.get('silo_position', '0')),
                str(data.get('start_time', '0'))
            ]
            
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                self.table.setItem(row, col, item)
    
    def clear(self):
        """Clear all silos"""
        self.table.setRowCount(0)
    
    def update_material_options(self, materials: List[str]):
        """Update available materials in dropdown"""
        self.delegate.update_materials(materials)
