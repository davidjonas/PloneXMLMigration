"""XML migration script by David Jonas
This script migrates XML files into Plone Objects

Supposed to be run as an external method trhough the boilerplate script migration.py 
(Instructions: http://plone.org/documentation/kb/create-and-use-an-external-method )
"""

import libxml2
import urllib2
import AccessControl
import transaction
import time
import sys
from DateTime import DateTime
from plone.i18n.normalizer import idnormalizer
from Testing.makerequest import makerequest
from Products.CMFCore.utils import getToolByName
from Acquisition import aq_inner
try:
    from collective.contentleadimage.config import IMAGE_FIELD_NAME
    from collective.contentleadimage.config import IMAGE_CAPTION_FIELD_NAME
    from collective.contentleadimage.interfaces import ILeadImageable
    import collective.contentleadimage
    LEADIMAGE_EXISTS = True
except ImportException:
    LEADIMAGE_EXISTS = False
    
# Folder where the images are (Do not forget to add a trailing slash)
IMAGE_FOLDER = "/var/plone4_/zeocluster/src/porseleinImages/"

class ObjectItem:
    """Class to store an Object from the xml file"""
    def __init__(self):
        self.priref = ""
        self.tags =  []
        self.body = ""
        self.label_text =  ""
        self.images = []
        self.object_number = ""
        self.object_name = ""
        self.title = ""
        self.production_place = ""
        self.production_date_start = ""
        self.production_date_end = ""
        self.production_period = ""
        self.materials = []
        self.dimention_types = []
        self.dimention_values = []
        self.dimention_units = []
        self.creator = ""
        self.checked = False
        
    def Title(self):
        if self.title != "":
            return self.title
        elif self.object_number != "" and self.object_name != "":
            return "%s, %s"%(self.object_number, self.object_name)
        elif self.object_name != "":
            return self.object_name
        elif self.object_number != "":
            return self.object_number
        else:
            return self.priref

    def Materials(self):
        return ", ".join(self.materials)

