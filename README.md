PloneXMLMigration
=================

Small script written to migrate content from XML files into Plone. It's specific to one particular website and one particular content but it can easily be adapted to create other plone content from XML files.

It is meant to be used in a product and run as an external method (Instructions:  )

I ran it by creating a Extensions product (in this case Products.MyExtensions), adding these files to it and running it from the url of the external method with the necessary arguments passed through the query string.

Note that there are many better ways to do this and many products have been created for this and are much more flexible. I have created this script because it was a one time migration and writing it myself had a considerably less steap learning curve than learning how to use any of the existing products at the time. It has served me well though.


Create and Use an External Method 
==================================

(from http://plone.org/documentation/kb/create-and-use-an-external-method)
 
by Tom Elliott — last modified Dec 30, 2008

Zope External Methods allow you to write and register python scripts that can be called through-the-web to manipulate your Zope/Plone instance. The main difference is that these can do things with a much higher privilege level since they are located on the file system, not in the web interface.
Inspect your Plone installation and find the Zope folder. For example, on Windows, you might find: C:\Program Files\Plone 2\Zope.

If there is not a folder named "Extensions" in your Zope folder, create one.
Put a copy of the module (e.g., blah.py) containing the function you want to call (e.g., argh()) in this directory.
(Re)start Zope.

Open the ZMI (e.g., http://localhost/manage) and navigate to the folder where you want the external method to reside (e.g., /dog/leg). This location will provide the run context for your script (i.e., a "self" paramater on the argh() function will be populated with a reference to this folder). Note: don't use the ZMI to create new folders; instead, do it "through-the-Plone" (see How-to: Changing Tabs).
In the ZMI, on the "Contents" tab for the context folder, select the combo box next to the "Add" button and choose "External Method".

Give the new external method the necessary properties, for example:

id: run_argh

title (optional): Run the argh function

module name: blah

function name: argh

Click the "Add" button

You can now call your external method through the web, e.g.: 

http://localhost/dog/leg/run_argh

If the function called by your external method requires parameters, you can supply these after a question mark, for example: http://localhost/dog/leg/run_argh?voice=piratical

This how-to was helped along by http://www.zope.org/Documentation/How-To/ExternalMethods and Sean Gillies.
