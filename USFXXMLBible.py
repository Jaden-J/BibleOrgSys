#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# USFXXMLBible.py
#   Last modified: 2013-12-18 by RJH (also update ProgVersion below)
#
# Module handling USFX XML Bibles
#
# Copyright (C) 2013 Robert Hunt
# Author: Robert Hunt <robert316@users.sourceforge.net>
# License: See gpl-3.0.txt
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Module for defining and manipulating complete or partial USFX Bibles.
"""

ProgName = "USFX XML Bible handler"
ProgVersion = "0.03"
ProgNameVersion = "{} v{}".format( ProgName, ProgVersion )

debuggingThisModule = False


import os, sys, logging, multiprocessing
from gettext import gettext as _
from xml.etree.ElementTree import ElementTree, ParseError

import Globals
from Bible import Bible, BibleBook



filenameEndingsToIgnore = ('.ZIP.GO', '.ZIP.DATA',) # Must be UPPERCASE
extensionsToIgnore = ('ZIP', 'BAK', 'LOG', 'HTM','HTML', 'USX', 'STY', 'LDS', 'SSF', 'VRS', 'ASC', 'CSS', 'ODT','DOC','TXT', 'JAR', ) # Must be UPPERCASE



def USFXXMLBibleFileCheck( sourceFolder, strictCheck=True, autoLoad=False ):
    """
    Given a folder, search for USFX XML Bible files or folders in the folder and in the next level down.

    Returns False if an error is found.

    if autoLoad is false (default)
        returns None, or the number found.

    if autoLoad is true and exactly one USFX Bible is found,
        returns the loaded USFXXMLBible object.
    """
    if Globals.verbosityLevel > 2: print( "USFXXMLBibleFileCheck( {}, {}, {} )".format( sourceFolder, strictCheck, autoLoad ) )
    if Globals.debugFlag: assert( sourceFolder and isinstance( sourceFolder, str ) )
    if Globals.debugFlag: assert( autoLoad in (True,False,) )

    # Check that the given folder is readable
    if not os.access( sourceFolder, os.R_OK ):
        logging.critical( _("USFXXMLBibleFileCheck: Given '{}' folder is unreadable").format( sourceFolder ) )
        return False
    if not os.path.isdir( sourceFolder ):
        logging.critical( _("USFXXMLBibleFileCheck: Given '{}' path is not a folder").format( sourceFolder ) )
        return False

    # Find all the files and folders in this folder
    if Globals.verbosityLevel > 3: print( " USFXXMLBibleFileCheck: Looking for files in given {}".format( sourceFolder ) )
    foundFolders, foundFiles = [], []
    for something in os.listdir( sourceFolder ):
        somepath = os.path.join( sourceFolder, something )
        if os.path.isdir( somepath ): foundFolders.append( something )
        elif os.path.isfile( somepath ):
            somethingUpper = something.upper()
            somethingUpperProper, somethingUpperExt = os.path.splitext( somethingUpper )
            ignore = False
            for ending in filenameEndingsToIgnore:
                if somethingUpper.endswith( ending): ignore=True; break
            if ignore: continue
            if not somethingUpperExt[1:] in extensionsToIgnore: # Compare without the first dot
                foundFiles.append( something )
    if '__MACOSX' in foundFolders:
        foundFolders.remove( '__MACOSX' )  # don't visit these directories
    #print( 'ff', foundFiles )

    # See if there's a USFX project here in this folder
    numFound = 0
    looksHopeful = False
    lastFilenameFound = None
    for thisFilename in sorted( foundFiles ):
        if strictCheck or Globals.strictCheckingFlag:
            firstLines = Globals.peekIntoFile( thisFilename, sourceFolder, numLines=3 )
            if not firstLines or len(firstLines)<2: continue
            if not firstLines[0].startswith( '<?xml version="1.0"' ) \
            and not firstLines[0].startswith( '\ufeff<?xml version="1.0"' ): # same but with BOM
                if Globals.verbosityLevel > 2: print( "USFXB (unexpected) first line was '{}' in {}".format( firstLines, thisFilename ) )
                continue
            if "<usfx " not in firstLines[0]:
                continue
        lastFilenameFound = thisFilename
        numFound += 1
    if numFound:
        if Globals.verbosityLevel > 2: print( "USFXXMLBibleFileCheck got", numFound, sourceFolder, lastFilenameFound )
        if numFound == 1 and autoLoad:
            ub = USFXXMLBible( sourceFolder, lastFilenameFound )
            ub.load() # Load and process the file
            return ub
        return numFound
    elif looksHopeful and Globals.verbosityLevel > 2: print( "    Looked hopeful but no actual files found" )

    # Look one level down
    numFound = 0
    foundProjects = []
    for thisFolderName in sorted( foundFolders ):
        tryFolderName = os.path.join( sourceFolder, thisFolderName+'/' )
        if Globals.verbosityLevel > 3: print( "    USFXXMLBibleFileCheck: Looking for files in {}".format( tryFolderName ) )
        foundSubfolders, foundSubfiles = [], []
        for something in os.listdir( tryFolderName ):
            somepath = os.path.join( sourceFolder, thisFolderName, something )
            if os.path.isdir( somepath ): foundSubfolders.append( something )
            elif os.path.isfile( somepath ):
                somethingUpper = something.upper()
                somethingUpperProper, somethingUpperExt = os.path.splitext( somethingUpper )
                ignore = False
                for ending in filenameEndingsToIgnore:
                    if somethingUpper.endswith( ending): ignore=True; break
                if ignore: continue
                if not somethingUpperExt[1:] in extensionsToIgnore: # Compare without the first dot
                    foundSubfiles.append( something )
        #print( 'fsf', foundSubfiles )

        # See if there's a USFX project here in this folder
        for thisFilename in sorted( foundSubfiles ):
            if strictCheck or Globals.strictCheckingFlag:
                firstLines = Globals.peekIntoFile( thisFilename, tryFolderName, numLines=2 )
                if not firstLines or len(firstLines)<2: continue
                if not firstLines[0].startswith( '<?xml version="1.0"' ) \
                and not firstLines[0].startswith( '\ufeff<?xml version="1.0"' ): # same but with BOM
                    if Globals.verbosityLevel > 2: print( "USFXB (unexpected) first line was '{}' in {}".format( firstLines, thisFilename ) )
                    continue
                if "<usfx " not in firstLines[0]:
                    continue
            foundProjects.append( (tryFolderName, thisFilename,) )
            lastFilenameFound = thisFilename
            numFound += 1
    if numFound:
        if Globals.verbosityLevel > 2: print( "USFXXMLBibleFileCheck foundProjects", numFound, foundProjects )
        if numFound == 1 and autoLoad:
            if Globals.debugFlag: assert( len(foundProjects) == 1 )
            ub = USFXXMLBible( foundProjects[0][0], foundProjects[0][1] ) # Folder and filename
            ub.load() # Load and process the file
            return ub
        return numFound
# end of USFXXMLBibleFileCheck



def clean( elementText ):
    """
    Given some text from an XML element (which might be None)
        return a stripped value and with internal CRLF characters replaced by spaces.
    """
    if elementText is not None:
        return elementText.strip().replace( '\r\n', ' ' ).replace( '\n', ' ' ).replace( '\r', ' ' )
# end of clean



class USFXXMLBible( Bible ):
    """
    Class to load and manipulate USFX Bibles.

    """
    def __init__( self, sourceFolder, givenName=None, encoding='utf-8' ):
        """
        Create the internal USFX Bible object.
        """
         # Setup and initialise the base class first
        Bible.__init__( self )
        self.objectNameString = "USFX XML Bible object"
        self.objectTypeString = "USFX"

        self.sourceFolder, self.givenName, self.encoding = sourceFolder, givenName, encoding # Remember our parameters

        # Now we can set our object variables
        self.name = self.givenName
        if not self.name: self.name = os.path.basename( self.sourceFolder )
        if not self.name: self.name = os.path.basename( self.sourceFolder[:-1] ) # Remove the final slash
        if not self.name: self.name = "USFX Bible"
        if self.name.endswith( '_usfx' ): self.name = self.name[:-5] # Remove end of name for Haiola projects

        # Do a preliminary check on the readability of our folder
        if not os.access( self.sourceFolder, os.R_OK ):
            logging.error( "USFXXMLBible: Folder '{}' is unreadable".format( self.sourceFolder ) )

        # Do a preliminary check on the contents of our folder
        self.sourceFilename = self.sourceFilepath = None
        foundFiles, foundFolders = [], []
        for something in os.listdir( self.sourceFolder ):
            somepath = os.path.join( self.sourceFolder, something )
            if os.path.isdir( somepath ): foundFolders.append( something )
            elif os.path.isfile( somepath ):
                somethingUpper = something.upper()
                somethingUpperProper, somethingUpperExt = os.path.splitext( somethingUpper )
                ignore = False
                for ending in filenameEndingsToIgnore:
                    if somethingUpper.endswith( ending): ignore=True; break
                if ignore: continue
                if not somethingUpperExt[1:] in extensionsToIgnore: # Compare without the first dot
                    foundFiles.append( something )
            else: logging.error( "Not sure what '{}' is in {}!".format( somepath, self.sourceFolder ) )
        if foundFolders: logging.info( "USFXXMLBible: Surprised to see subfolders in '{}': {}".format( self.sourceFolder, foundFolders ) )
        if not foundFiles:
            if Globals.verbosityLevel > 0: print( "USFXXMLBible: Couldn't find any files in '{}'".format( self.sourceFolder ) )
            return # No use continuing

        #print( self.sourceFolder, foundFolders, len(foundFiles), foundFiles )
        numFound = 0
        for thisFilename in sorted( foundFiles ):
            firstLines = Globals.peekIntoFile( thisFilename, sourceFolder, numLines=3 )
            if not firstLines or len(firstLines)<2: continue
            if not firstLines[0].startswith( '<?xml version="1.0"' ) \
            and not firstLines[0].startswith( '\ufeff<?xml version="1.0"' ): # same but with BOM
                if Globals.verbosityLevel > 2: print( "USFXB (unexpected) first line was '{}' in {}".format( firstLines, thisFilename ) )
                continue
            if "<usfx " not in firstLines[0]:
                continue
            lastFilenameFound = thisFilename
            numFound += 1
        if numFound:
            if Globals.verbosityLevel > 2: print( "USFXXMLBible got", numFound, sourceFolder, lastFilenameFound )
            if numFound == 1:
                self.sourceFilename = lastFilenameFound
                self.sourceFilepath = os.path.join( self.sourceFolder, self.sourceFilename )
        elif looksHopeful and Globals.verbosityLevel > 2: print( "    Looked hopeful but no actual files found" )
    # end of USFXXMLBible.__init_


    def load( self ):
        """
        Load the XML data file -- we should already know the filepath.
        """
        if Globals.verbosityLevel > 1:
            print( _("USFXXMLBible: Loading {} from {}...").format( self.name, self.sourceFolder ) )

                                #if Globals.verbosityLevel > 2: print( _("  It seems we have {}...").format( BBB ) )
                        #self.thisBook = BibleBook( self.name, BBB )
                        #self.thisBook.objectNameString = "OSIS XML Bible Book object"
                        #self.thisBook.objectTypeString = "OSIS"
                        #self.haveBook = True

        try: self.tree = ElementTree().parse( self.sourceFilepath )
        except ParseError:
            errorString = sys.exc_info()[1]
            logging.critical( "USFXXMLBible.load: failed loading the xml file {}: '{}'.".format( self.sourceFilepath, errorString ) )
            return
        if Globals.debugFlag: assert( len ( self.tree ) ) # Fail here if we didn't load anything at all

        # Find the main (osis) container
        if self.tree.tag == 'usfx':
            location = "USFX file"
            Globals.checkXMLNoText( self.tree, location, '4f6h' )
            Globals.checkXMLNoTail( self.tree, location, '1wk8' )
            # Process the attributes first
            self.schemaLocation = None
            for attrib,value in self.tree.items():
                #print( "attrib", repr(attrib), repr(value) )
                if attrib.endswith("SchemaLocation"):
                    self.schemaLocation = value
                else:
                    logging.warning( "fv6g Unprocessed {} attribute ({}) in {}".format( attrib, value, location ) )
            BBB = C = V = None
            for element in self.tree:
                #print( "element", repr(element.tag) )
                sublocation = element.tag + " " + location
                if element.tag == 'languageCode':
                    self.languageCode = element.text
                    Globals.checkXMLNoTail( element, sublocation, 'cff3' )
                    Globals.checkXMLNoAttributes( element, sublocation, 'des1' )
                    Globals.checkXMLNoSubelements( element, sublocation, 'dwf2' )
                elif element.tag == 'book':
                    self.loadBook( element )
                    ##Globals.checkXMLNoSubelements( element, sublocation, '54f2' )
                    #Globals.checkXMLNoTail( element, sublocation, 'hd35' )
                    ## Process the attributes
                    #idField = bookStyle = None
                    #for attrib,value in element.items():
                        #if attrib=='id' or attrib=='code':
                            #idField = value # Should be USFM bookcode (not like bookReferenceCode which is BibleOrgSys BBB bookcode)
                            ##if idField != bookReferenceCode:
                            ##    logging.warning( _("Unexpected book code ({}) in {}").format( idField, sublocation ) )
                        #elif attrib=='style':
                            #bookStyle = value
                        #else:
                            #logging.warning( _("gfw2 Unprocessed {} attribute ({}) in {}").format( attrib, value, sublocation ) )
                else:
                    logging.warning( _("dbw1 Unprocessed {} element after {} {}:{} in {}").format( element.tag, BBB, C, V, sublocation ) )
                    #self.addPriorityError( 1, c, v, _("Unprocessed {} element").format( element.tag ) )

        if not self.books: # Didn't successfully load any regularly named books -- maybe the files have weird names??? -- try to be intelligent here
            if Globals.verbosityLevel > 2:
                print( "USFXXMLBible.load: Didn't find any regularly named USFX files in '{}'".format( self.sourceFolder ) )
            for thisFilename in foundFiles:
                # Look for BBB in the ID line (which should be the first line in a USFX file)
                isUSFX = False
                thisPath = os.path.join( self.sourceFolder, thisFilename )
                with open( thisPath ) as possibleUSXFile: # Automatically closes the file when done
                    for line in possibleUSXFile:
                        if line.startswith( '\\id ' ):
                            USXId = line[4:].strip()[:3] # Take the first three non-blank characters after the space after id
                            if Globals.verbosityLevel > 2: print( "Have possible USFX ID '{}'".format( USXId ) )
                            BBB = Globals.BibleBooksCodes.getBBBFromUSFM( USXId )
                            if Globals.verbosityLevel > 2: print( "BBB is '{}'".format( BBB ) )
                            isUSFX = True
                        break # We only look at the first line
                if isUSFX:
                    UBB = USFXXMLBibleBook( self.name, BBB )
                    UBB.load( self.sourceFolder, thisFilename, self.encoding )
                    UBB.validateMarkers()
                    print( UBB )
                    self.books[BBB] = UBB
                    # Make up our book name dictionaries while we're at it
                    assumedBookNames = UBB.getAssumedBookNames()
                    for assumedBookName in assumedBookNames:
                        self.BBBToNameDict[BBB] = assumedBookName
                        assumedBookNameLower = assumedBookName.lower()
                        self.bookNameDict[assumedBookNameLower] = BBB # Store the deduced book name (just lower case)
                        self.combinedBookNameDict[assumedBookNameLower] = BBB # Store the deduced book name (just lower case)
                        if ' ' in assumedBookNameLower: self.combinedBookNameDict[assumedBookNameLower.replace(' ','')] = BBB # Store the deduced book name (lower case without spaces)
            if self.books: print( "USFXXMLBible.load: Found {} irregularly named USFX files".format( len(self.books) ) )
    # end of USFXXMLBible.load


    def loadBook( self, bookElement ):
        """
        Load the book container from the XML data file.
        """
        if Globals.verbosityLevel > 3:
            print( _("USFXXMLBible.loadBook: Loading {} from {}...").format( self.name, self.sourceFolder ) )
        assert( bookElement.tag == 'book' )
        mainLocation = self.name + " USFX book"

        # Process the attributes first
        bookCode = None
        for attrib,value in bookElement.items():
            if attrib == 'id':
                bookCode = value
            else:
                logging.warning( "bce3 Unprocessed {} attribute ({}) in {}".format( attrib, value, mainLocation ) )
        BBB = Globals.BibleBooksCodes.getBBBFromUSFM( bookCode )
        mainLocation = "{} USFX {} book".format( self.name, BBB )
        if Globals.verbosityLevel > 2:
            print( _("USFXXMLBible.loadBook: Loading {} from {}...").format( BBB, self.name ) )
        Globals.checkXMLNoText( self.tree, mainLocation, '4f6h' )
        Globals.checkXMLNoTail( self.tree, mainLocation, '1wk8' )

        # Now create our actual book
        self.thisBook = BibleBook( self.name, BBB )
        self.thisBook.objectNameString = "USFX XML Bible Book object"
        self.thisBook.objectTypeString = "USFX"

        C = V = None
        for element in bookElement:
            #print( "element", repr(element.tag) )
            location = element.tag + " of " + mainLocation
            if element.tag == 'id':
                idText = clean( element.text )
                Globals.checkXMLNoTail( element, location, 'vsg3' )
                Globals.checkXMLNoSubelements( element, location, 'ksq2' )
                for attrib,value in element.items():
                    if attrib == 'id':
                        assert( value == bookCode )
                    else:
                        logging.warning( _("vsg4 Unprocessed {} attribute ({}) in {}").format( attrib, value, location ) )
                self.thisBook.appendLine( 'id', bookCode + ((' '+idText) if idText else '') )
            elif element.tag == 'ide':
                ideText = clean( element.text )
                Globals.checkXMLNoTail( element, location, 'jsa0' )
                Globals.checkXMLNoSubelements( element, location, 'ls01' )
                charset = None
                for attrib,value in element.items():
                    if attrib == 'charset': charset = value
                    else:
                        logging.warning( _("jx53 Unprocessed {} attribute ({}) in {}").format( attrib, value, location ) )
                self.thisBook.appendLine( 'ide', charset + ((' '+ideText) if ideText else '') )
            elif element.tag == 'h':
                hText = element.text
                Globals.checkXMLNoTail( element, location, 'dj35' )
                Globals.checkXMLNoAttributes( element, location, 'hs35' )
                Globals.checkXMLNoSubelements( element, location, 'hs32' )
                self.thisBook.appendLine( 'h', clean(hText) )
            elif element.tag == 'toc':
                tocText = element.text
                Globals.checkXMLNoTail( element, location, 'ss13' )
                Globals.checkXMLNoSubelements( element, location, 'js13' )
                level = None
                for attrib,value in element.items():
                    if attrib == 'level': # Seems compulsory
                        level = value
                    else:
                        logging.warning( _("dg36 Unprocessed {} attribute ({}) in {}").format( attrib, value, location ) )
                self.thisBook.appendLine( 'toc'+level, clean(tocText) )
            elif element.tag == 'c':
                Globals.checkXMLNoText( element, location, 'ks35' )
                Globals.checkXMLNoTail( element, location, 'gs35' )
                Globals.checkXMLNoSubelements( element, location, 'kdr3' ) # This is a milestone
                for attrib,value in element.items():
                    if attrib == 'id':
                        C = value
                    else:
                        logging.warning( _("hj52 Unprocessed {} attribute ({}) in {}").format( attrib, value, location ) )
                self.thisBook.appendLine( 'c', C )
            elif element.tag == 's':
                sText = clean( element.text )
                Globals.checkXMLNoTail( element, location, 'wxg0' )
                level = None
                for attrib,value in element.items():
                    if attrib == 'level': # Seems optional
                        level = value
                    else:
                        logging.warning( _("bdy6 Unprocessed {} attribute ({}) in {}").format( attrib, value, location ) )
                marker = 's'
                if level: marker += level
                self.thisBook.appendLine( marker, sText )
                for subelement in element:
                    #print( "subelement", repr(subelement.tag) )
                    sublocation = subelement.tag + " of " + location
                    if subelement.tag == 'f':
                        self.loadFootnote( subelement, sublocation )
                    elif subelement.tag == 'x':
                        self.loadCrossreference( subelement, sublocation )
                    elif subelement.tag == 'fig':
                        self.loadFigure( subelement, sublocation )
                    elif subelement.tag == 'table':
                        self.loadTable( subelement, sublocation )
                    elif subelement.tag in ('add','it','bd','bdit','sc',):
                        self.loadCharacterFormatting( subelement, sublocation )
                    elif subelement.tag == 'optionalLineBreak':
                        print( "What is loadBook optionalLineBreak?" )
                    else:
                        logging.warning( _("jx9q Unprocessed {} element after {} {}:{} in {}").format( subelement.tag, BBB, C, V, sublocation ) )
            elif element.tag in ('p','q',):
                self.loadParagraph( element, location, C )
            elif element.tag == 'b':
                Globals.checkXMLNoText( element, location, 'ks35' )
                Globals.checkXMLNoTail( element, location, 'gs35' )
                Globals.checkXMLNoAttributes( element, location, 'nd04' )
                Globals.checkXMLNoSubelements( element, location, 'kdr3' )
                self.thisBook.appendLine( 'b', '' )
            elif element.tag in ('d','cl',): # Simple single-line paragraph-level markers
                marker, text = element.tag, clean(element.text)
                Globals.checkXMLNoTail( element, location, 'od01' )
                Globals.checkXMLNoAttributes( element, location, 'us91' )
                Globals.checkXMLNoSubelements( element, location, 'gd92' )
                self.thisBook.appendLine( marker, text )
            elif element.tag == 'table':
                self.loadTable( element, location )
            else:
                logging.warning( _("caf2 Unprocessed {} element after {} {}:{} in {}").format( element.tag, BBB, C, V, location ) )
                #self.addPriorityError( 1, c, v, _("Unprocessed {} element").format( element.tag ) )
        self.saveBook( self.thisBook )
    # end of USFXXMLBible.loadBook


    def loadParagraph( self, paragraphElement, paragraphLocation, C ):
        """
        Load the paragraph (p or q) container from the XML data file.
        """
        if Globals.verbosityLevel > 3:
            print( _("USFXXMLBible.loadParagraph: Loading {} from {}...").format( self.name, self.sourceFolder ) )

        V = None
        pText = paragraphElement.text
        Globals.checkXMLNoTail( paragraphElement, paragraphLocation, 'vsg7' )

        # Process the attributes first
        sfm = level = style = None
        for attrib,value in paragraphElement.items():
            if attrib == 'sfm':
                sfm = value
            elif attrib == 'level':
                level = value
            elif attrib == 'style':
                style = value
            else:
                logging.warning( "vfh4 Unprocessed {} attribute ({}) in {}".format( attrib, value, paragraphLocation ) )

        for element in paragraphElement:
            location = element.tag + " of " + paragraphLocation
            #print( "element", repr(element.tag) )
            if element.tag == 'v': # verse milestone
                vTail = clean( element.tail ) # Main verse text
                Globals.checkXMLNoText( element, location, 'crc2' )
                Globals.checkXMLNoSubelements( element, location, 'lct3' )
                lastV, V = V, None
                for attrib,value in element.items():
                    if attrib == 'id':
                        V = value
                    else:
                        logging.warning( _("cbs2 Unprocessed {} attribute ({}) in {}").format( attrib, value, location ) )
                assert( V is not None )
                assert( V )
                self.thisBook.appendLine( 'v', V + ((' '+vTail) if vTail else '' ) )
            elif element.tag == 've': # verse end milestone -- we can just ignore this
                Globals.checkXMLNoText( element, location, 'lsc3' )
                Globals.checkXMLNoTail( element, location, 'mfy4' )
                Globals.checkXMLNoAttributes( element, location, 'ld02' )
                Globals.checkXMLNoSubelements( element, location, 'ls13' )
            elif element.tag == 'fig':
                self.loadFigure( element, location )
            elif element.tag == 'table':
                self.loadTable( element, location )
            elif element.tag == 'f':
                self.loadFootnote( element, location )
            elif element.tag == 'x':
                self.loadCrossreference( element, location )
            elif element.tag in ('add','nd','wj','rq','sig','sls','bk','k','tl','vp','pn','qs','qt','em','it','bd','bdit','sc','no',): # character formatting
                self.loadCharacterFormatting( element, location )
            elif element.tag == 'cs': # character style -- seems like a USFX hack
                text, tail = clean(element.text), clean(element.tail)
                Globals.checkXMLNoSubelements( element, location, 'kf92' )
                sfm = None
                for attrib,value in element.items():
                    if attrib == 'sfm': sfm = value
                    else:
                        logging.warning( _("sh29 Unprocessed {} attribute ({}) in {}").format( attrib, value, location ) )
                if sfm not in ('w','ior',): print( "cs sfm got", repr(sfm) )
                self.thisBook.appendToLastLine( ' \\{} {}\\{}*{}'.format( sfm, text, sfm, (' '+tail) if tail else '' ) )
            elif element.tag in ('cp',): # Simple single-line paragraph-level markers
                marker, text = element.tag, clean(element.text)
                Globals.checkXMLNoTail( element, location, 'kdf0' )
                Globals.checkXMLNoAttributes( element, location, 'lkj1' )
                Globals.checkXMLNoSubelements( element, location, 'da13' )
                self.thisBook.appendLine( marker, text )
            elif element.tag == 'optionalLineBreak':
                print( "What is loadParagraph optionalLineBreak?" )
            elif element.tag == 'milestone':
                print( "What is loadParagraph milestone?" )
            else:
                logging.warning( _("df45 Unprocessed {} element after {} {}:{} in {}").format( repr(element.tag), self.thisBook.bookReferenceCode, C, V, location ) )
    # end of USFXXMLBible.loadParagraph


    def loadCharacterFormatting( self, element, location ):
        """
        """
        marker, text, tail = element.tag, clean(element.text), clean(element.tail)
        Globals.checkXMLNoAttributes( element, location, 'sd12' )
        Globals.checkXMLNoSubelements( element, location, 'la14' )
        self.thisBook.appendToLastLine( ' \\{} {}\\{}*{}'.format( marker, text, marker, (' '+tail) if tail else '' ) )
    # end of USFXXMLBible.loadCharacterFormatting


    def loadFigure( self, element, location ):
        """
        """
        Globals.checkXMLNoText( element, location, 'ff36' )
        Globals.checkXMLNoAttributes( element, location, 'cf35' )
        figDict = { 'description':'', 'catalog':'', 'size':'', 'location':'', 'copyright':'', 'caption':'', 'reference':'' }
        for subelement in element:
            sublocation = subelement.tag + " of " + location
            figTag, figText = subelement.tag, clean(subelement.text)
            assert( figTag in figDict )
            figDict[figTag] = '' if figText is None else figText
            Globals.checkXMLNoTail( subelement, sublocation, 'ld02' )
            Globals.checkXMLNoAttributes( subelement, sublocation, 'ld02' )
            Globals.checkXMLNoSubelements( subelement, sublocation, 'ls13' )
        newString = ''
        for j,tag in enumerate( ('description', 'catalog', 'size', 'location', 'copyright', 'caption', 'reference',) ):
            newString += ('' if j==0 else '|') + figDict[tag]
        figTail = clean( element.tail )
        self.thisBook.appendToLastLine( ' \\fig {}\\fig*{}'.format( newString, (' '+figTail) if figTail else '' ) )
    # end of USFXXMLBible.loadFigure


    def loadTable( self, element, location ):
        """
        """
        Globals.checkXMLNoText( element, location, 'kg92' )
        Globals.checkXMLNoTail( element, location, 'ka92' )
        Globals.checkXMLNoAttributes( element, location, 'ks63' )
        for subelement in element:
            sublocation = subelement.tag + " of " + location
            if subelement.tag == 'tr':
                #print( "table", sublocation )
                self.thisBook.appendLine( 'tr', '' )
                Globals.checkXMLNoText( subelement, sublocation, 'sg32' )
                Globals.checkXMLNoTail( subelement, sublocation, 'dh82' )
                Globals.checkXMLNoAttributes( subelement, sublocation, 'mniq' )
                for sub2element in subelement:
                    sub2location = sub2element.tag + " of " + sublocation
                    tag, text = sub2element.tag, clean(sub2element.text)
                    assert( tag in ('th', 'thr', 'tc', 'tcr',) )
                    Globals.checkXMLNoTail( sub2element, sub2location, 'ah82' )
                    Globals.checkXMLNoSubelements( sub2element, sub2location, 'ka63' )
                    level = None
                    for attrib,value in sub2element.items():
                        if attrib == 'level': level = value
                        else:
                            logging.warning( _("vx25 Unprocessed {} attribute ({}) in {}").format( attrib, value, location ) )
                    marker = tag + (level if level else '')
                    self.thisBook.appendToLastLine( ' \\{} {}'.format( marker, text ) )
            else:
                logging.warning( _("kv64 Unprocessed {} element after {} {}:{} in {}").format( subelement.tag, self.thisBook.bookReferenceCode, C, V, sublocation ) )
    # end of USFXXMLBible.loadTable


    def loadFootnote( self, element, location ):
        """
        """
        text, tail = clean(element.text), clean(element.tail)
        caller = None
        for attrib,value in element.items():
            if attrib == 'caller':
                caller = value
            else:
                logging.warning( _("dg35 Unprocessed {} attribute ({}) in {}").format( attrib, value, location ) )
        self.thisBook.appendToLastLine( ' \\f {}{}'.format( caller, (' '+text) if text else '' ) )
        for subelement in element:
            sublocation = subelement.tag + " of " + location
            marker, fText, fTail = subelement.tag, clean(subelement.text), clean(subelement.tail)
            #print( marker )
            if Globals.debugFlag: assert( marker in ('fr','ft','fq','fv','fk','fqa','it','bd','rq',) )
            Globals.checkXMLNoAttributes( subelement, sublocation, 'ld02' )
            Globals.checkXMLNoSubelements( subelement, sublocation, 'ls13' )
            if marker[0] == 'f' and not fTail:
                #print( "tail", repr(fTail) )
                #Globals.checkXMLNoTail( subelement, sublocation, 'csf3' )
                self.thisBook.appendToLastLine( ' \\{} {}'.format( marker, fText ) )
            else: # it's a regular formatting marker
                self.thisBook.appendToLastLine( ' \\{} {}\\{}*{}'.format( marker, fText, marker, (' '+fTail) if fTail else '' ) )
        self.thisBook.appendToLastLine( '\\f*{}'.format( (' '+tail) if tail else '' ) )
    # end of USFXXMLBible.loadFootnote


    def loadCrossreference( self, element, location ):
        """
        """
        text, tail = clean(element.text), clean(element.tail)
        caller = None
        for attrib,value in element.items():
            if attrib == 'caller':
                caller = value
            else:
                logging.warning( _("fhj2 Unprocessed {} attribute ({}) in {}").format( attrib, value, location ) )
        self.thisBook.appendToLastLine( ' \\x {}'.format( caller ) )
        for subelement in element:
            sublocation = subelement.tag + " of " + location
            marker, xText, xTail = subelement.tag, clean(subelement.text), clean(subelement.tail)
            assert( marker in ('xo','xt',) )
            Globals.checkXMLNoAttributes( subelement, sublocation, 'sc35' )
            Globals.checkXMLNoSubelements( subelement, sublocation, 's1sd' )
            if marker[0] == 'x':
                Globals.checkXMLNoTail( subelement, sublocation, 'la31' )
                self.thisBook.appendToLastLine( ' \\{} {}'.format( marker, xText ) )
            else: # it's a regular formatting marker
                halt
                self.thisBook.appendToLastLine( ' \\{} {}\\{}*{}'.format( marker, xText, marker, (' '+xTail) if xTail else '' ) )
        self.thisBook.appendToLastLine( '\\x*{}'.format( (' '+tail) if tail else '' ) )
    #end of USFXXMLBible.loadCrossreference
# end of class USFXXMLBible



def demo():
    """
    Demonstrate reading and checking some Bible databases.
    """
    if Globals.verbosityLevel > 0: print( ProgNameVersion )

    testData = (
                ("AGM", "../../../../../Data/Work/Bibles/USFX Bibles/Haiola USFX test versions/agm_usfx/",),
                ) # You can put your USFX test folder here

    for name, testFolder in testData:
        if os.access( testFolder, os.R_OK ):
            UB = USFXXMLBible( testFolder, name )
            UB.load()
            if Globals.verbosityLevel > 0: print( UB )
            if Globals.strictCheckingFlag: UB.check()
            if Globals.commandLineOptions.export: UB.doAllExports()
            #UBErrors = UB.getErrors()
            # print( UBErrors )
            #print( UB.getVersification () )
            #print( UB.getAddedUnits () )
            #for ref in ('GEN','Genesis','GeNeSiS','Gen','MrK','mt','Prv','Xyz',):
                ##print( "Looking for", ref )
                #print( "Tried finding '{}' in '{}': got '{}'".format( ref, name, UB.getXRefBBB( ref ) ) )
        else: print( "Sorry, test folder '{}' is not readable on this computer.".format( testFolder ) )

    #if Globals.commandLineOptions.export:
    #    if Globals.verbosityLevel > 0: print( "NOTE: This is {} V{} -- i.e., not even alpha quality software!".format( ProgName, ProgVersion ) )
    #       pass


if __name__ == '__main__':
    # Configure basic set-up
    parser = Globals.setup( ProgName, ProgVersion )
    Globals.addStandardOptionsAndProcess( parser, exportAvailable=True )

    multiprocessing.freeze_support() # Multiprocessing support for frozen Windows executables

    demo()

    Globals.closedown( ProgName, ProgVersion )
# end of USFXXMLBible.py