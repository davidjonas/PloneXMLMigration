"""XML migration script by David Jonas
This script migrates XML files into Plone Objects

Supposed to be run as an external method (Instructions: http://plone.org/documentation/kb/create-and-use-an-external-method ) 
"""

def migrate(self, xmlFilePath, typeToCreate, folder):
    from Products.MyExtensions.migrator import XMLMigrator
    
    #Create the migrator
    migrator = XMLMigrator(self, xmlFilePath, typeToCreate, folder)
    
    #Finally migrate
    print("=== Starting Migration. ===")
    migrator.startMigration()
    return "=== Migration sucessfull. Created %d items on folder %s (%d errors and %d skipped) ==="%(migrator.created, migrator.folderPath, migrator.errors, migrator.skipped)


from Products.CMFCore.utils import getToolByName
import transaction
from zope.site.hooks import getSite
from DateTime import DateTime


def normalizePersonName(person):
        names = person.strip().split(",")
        if len(names) == 2:
            return "%s %s"%(names[1], names[0])
        else:
            return person


def normalizeAllPersons(self):
    catalog = getToolByName(getSite(), 'portal_catalog')
    objects = catalog.searchResults(portal_type = ["Media Person"])
    
    count = 0
    
    for object in objects:
      print "Found %s and normalizes to: %s"%(object.Title, normalizePersonName(object.Title))
      object.getObject().title = normalizePersonName(object.Title)
      transaction.commit()
      count = count + 1
    
    print "Found and processed %s items"%count


def changeDatesOnAllPersons(self):
    catalog = getToolByName(getSite(), 'portal_catalog')
    objects = catalog.searchResults(portal_type = ["Media Person"])
    
    count = 0
    
    for object in objects:
      print "Found born date %s and normalizes to: %s"%(object.getObject().start(), object.getObject().start() is None and "None" or object.getObject().start().year())
      print "Found died date %s and normalizes to: %s"%(object.getObject().end(), object.getObject().end() is None and "None" or object.getObject().end().year())
      if object.getObject().start() is not None:
          object.getObject().bornDate = "%s"%object.getObject().start().year()
      if object.getObject().end() is not None:
          object.getObject().diedDate = "%s"%object.getObject().end().year()
      transaction.commit()
      count = count + 1
    
    print "Found and processed %s items"%count
    
    
def migrate_timezones(self):
	catalog = getToolByName(getSite(), 'portal_catalog')
	results = catalog.searchResults({'portal_type': 'Media Event'})
        
        for result in results:
            event = result.getObject()
            try:
                valueStart = event.start()
                valueEnd = event.end()
            except:
                print("Error: getting the start or end date of %s"%event.id)
                continue
            
            print("migrating %(id)s with start: %(start)s and end: %(end)s"%{'id': event.id, 'start': valueStart, 'end': valueEnd})
            
            timezone = u'Europe/London'
            finalStart = DateTime(valueStart.year(), valueStart.month(), valueStart.day(), valueStart.hour(), valueStart.minute(), valueStart.second(), timezone)
            finalEnd = DateTime(valueEnd.year(), valueEnd.month(), valueEnd.day(), valueEnd.hour(), valueEnd.minute(), valueEnd.second(), timezone)
            
            event.setTimezone(timezone)
            
            event.setStartDate(finalStart)
            event.setEndDate(finalEnd)
            
            print("Migrated %(id)s with start: %(start)s and end: %(end)s"%{'id': event.id, 'start': event.start(), 'end': event.end()})
            
            transaction.commit()