class XMLMigrator:
    """ Gets an XML file, parses it and creates the content in the chosen plone instance """
 
    def __init__(self, portal, xmlFilePath, typeToCreate, folder):
        """Constructor that gets access to both the parsed file and the chosen portal"""
        print("INITIALIZING CONTENT MIGRATOR")
        #check if portal exists
        self.portal = portal
        
        #Parse the XML file
        self.xmlDoc = libxml2.parseFile(xmlFilePath)
        
        #Set the migration mode
        self.typeToCreate = typeToCreate
        
        #Save the path to the folder to migrate to
        self.folderPath = folder.split("/")
        
        #Initialize the counters for the log
        self.errors = 0 #Number of errors - failed to create an item
        self.created = 0 #Number of sucessfully created items
        self.skipped = 0 #Number of items skipped because another item with the same id already exists on that folder.
    
        #DEBUG
        self.fields = []
    
    
    def cleanUp(self):
        self.xmlDoc.freeDoc()
        return
    
    def getContainer(self):
        #if there is no folder info, fail.
        if len(self.folderPath) == 0:
            print("Folder check failed")
            return None
        
        #Set the container to the root object of the portal
        container = self.portal
        
        #Navigate the folders creating them if necessary
        for folder in self.folderPath:
            if hasattr(container, folder):
                container = container[folder]
            else:
                print ("== Chosen folder " + folder + " does not exist. Creating new folder ==")
                container.invokeFactory(type_name="Folder", id=folder, title="migration of type: " + self.typeToCreate)
                container = container[folder]
            
        return container

    def getOrCreateFolder(self, container, folderId, publish):
        #Get a folder if it exists or create it if it doesn't
        if folderId != "":
            try:
                if hasattr(container, folderId):
                        container = container[folderId]
                else:
                    print ("== Creating new folder ==")
                    container.invokeFactory(type_name="Folder", id=folderId, title=folderId)
                    container = container[folderId]
                    
                    #publish the folder if needed
                    if publish:
                        container.portal_workflow.doActionFor(container, "publish", comment="content automatically published by migrationScript")
                    
                return container
            except:
                print("Folder %s could not be created: %s"%(folderId, sys.exc_info()[1]))
                return None
        else:
            return None
            

    def addImage(self, container, image):
        try:
            filename = image.split("\\")[2]
            dirtyId = filename
            result = False
            transaction.begin()
        
        
            id = idnormalizer.normalize(unicode(dirtyId, "utf-8"))
            
            #if not hasattr(container, str(id)):                                             #The processForm changes the id to the fileneame in lower case
            if not hasattr(container, filename.lower()): 
                #import pdb; pdb.set_trace()
                print "Adding a new image: %s"%filename
                container.invokeFactory(type_name="Image", id=id, title=filename)
            else:
                print "Image %s already exists, skipping"%filename
                return True
            
            item = container[str(id)]
            
            imageFile = open(IMAGE_FOLDER + filename.lower(), "r")
            imageData = imageFile.read()
            item.edit(file=imageData)
            imageFile.close()
            
            #import pdb; pdb.set_trace()
            item.processForm()
             
            transaction.commit()
            result = True
            return result
        except:
            transaction.abort()
            print "Unexpected error on createImage: ", sys.exc_info()[1]
            return False

    def addLeadImage(self, item, image):
        #set the lead image if necessary and if lead image product is installed
        if LEADIMAGE_EXISTS and image != "":
            #download and create the image
            try:
                imageFile = urllib2.urlopen(image)
                imageData = imageFile.read()
                urlSplit = image.split("/")
                filename = urlSplit[len(urlSplit)-1]
                
                #add the image as leadImage
                if ILeadImageable.providedBy(item):
                    field = aq_inner(item).getField(IMAGE_FIELD_NAME)
                    field.set(item, imageData, filename=filename)
                else:
                    print("Item type does not accept leadImage")
                
                #release the image file
                imageFile.close()
                return
            except:
                print "LeadImage URL not available. LeadImage not created because: (" + image + ")", sys.exc_info()[1]
                return
            
    def addLeadImageCaption(self, item, caption):
        #set the caption if necessary and if lead image product is installed
        if LEADIMAGE_EXISTS and caption != "":
            #add the caption
            try:
                if ILeadImageable.providedBy(item):
                    field = aq_inner(item).getField(IMAGE_CAPTION_FIELD_NAME) 
                    field.set(item, caption)
                else:
                    print("Item type does not accept leadImage therefore captions will be ignored")
            except:
                print "Error adding leadImage caption: ", sys.exc_info()[1]
        return

    def createObject(self, obj):
        transaction.begin()
        container = self.getContainer()
        dirtyId = obj.priref
        counter = 1
        result = False

        try:
            id = idnormalizer.normalize(unicode(dirtyId, "utf-8"))
            
            #while hasattr(container, id) and id != "":
            #    print ("Object " + id + " already exists.")
            #    counter = counter+1
            #    dirtyId = obj.title + str(counter)
            #    id = idnormalizer.normalize(unicode(dirtyId, "utf-8"))
            #    print ("creating " + id + " instead")
            
            if hasattr(container, id):
                self.created = self.created + 1
                print "Item already exists, reviewing fields"
                changedObj = False
                existingObj = container[id]
                
                if existingObj.title != obj.Title():
                    existingObj.title = obj.Title()
                    #print "Title change from %s to %s"%(existingObj.title, obj.Title())
                    changedObj = True
                if existingObj.label_text != obj.label_text:
                    existingObj.label_text = obj.label_text
                    #print "Label change from %s to %s"%(existingObj.label_text, obj.label_text)
                    changedObj = True
                if existingObj.object_number != obj.object_number:
                    existingObj.object_number = obj.object_number
                    #print "Object Number change from %s to %s"%(existingObj.object_number, obj.object_number)
                    changedObj = True
                if existingObj.object_name != obj.object_name:
                    existingObj.object_name = obj.object_name
                    #print "Object Name change from %s to %s"%(existingObj.object_name, obj.object_name)
                    changedObj = True
                if existingObj.production_place != obj.production_place:
                    existingObj.production_place = obj.production_place
                    #print "Production Place change from %s to %s"%(existingObj.production_place, obj.production_place)
                    changedObj = True
                if existingObj.production_date_start != obj.production_date_start:
                    existingObj.production_date_start = obj.production_date_start
                    #print "Production Date Start change from %s to %s"%(existingObj.production_date_start, obj.production_date_start)
                    changedObj = True
                if existingObj.production_date_end != obj.production_date_end:
                    existingObj.production_date_end = obj.production_date_end
                    #print "Production Date End change from %s to %s"%(existingObj.production_date_end, obj.production_date_end)
                    changedObj = True
                if existingObj.period != obj.production_period:
                    print "Production period change from %s to %s"%(existingObj.period, obj.production_period)
                    existingObj.period = obj.production_period
                    changedObj = True
                if existingObj.materials != obj.Materials():
                    existingObj.materials = obj.Materials()
                    #print "Materials change from %s to %s"%(existingObj.materials, obj.Materials())
                    changedObj = True
                if existingObj.creator != obj.creator:
                    existingObj.creator = obj.creator
                    #print "Creator change from %s to %s"%(existingObj.creator, obj.creator)
                    changedObj = True
                
                if changedObj:
                    # Commit transaction
                    print "Item has changed, Commiting transaction..."
                    
                    transaction.commit()
                    # Perform ZEO client synchronization (if runnning in clustered mode) Not doing this because now its running as a External Metod instead
                    #app._p_jar.sync()
                
                #print "Checking for new images:"
                #Add Images to the object
                #item = container[id]
                #for image in obj.images:
                    #pass
                    #print "Adding image %s: "%image
                    #self.addImage(item, image)
                return True
            
            #Check if Object exists
            if not hasattr(container, id):
                print "NEW OBJECT FOUND. ADDING: %s"%id
                container.invokeFactory(
                    type_name="Object",
                    id=id,
                    title=obj.Title(),
                    priref=obj.priref,
                    label_text = obj.label_text,
                    object_number=obj.object_number,
                    object_name = obj.object_name,
                    production_place = obj.production_place,
                    production_date_start = obj.production_date_start,
                    production_date_end = obj.production_date_end,
                    period = obj.production_period,
                    materials = obj.Materials(),
                    creator = obj.creator
                    )
                
                #get the Object after creating
                item = container[id]
                
                #set the body
                item.setText(obj.body)
                
                #set the dimentions
                dims = []
                for i in range(0, len(obj.dimention_types)):
                    try:
                        dims.append("%s: %s %s"%(obj.dimention_types[i], obj.dimention_values[i], obj.dimention_units[i]))
                    except:
                        pass
                item.dimentions = "; ".join(dims)
                    
                #Add tags to Keywords/Categories
                item.setSubject(obj.tags)
                
                #publish or revise
                if obj.checked:
                    item.portal_workflow.doActionFor(item, "revise")
                #else:
                    #item.portal_workflow.doActionFor(item, "publish", comment="Content automatically published by migrationScript")
                
                # Commit transaction
                transaction.commit()
                # Perform ZEO client synchronization (if runnning in clustered mode) Not doing this because now its running as a External Metod instead
                #app._p_jar.sync()
                
                #Add Images to the object
                for image in obj.images:
                    #pass
                    print "Adding image %s: "%image
                    self.addImage(item, image)
                
                result = True
                self.created = self.created + 1
                print("== Page created ==")
                
        except:
            self.errors = self.errors + 1
            print "Unexpected error on createObject (" +dirtyId+ "):", sys.exc_info()[1]
            transaction.abort()
            raise
            return result
            
          
    
        if not result:
            self.skipped = self.skipped + 1
            print("Skipped item: " + dirtyId)
        return result

    def migrateTest(self):
        root = self.xmlDoc.children
        for field in root.children:
            if field.name == "record":
                #print("== Parsing record ==")
                for testField in field.children:
                    if testField.name not in self.fields:
                        self.fields.append(testField.name)
        return
    
    def migrateToObject(self):
        root = self.xmlDoc.children
        for field in root.children:
            if field.name == "record":
                #print("== Parsing Object: ==")
                currentObject = ObjectItem()
                for objectField in field.children:
                    if objectField.name == 'priref':
                        currentObject.priref = objectField.content
                        #print("    priref: " + currentObject.priref)
                    elif objectField.name == 'object_name':
                        currentObject.tags.append(objectField.content)
                        currentObject.object_name = objectField.content
                        #print("    tag added: " + objectField.content)
                    elif objectField.name == 'label.text':
                        if currentObject.body == "":
                            currentObject.body = "<p>%s</p>"%objectField.content
                        else:
                            currentObject.label_text = currentObject.label_text + "<p>%s</p>"%objectField.content
                        #print("    body / label_text added: " + currentObject.body)
                    elif objectField.name == 'reproduction.identifier_URL':
                        currentObject.images.append(objectField.content)
                        #print("    image: " + objectField.content)
                    elif objectField.name == 'object_number':
                        currentObject.object_number = objectField.content
                        #print("    object_number: " + currentObject.object_number)
                    elif objectField.name == 'title':
                        if objectField.content !="-":
                            currentObject.title = objectField.content
                            #print("    title: " + currentObject.title)
                    elif objectField.name == 'production.place':
                        currentObject.production_place = objectField.content
                        #print("    production_place: " + currentObject.production_place)
                    elif objectField.name == 'production.date.start':
                        currentObject.production_date_start = objectField.content
                        #print("    production_date_start: " + currentObject.production_date_start)
                    elif objectField.name == 'production.date.end':
                        currentObject.production_date_end = objectField.content
                        #print("    production_date_end: " + currentObject.production_date_end)
                    elif objectField.name == 'production.period':
                        currentObject.production_period = objectField.content
                        #print("    production_period: " + currentObject.production_period)
                    elif objectField.name == 'material':
                        currentObject.materials.append(objectField.content)
                        currentObject.tags.append(objectField.content)
                        #print("    material added: " + objectField.content)
                    elif objectField.name == 'dimension.type':
                        currentObject.dimention_types.append(objectField.content)
                        #print("    dimention added: " + objectField.content)
                    elif objectField.name == 'dimension.value':
                        currentObject.dimention_values.append(objectField.content)
                        #print("    dimention val added: " + objectField.content)
                    elif objectField.name == 'dimension.unit':
                        currentObject.dimention_units.append(objectField.content)
                        #print("    dimention unit added: " + objectField.content)
                    elif objectField.name == 'creator':
                        currentObject.creator = objectField.content
                        #print("    creator: " + currentObject.creator)
                    
                        
                #currentObject is now populated with the data from the XML now we create a Object in plone
                self.createObject(currentObject)
        return

    def startMigration(self):
        if self.portal is not None:
            if self.typeToCreate == "Test":
                self.migrateTest()
                for f in self.fields:
                    print f
            elif self.typeToCreate == "Object":
                self.migrateToObject()
            else:
                print("TYPE NOT RECOGNIZED!! ==>> " + self.typeToCreate)
            
            self.cleanUp()
        else:
            print ("Portal is NONE!!!")
            self.cleanUp()
        return
