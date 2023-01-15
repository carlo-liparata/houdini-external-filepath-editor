
import os
import hou
import glob

from PySide2 import QtGui,QtCore,QtWidgets
from PySide2.QtCore import Qt, QSize
from PySide2.QtGui import QPalette, QBrush, QColor
from PySide2.QtWidgets import *



allowedFileExtensions = [".abc", ".obj", ".fbx", ".usd", ".usdc", ".usda", ".sc", ".bgeo", ".ass", ".sim", ".vdb", ".jpeg", ".jpg", ".exr", ".tx", ".bmp", ".png", ".tif", ".tiff", ".tga", ".hdr"]

geometryFileExtensions = [".abc", ".obj", ".fbx", ".usd", ".usdc", ".usda", ".sc", ".bgeo", ".ass", ".sim", ".vdb"]
imageFileExtensions = [".jpeg", ".jpg", ".exr", ".tx", ".bmp", ".png", ".tif", ".tiff", ".tga", ".hdr"]

nodesBlacklist = ["alembic", "alembicxform"]


##################### UI

class myMainUi(QtWidgets.QMainWindow):
    

    def __init__(self, parent=None):     
        
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setMinimumSize(600, 400)
        self.setWindowTitle("File Path Editor")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)        
        
        self.geometryFileExtensions = [".abc", ".obj", ".fbx", ".usd", ".usdc", ".usda", ".sc", ".bgeo", ".ass", ".sim", ".vdb"]
        self.imageFileExtensions = [".jpeg", ".jpg", ".exr", ".tx", ".bmp", ".png", ".tif", ".tiff", ".tga", ".hdr"]
        
        self.allowedFileExtensions = self.geometryFileExtensions + self.imageFileExtensions
        
        
        self.fileList = []
        self.errorText = ""
        self.existenceList = []
        self.numErr = None
        self.fileErr = None
        self.parmList = []
        self.numberOfErrors = 0
        self.filePathErrors = []
        self.nodeFileParm = []
        self.nodesList = []
        self.nodeFileDict = None
        
        
        self.getFileandParmLists()
        
               
        ## LIST WIDGET ##
        
        self.listWidget = QListWidget(self)
        self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.listWidget.move(50, 50)
        
        
        for index, filepath in enumerate(self.fileList):
            myItem = QtWidgets.QListWidgetItem(filepath)
                        
            if self.checkSingleFileExists(filepath) == True:
                myItem.setCheckState(QtCore.Qt.Checked)
                myItem.setForeground(QBrush(Qt.white))                
                
            if self.checkSingleFileExists(filepath) == False:
                myItem.setCheckState(QtCore.Qt.Unchecked)            
                myItem.setForeground(QBrush(Qt.darkRed))
                
            self.listWidget.addItem(myItem)
                    
        self.listWidget.resize(440, 500)

        
        ## FILE EXTENSION FILTER ##
        
        self.geoCheckBox = QCheckBox("Show Geometry Files", self)
        self.geoCheckBox.move(10, 10)
        self.geoCheckBox.resize(500, 30)        
        self.geoCheckBox.setChecked(True)
        self.geoCheckBox.setStyleSheet("font-size: 14pt")        
        self.geoCheckBox.stateChanged.connect(self.refresh)  
        
        self.imageCheckBox = QCheckBox("Show Image Files", self)
        self.imageCheckBox.move(10, 10)
        self.imageCheckBox.resize(500, 30)
        self.imageCheckBox.setChecked(True)
        self.imageCheckBox.setStyleSheet("font-size: 14pt")        
        self.imageCheckBox.stateChanged.connect(self.refresh)          
        
        
        ## INFO BOX LABEL ##
        
        self.infoBox = QLabel(self.errorText, self)
        self.infoBox.resize(400, 100)
        self.infoBox.move(500, 50)
        
        
        ## REFRESH BUTTON ##
        
        self.refreshButton = QPushButton("Refresh", self)
        self.refreshButton.move(50, 600)
        self.refreshButton.resize(100,50)
        self.refreshButton.clicked.connect(self.refresh)
        
        
        ## SELECT ALL ##
        
        self.selectAllButton = QPushButton("Select All", self)
        self.selectAllButton.move(50, 10)
        self.selectAllButton.clicked.connect(self.selectAll)
        
        
        ## CLEAR SELECTION ##
        
        self.clearAllButton = QPushButton("Clear All", self)
        self.clearAllButton.move(160, 10)
        self.clearAllButton.clicked.connect(self.clearAll)
        
        
        ## SELECT BY NAME ##
        
        self.selectByNameButton = QPushButton("Select by name", self)
        self.selectByNameButton.move(270, 10)
        self.selectByNameButton.clicked.connect(self.selectByName)
        self.selectByNameDialog = selectByNameWindow(self)     

        
        
        ## REPLACE ##

        self.replaceButton = QPushButton("Replace Selected", self)
        self.replaceButton.move(175, 600)
        self.replaceButton.resize(150,50)
        self.replaceButton.clicked.connect(self.replaceInPath)        
        self.replaceDialogWindow = replaceWindow(self)        
        
        
        ## GO TO SELECTED NODE ##
        
        self.goToNodeButton = QPushButton("Go To Node", self)
        self.goToNodeButton.move(350, 600)
        self.goToNodeButton.resize(150, 50)
        self.goToNodeButton.clicked.connect(self.centerViewOnSelectedNode)
                           
        self.refresh()
    
        self.getNodes()
            
        gridLay = QGridLayout()
        gridLay.addWidget(self.geoCheckBox, 0, 1)
        gridLay.addWidget(self.imageCheckBox, 0, 2)
        gridLay.addWidget(self.listWidget, 2, 0)
        gridLay.addWidget(self.selectAllButton, 1, 0)        
        gridLay.addWidget(self.clearAllButton, 1, 1)        
        gridLay.addWidget(self.selectByNameButton, 1, 2)
        gridLay.addWidget(self.refreshButton, 3, 0)
        gridLay.addWidget(self.replaceButton, 3, 1)
        gridLay.addWidget(self.goToNodeButton, 3, 2)
        gridLay.addWidget(self.infoBox, 2, 1)
        
        
        widget = QWidget()
        widget.setLayout(gridLay)
        self.setCentralWidget(widget)
        
        
    def centerViewOnSelectedNode(self):
        myPaneTabs = hou.ui.paneTabs()    
        
        networkView = None
        
        for i in myPaneTabs:
            if i.type() == hou.paneTabType.NetworkEditor:
                networkView = i
                break
        
        selectedItem = self.listWidget.selectedItems()[0]
        self.nodeFileDict[selectedItem.text()].node().setCurrent(True, True)
        networkView.homeToSelection()
        self.listWidget.clearSelection()
                    
        
    def getNodes(self):
        nodesList = []
        for i in self.parmList:
            nodesList.append(i)
        self.nodesList = nodesList[:len(nodesList)//2]
        self.nodeFileDict = dict(zip(self.fileList, self.nodesList))                
    
        
    def getFileandParmLists(self):                
        
        for i in hou.fileReferences():  
                   
            fileInputParm = i[0]
            filepath = i[1]
            
            extension = os.path.splitext(filepath)[1]
            
            if fileInputParm != None and fileInputParm.node().isInsideLockedHDA() == False and fileInputParm.node().type().name() not in nodesBlacklist:               
                if extension in self.allowedFileExtensions:
                    self.fileList.append(filepath)
                    self.parmList.append(fileInputParm)
                    
                
    def checkSingleFileExists(self, myFile):        
        expandedPath = hou.text.expandString(myFile)
        fileExists = None
        if "<UDIM>" in expandedPath:
            wildCardPath = expandedPath.replace("<UDIM>","*")
            if glob.glob(wildCardPath):
                fileExists = True
            else:
                fileExists = False
        else:
            fileExists = os.path.exists(expandedPath)
     
        return fileExists    

        
    def checkFilesExists(self, myList):        
        self.existenceList = []        
        for i in myList:            
            expandedPath = hou.expandString(i)
            if "<UDIM>" in expandedPath:
                wildCardPath = expandedPath.replace("<UDIM>","*")
                if glob.glob(wildCardPath):
                    self.existenceList.append(True)
                else:
                    self.existenceList.append(False)
            else:
                fileExists = os.path.exists(expandedPath)
                self.existenceList.append(fileExists)

        return self.existenceList        

        
    def getInfo(self):    
        self.numberOfErrors = 0
        self.filePathErrors = []                
        existenceFalseCount = self.existenceList.count(False)               
        if existenceFalseCount > 0:            
            self.numberOfErrors += existenceFalseCount             
        falseIndices = [i for i, x in enumerate(self.existenceList) if x == False]       
        for i in falseIndices:
            self.filePathErrors.append(self.fileList[i])            
        return self.numberOfErrors, self.filePathErrors
        
        
    def selectAll(self):
        self.listWidget.selectAll()
    
        
    def clearAll(self):
        self.listWidget.clearSelection()
    
        
    def selectByName(self):
        self.selectByNameDialog.show()
    
        
    def replaceInPath(self):
        self.replaceDialogWindow.show()        
           
        
    def refresh(self):               
        
        if self.geoCheckBox.isChecked() == True and self.imageCheckBox.isChecked() == False:
            self.allowedFileExtensions = self.geometryFileExtensions
        elif self.geoCheckBox.isChecked() == False and self.imageCheckBox.isChecked() == True:
            self.allowedFileExtensions = self.imageFileExtensions
        elif self.geoCheckBox.isChecked() == True and self.imageCheckBox.isChecked() == True:
            self.allowedFileExtensions = self.imageFileExtensions + self.geometryFileExtensions
        else:
            self.allowedFileExtensions = self.imageFileExtensions + self.geometryFileExtensions  
        self.getFileandParmLists()
        
        if len(self.fileList)>0 :                                       
            
            self.fileList = []           
            self.getFileandParmLists()            
            self.existenceList = self.checkFilesExists(self.fileList)
            
            self.numErr = self.getInfo()[0]
            self.fileErr = self.getInfo()[1]
            
            myText = ""
            
            for i in self.fileErr:
                myText += str(i)+"\n"
              
            self.errorText = "There are " + str(self.numErr) + " errors, with these files:\n" + myText            
            
            self.listWidget.clear()
            
            for index, filepath in enumerate(self.fileList):
                myItem = QtWidgets.QListWidgetItem(filepath)
                
                if self.checkSingleFileExists(filepath) == True:
                    myItem.setCheckState(QtCore.Qt.Checked)
                    myItem.setForeground(QBrush(Qt.white))
                    
                if self.checkSingleFileExists(filepath) == False:
                    myItem.setCheckState(QtCore.Qt.Unchecked)            
                    myItem.setForeground(QBrush(Qt.darkRed))
                    
                self.listWidget.addItem(myItem)
            
            self.infoBox.setText(self.errorText)
            
           
class selectByNameWindow(QtWidgets.QMainWindow):
    
    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        self.setFixedSize(430, 80)
        self.setWindowTitle("Select by name")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        
        ## TARGET STRING ##
        self.targetString = QLineEdit("", self) 
        self.targetString.resize(300, 30)
        self.targetString.move(10, 20)
        
        ## SELECT BUTTON ##
        
        self.selectButton2 = QPushButton("Select",self)
        self.selectButton2.resize(100, 30)
        self.selectButton2.move(320, 20)
        self.selectButton2.clicked.connect(self.selectMatchingItems)     
     
        
    def selectMatchingItems(self):
        selectedFiles = []
        selectedIndices = []
        
        targetString = self.targetString.text()
        
        items = []        
        filesList = self.parent.listWidget 
        
        for i in range(filesList.count()-1):
            items.append(filesList.item(i))
        
        for item in items:
            if targetString != None and targetString in item.text():
                item.setSelected(True)
        self.close()

        
class replaceWindow(QtWidgets.QMainWindow):
    
    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        self.setFixedSize(1000, 300)
        self.setWindowTitle("Replace Selected Paths")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        
        ## SOURCE STRING ##       
        self.sourceStringLabel = QLabel("Text To Be Replaced:", self)
        self.sourceStringLabel.resize(180, 30)
        self.sourceStringLabel.move(10, 20)
        
        self.sourceString = QLineEdit("", self) 
        self.sourceString.resize(300, 30)
        self.sourceString.move(220, 20)
        
        
        ## TARGET STRING ##
        self.targetStringLabel = QLabel("New Text:", self)
        self.targetStringLabel.resize(120, 30)
        self.targetStringLabel.move(10, 80)        
        
        self.targetString = QLineEdit("", self) 
        self.targetString.resize(300, 30)
        self.targetString.move(140, 80)        
        
        
        ## PREVIEW LABEL ##        
        self.previewLabel = QLabel("",self)
        self.previewLabel.setStyleSheet("background-color:black; border-width:20px; border-color:white")
        self.previewLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.previewLabel.resize(700, 30)
        self.previewLabel.move(140, 150)
        
        
        ## PREVIEW BUTTON ##
        self.previewButton = QPushButton("Preview", self)
        self.previewButton.resize(100, 30)
        self.previewButton.move(10, 150)
        self.previewButton.clicked.connect(self.preview)
        
        
        ## REPLACE BUTTON ##
        self.doReplaceButton = QPushButton("Replace", self)
        self.doReplaceButton.resize(100, 30)
        self.doReplaceButton.move(10, 220)
        self.doReplaceButton.clicked.connect(self.doReplacement)
        
        
    def preview(self):
        if self.sourceString != None or self.sourceString != "" :
            selectedItems = self.parent.listWidget.selectedItems()
            previewItemName = selectedItems[0].text()
            previewText = previewItemName.replace(self.sourceString.text(), self.targetString.text())
            self.previewLabel.setText(previewText)
        else:
            print("Nothing is selected")
        
    def doReplacement(self):
        if self.sourceString != None or self.sourceString != "" :
            selectedItems = self.parent.listWidget.selectedItems()
            for i in selectedItems:
                selectedItemName = i.text()
                newPath = selectedItemName.replace(self.sourceString.text(), self.targetString.text())                                   
                self.parent.getNodes()
                filePathParm = self.parent.nodeFileDict[selectedItemName]
                filePathParm.set(newPath)                
                i.setText(newPath)                
            self.parent.refresh()     
        else:
            print("Source string is empty")
        self.close()
                        
        
mainWin = myMainUi()
mainWin.show()
