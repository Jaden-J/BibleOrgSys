#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# YETBible.py
#   Last modified: 2013-12-19 by RJH (also update ProgVersion below)
#
# Module handling YET Bible files
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
Module reading and loading YET Bible files.

e.g.,
    info    shortName       KJV
    info    longName        King James Version
    info    description     King James Version (1611 Authorized Version)
    info    locale  en
    book_name       1       Genesis
    book_name       2       Exodus
    ...
    verse   1       1       1       In the beginning God created the heaven and the earth.
    verse   1       1       2       @@And the earth was without form, and void; and darkness @9was@7 upon the face of the deep. And the Spirit of God moved upon the face of the waters.
    verse   1       1       3       And God said, Let there be light: and there was light.
    verse   1       1       4       @@And God saw the light, that @9it was@7 good: and God divided the light from the darkness.
    verse   1       1       5       And God called the light Day, and the darkness he called Night. And the evening and the morning were the first day.
    verse   1       1       6       @@@^And God said, Let there be a firmament in the midst of the waters, and let it divide the waters from the waters.
    ...
Plus optional
    xref    40      1       23      1       @<ta:1443598@>Mrk. 7:14@/
    xref    40      2       6       1       @<ta:2098435@>Act. 5:2@/
    ...
    footnote        40      1       11      1       1:11 @9word @7Some note about word in Mat 1:11.
    footnote        40      1       16      1       1:16 @9Christ @7Not in all versions.
    ...
Plus optional
    pericope        40      1       1       Heading to precede Mat 1:1 here
    parallel        Luk. 3:23-38
    pericope        40      1       18      Heading2 here
    parallel        Luk. 2:1-7
    parallel        Jhn. 3:2-7
    ...

Limitations:
    Unsure whether italic codes in verse text could just be \it instead of \add
    Currently ignores encoded verse references in cross-references
"""

ProgName = "YET Bible format handler"
ProgVersion = "0.01"
ProgNameVersion = "{} v{}".format( ProgName, ProgVersion )

debuggingThisModule = False


import logging, os, re
from gettext import gettext as _
import multiprocessing
from collections import OrderedDict

import Globals
from Bible import Bible, BibleBook


filenameEndingsToAccept = ('.YET',) # Must be UPPERCASE
#filenameEndingsToIgnore = ('.ZIP.GO', '.ZIP.DATA',) # Must be UPPERCASE
#extensionsToIgnore = ('ZIP', 'BAK', 'LOG', 'HTM','HTML', 'XML', 'OSIS', 'USX', 'STY', 'LDS', 'SSF', 'VRS', 'ASC', 'CSS', 'ODT','DOC','TXT', 'JAR', ) # Must be UPPERCASE



def YETBibleFileCheck( givenFolderName, strictCheck=True, autoLoad=False ):
    """
    Given a folder, search for YET Bible files or folders in the folder and in the next level down.

    Returns False if an error is found.

    if autoLoad is false (default)
        returns None, or the number of Bibles found.

    if autoLoad is true and exactly one YET Bible is found,
        returns the loaded YETBible object.
    """
    if Globals.verbosityLevel > 2: print( "YETBibleFileCheck( {}, {}, {} )".format( givenFolderName, strictCheck, autoLoad ) )
    if Globals.debugFlag: assert( givenFolderName and isinstance( givenFolderName, str ) )
    if Globals.debugFlag: assert( autoLoad in (True,False,) )

    # Check that the given folder is readable
    if not os.access( givenFolderName, os.R_OK ):
        logging.critical( _("YETBibleFileCheck: Given '{}' folder is unreadable").format( givenFolderName ) )
        return False
    if not os.path.isdir( givenFolderName ):
        logging.critical( _("YETBibleFileCheck: Given '{}' path is not a folder").format( givenFolderName ) )
        return False

    # Find all the files and folders in this folder
    if Globals.verbosityLevel > 3: print( " YETBibleFileCheck: Looking for files in given {}".format( givenFolderName ) )
    foundFolders, foundFiles = [], []
    for something in os.listdir( givenFolderName ):
        somepath = os.path.join( givenFolderName, something )
        if os.path.isdir( somepath ): foundFolders.append( something )
        elif os.path.isfile( somepath ):
            somethingUpper = something.upper()
            somethingUpperProper, somethingUpperExt = os.path.splitext( somethingUpper )
            if somethingUpperExt in filenameEndingsToAccept:
                foundFiles.append( something )
    if '__MACOSX' in foundFolders:
        foundFolders.remove( '__MACOSX' )  # don't visit these directories

    # See if there's an YETBible project here in this given folder
    numFound = 0
    lastFilenameFound = None
    for thisFilename in sorted( foundFiles ):
        if thisFilename.endswith( '.yet' ):
            if strictCheck or Globals.strictCheckingFlag:
                firstLine = Globals.peekIntoFile( thisFilename, givenFolderName )
                if not firstLine.startswith( "info\t"):
                    if Globals.verbosityLevel > 2: print( "YETBible (unexpected) first line was '{}' in {}".format( firstLine, thisFilename ) )
                    continue
            lastFilenameFound = thisFilename
            numFound += 1
    if numFound:
        if Globals.verbosityLevel > 2: print( "YETBibleFileCheck got", numFound, givenFolderName, lastFilenameFound )
        if numFound == 1 and autoLoad:
            uB = YETBible( givenFolderName, lastFilenameFound[:-4] ) # Remove the end of the actual filename ".yet"
            uB.load() # Load and process the file
            return uB
        return numFound

    # Look one level down
    numFound = 0
    foundProjects = []
    for thisFolderName in sorted( foundFolders ):
        tryFolderName = os.path.join( givenFolderName, thisFolderName+'/' )
        if not os.access( tryFolderName, os.R_OK ): # The subfolder is not readable
            logging.warning( _("YETBibleFileCheck: '{}' subfolder is unreadable").format( tryFolderName ) )
            continue
        if Globals.verbosityLevel > 3: print( "    YETBibleFileCheck: Looking for files in {}".format( tryFolderName ) )
        foundSubfolders, foundSubfiles = [], []
        for something in os.listdir( tryFolderName ):
            somepath = os.path.join( givenFolderName, thisFolderName, something )
            if os.path.isdir( somepath ): foundSubfolders.append( something )
            elif os.path.isfile( somepath ):
                somethingUpper = something.upper()
                somethingUpperProper, somethingUpperExt = os.path.splitext( somethingUpper )
                if somethingUpperExt in filenameEndingsToAccept:
                    foundSubfiles.append( something )

        # See if there's an YETBible project here in this folder
        for thisFilename in sorted( foundSubfiles ):
            if thisFilename.endswith( '.yet' ):
                if strictCheck or Globals.strictCheckingFlag:
                    firstLine = Globals.peekIntoFile( thisFilename, tryFolderName )
                    if not firstLine.startswith( "info\t"):
                        if Globals.verbosityLevel > 2: print( "YETBible (unexpected) first line was '{}' in {}".format( firstLine, thisFilname ) ); halt
                        continue
                foundProjects.append( (tryFolderName, thisFilename,) )
                lastFilenameFound = thisFilename
                numFound += 1
    if numFound:
        if Globals.verbosityLevel > 2: print( "YETBibleFileCheck foundProjects", numFound, foundProjects )
        if numFound == 1 and autoLoad:
            if Globals.debugFlag: assert( len(foundProjects) == 1 )
            uB = YETBible( foundProjects[0][0], foundProjects[0][1][:-9] ) # Remove the end of the actual filename "_utf8.txt"
            uB.load() # Load and process the file
            return uB
        return numFound
# end of YETBibleFileCheck



class YETBible( Bible ):
    """
    Class for reading, validating, and converting YETBible files.
    """
    def __init__( self, sourceFolder, givenName, encoding='utf-8' ):
        """
        Constructor: just sets up the Bible object.
        """
         # Setup and initialise the base class first
        Bible.__init__( self )
        self.objectNameString = "YET Bible object"
        self.objectTypeString = "YET"

        # Now we can set our object variables
        self.sourceFolder, self.givenName, self.encoding = sourceFolder, givenName, encoding
        self.sourceFilepath =  os.path.join( self.sourceFolder, self.givenName+'.yet' )

        # Do a preliminary check on the readability of our file
        if not os.access( self.sourceFilepath, os.R_OK ):
            logging.critical( _("YETBible: File '{}' is unreadable").format( self.sourceFilepath ) )

        self.name = self.givenName
        #if self.name is None:
            #pass
    # end of YETBible.__init__


    def load( self ):
        """
        Load a single source file and load book elements.
        """
        if Globals.verbosityLevel > 2: print( _("Loading {}...").format( self.sourceFilepath ) )

        def decodeVerse( encodedVerseString ):
            """
            Decodes the verse which has @ format codes.
            """
            verseString = encodedVerseString
            if verseString.startswith( '@@' ): # This simply means that encoding follows
                verseString = verseString[2:]
            if verseString.startswith( '@@' ): # This simply means that encoding follows
                verseString = verseString[2:]
            # Paragraph markers (marked now with double backslash)
            verseString = verseString.replace( '@^', '\\\\p ' )
            verseString = verseString.replace( '@0', '\\\\m ' )
            verseString = verseString.replace( '@1', '\\\\q1 ' ).replace( '@2', '\\\\q2 ' ).replace( '@3', '\\\\q3 ' ).replace( '@4', '\\q4 ' )
            verseString = verseString.replace( '@8', '\\\\m ' )
            # Character markers (marked now with single backslash)
            verseString = verseString.replace( '@6', '\\wj ' ).replace( '@5', '\\wj*' )
            verseString = verseString.replace( '@9', '\\add ' ).replace( '@7', '\\add*' ) # or \\i ???
            verseString = re.sub( r'@<f([0-9])@>@/', r'\\ff\1', verseString )
            verseString = re.sub( r'@<x([0-9])@>@/', r'\\xx\1', verseString )
            #print( repr( verseString ) )
            assert( '@' not in verseString )
            return verseString
        # end of decodeVerse

        # Read all the lines into bookDict
        lastLine, lineCount = '', 0
        bookNameDict, bookDict, footnoteDict, xrefDict, headingDict = OrderedDict(), OrderedDict(), {}, {}, {}
        BBB = bookNumberString = chapterNumberString = verseNumberString = encodedVerseString = ''
        lastBBB = lastBookNumberString = lastChapterNumberString = lastVerseNumberString = None
        with open( self.sourceFilepath, encoding=self.encoding ) as myFile: # Automatically closes the file when done
            for line in myFile:
                lineCount += 1
                #if lineCount==1 and self.encoding.lower()=='utf-8' and line[0]==chr(65279): #U+FEFF
                    #logging.info( "      YETBible.load: Detected UTF-16 Byte Order Marker" )
                    #line = line[1:] # Remove the UTF-8 Byte Order Marker
                if line[-1]=='\n': line=line[:-1] # Removing trailing newline character
                if not line: continue # Just discard blank lines
                lastLine = line
                #print ( 'YETBible file line is "' + line + '"' )

                bits = line.split( '\t' )
                #print( self.givenName, BBB, bits )
                if bits[0] == 'info':
                    assert( len(bits) == 3 )
                    if bits[1] == 'shortName':
                        shortName = bits[2]
                        self.name = shortName
                    elif bits[1] == 'longName':
                        longName = bits[2]
                    elif bits[1] == 'description':
                        description = bits[2]
                    elif bits[1] == 'locale':
                        locale = bits[2]
                        assert( 2 <= len(locale) <= 3 )
                        if locale == 'in': locale = 'id' # Fix a quirk in the locale encoding
                    else:
                        logging.warning( _("YETBible: unknown {} info field in {} {} {}:{}") \
                            .format( repr(bits[1]), BBB, bookCode, chapterNumberString, verseNumberString ) )
                    continue
                elif bits[0] == 'book_name':
                    assert( 3 <= len(bits) <= 4 )
                    thisBBB = Globals.BibleBooksCodes.getBBBFromReferenceNumber( bits[1] )
                    if len(bits) == 3:
                        bookNameDict[thisBBB] = bits[2], ''
                    elif len(bits) == 4:
                        bookNameDict[thisBBB] = bits[2], bits[3]
                    continue
                elif bits[0] == 'verse':
                    assert( len(bits) == 5 )
                    bookNumberString, chapterNumberString, verseNumberString, encodedVerseString = bits[1:]
                    if Globals.debugFlag:
                        assert( bookNumberString.isdigit() )
                        assert( chapterNumberString.isdigit() )
                        assert( verseNumberString.isdigit() )
                    BBB = Globals.BibleBooksCodes.getBBBFromReferenceNumber( bookNumberString )
                    #print( "{} {}:{} = {}".format( BBB, chapterNumberString, verseNumberString, repr(encodedVerseString) ) )
                    if BBB != lastBBB: # We have a new book
                        if lastBBB is not None: # We have a completed book to save
                            bookDict[lastBBB] = bookLines
                        assert( BBB in bookNameDict )
                        bookLines = OrderedDict() # Keys are (C,V) strings
                    verseString = decodeVerse( encodedVerseString )
                    bookLines[(chapterNumberString,verseNumberString)] = verseString # Just store it for now
                    lastBBB = BBB
                    continue
                elif bits[0] == 'pericope':
                    assert( len(bits) == 5 )
                    bookNumberString, chapterNumberString, verseNumberString, encodedHeadingString = bits[1:]
                    if Globals.debugFlag:
                        assert( bookNumberString.isdigit() )
                        assert( chapterNumberString.isdigit() )
                        assert( verseNumberString.isdigit() )
                    BBB = Globals.BibleBooksCodes.getBBBFromReferenceNumber( bookNumberString )
                    headingString = encodedHeadingString.replace( '@9', '\\it ' ).replace( '@7', '\\it*' )
                    #print( repr(encodedHeadingString), repr(headingString) )
                    assert( '@' not in headingString )
                    headingDict[(BBB,chapterNumberString,verseNumberString)] = headingString, [] # Blank refList
                    continue
                elif bits[0] == 'parallel': # These lines optionally follow pericope lines
                    assert( len(bits) == 2 )
                    heading, refList = headingDict[(BBB,chapterNumberString,verseNumberString)]
                    refList.append( bits[1] )
                    #print( "parallel2", repr(heading), refList )
                    headingDict[(BBB,chapterNumberString,verseNumberString)] = heading, refList
                    continue
                elif bits[0] == 'xref':
                    assert( len(bits) == 6 )
                    bookNumberString, chapterNumberString, verseNumberString, indexNumberString, encodedNoteString = bits[1:]
                    if Globals.debugFlag:
                        assert( bookNumberString.isdigit() )
                        assert( chapterNumberString.isdigit() )
                        assert( verseNumberString.isdigit() )
                        assert( indexNumberString.isdigit() )
                    BBB = Globals.BibleBooksCodes.getBBBFromReferenceNumber( bookNumberString )
                    noteString = encodedNoteString.replace( '@9', '\\it ' ).replace( '@7', '\\it*' )
                    noteString = re.sub( r'@<ta(.+?)@>', r'', noteString ) # Get rid of these encoded BCV references for now
                    noteString = re.sub( r'@<to(.+?)@>', r'', noteString ) # Get rid of these OSIS BCV references for now
                    noteString = noteString.replace( '@/', '' )
                    #print( repr(encodedNoteString), repr(noteString) )
                    assert( '@' not in noteString )
                    xrefDict[(BBB,chapterNumberString,verseNumberString,indexNumberString)] = noteString
                    continue
                elif bits[0] == 'footnote':
                    assert( len(bits) == 6 )
                    bookNumberString, chapterNumberString, verseNumberString, indexNumberString, encodedNoteString = bits[1:]
                    if Globals.debugFlag:
                        assert( bookNumberString.isdigit() )
                        assert( chapterNumberString.isdigit() )
                        assert( verseNumberString.isdigit() )
                        assert( indexNumberString.isdigit() )
                    BBB = Globals.BibleBooksCodes.getBBBFromReferenceNumber( bookNumberString )
                    noteString = encodedNoteString.replace( '@9', '\\it ' ).replace( '@7', '\\it*' )
                    assert( '@' not in noteString )
                    footnoteDict[(BBB,chapterNumberString,verseNumberString,indexNumberString)] = noteString
                    continue
                else: print( "YETBible: Unknown line type", self.givenName, BBB, bookCode, chapterNumberString, verseNumberString, len(bits), bits ); halt
            bookDict[lastBBB] = bookLines # Save the last book


                #if bookCode != lastBookCode: # We've started a new book
                    #if lastBookCode != -1: # Better save the last book
                        #self.saveBook( thisBook )
                    #BBB = Globals.BibleBooksCodes.getBBBFromYETBibleCode( bookCode )
                    #thisBook = BibleBook( self.name, BBB )
                    #thisBook.objectNameString = "YET Bible Book object"
                    #thisBook.objectTypeString = "YET"
                    #lastBookCode = bookCode
                    #lastChapterNumber = lastVerseNumber = -1

                #if chapterNumber != lastChapterNumber: # We've started a new chapter
                    #if Globals.debugFlag: assert( chapterNumber > lastChapterNumber or BBB=='ESG' ) # Esther Greek might be an exception
                    #if chapterNumber == 0:
                        #logging.info( "Have chapter zero in {} {} {} {}:{}".format( self.givenName, BBB, bookCode, chapterNumberString, verseNumberString ) )
                    #thisBook.appendLine( 'c', chapterNumberString )
                    #lastChapterNumber = chapterNumber
                    #lastVerseNumber = -1

                ## Handle the verse info
                #if verseNumber==lastVerseNumber and vText==lastVText:
                    #logging.warning( _("Ignored duplicate verse line in {} {} {} {}:{}").format( self.givenName, BBB, bookCode, chapterNumberString, verseNumberString ) )
                    #continue
                #if BBB=='PSA' and verseNumberString=='1' and vText.startswith('&lt;') and self.givenName=='basic_english':
                    ## Move Psalm titles to verse zero
                    #verseNumber = 0
                #if verseNumber < lastVerseNumber:
                    #logging.warning( _("Ignored receding verse number (from {} to {}) in {} {} {} {}:{}").format( lastVerseNumber, verseNumber, self.givenName, BBB, bookCode, chapterNumberString, verseNumberString ) )
                #elif verseNumber == lastVerseNumber:
                    #if vText == lastVText:
                        #logging.warning( _("Ignored duplicated {} verse in {} {} {} {}:{}").format( verseNumber, self.givenName, BBB, bookCode, chapterNumberString, verseNumberString ) )
                    #else:
                        #logging.warning( _("Ignored duplicated {} verse number in {} {} {} {}:{}").format( verseNumber, self.givenName, BBB, bookCode, chapterNumberString, verseNumberString ) )
                #thisBook.appendLine( 'v', verseNumberString + ' ' + vText )
                #lastVText = vText
                #lastVerseNumber = verseNumber

        # Now process the books
        for BBB,bkData in bookDict.items():
            #print( "Processing", BBB )
            thisBook = BibleBook( self.name, BBB )
            thisBook.objectNameString = "YET Bible Book object"
            thisBook.objectTypeString = "YET"
            lastChapterNumberString = None
            for (chapterNumberString,verseNumberString), verseString in bkData.items():
                # Insert headings (can only occur before verses)
                if (BBB,chapterNumberString,verseNumberString) in headingDict:
                    heading, refList = headingDict[(BBB,chapterNumberString,verseNumberString)]
                    #print( 's', BBB, chapterNumberString, verseNumberString, repr(heading), refList )
                    thisBook.appendLine( 's', heading )
                    if refList:
                        refString = ""
                        #print( 's', BBB, chapterNumberString, verseNumberString, repr(heading), refList )
                        for ref in refList:
                            refString += ('; ' if refString else '') + ref
                        #print( 's', BBB, chapterNumberString, verseNumberString, repr(heading), refList, repr(refString) )
                        thisBook.appendLine( 'r', '('+refString+')' )
                # Insert footnotes and cross-references
                while( '\\ff' in verseString ):
                    #print( "footnote", repr(verseString) )
                    fIx = verseString.index( '\\ff' )
                    caller = verseString[fIx+3]
                    #print( "fcaller", repr(caller) )
                    assert( caller.isdigit() )
                    note = footnoteDict[(BBB,chapterNumberString,verseNumberString,caller)]
                    #print( "fnote", repr(note) )
                    verseString = verseString[:fIx] + '\\f + \\ft ' + note + '\\f*' + verseString[fIx+4:]
                    #print( "fvS", repr(verseString) )
                while( '\\xx' in verseString ):
                    #print( "xref", repr(verseString) )
                    fIx = verseString.index( '\\xx' )
                    caller = verseString[fIx+3]
                    #print( "xcaller", repr(caller) )
                    assert( caller.isdigit() )
                    note = xrefDict[(BBB,chapterNumberString,verseNumberString,caller)]
                    #print( "xnote", repr(note) )
                    verseString = verseString[:fIx] + '\\x - \\xt ' + note + '\\x*' + verseString[fIx+4:]
                    #print( "xvS", repr(verseString) )
                # Save the Bible data fields
                if chapterNumberString != lastChapterNumberString:
                    thisBook.appendLine( 'c', chapterNumberString )
                    lastChapterNumberString = chapterNumberString
                #print( BBB, chapterNumberString, verseNumberString, repr(verseString) )
                if verseString.startswith( '\\\\' ):  # It's an initial paragraph marker
                    if verseString[3]==' ': marker, verseString = verseString[2], verseString[4:]
                    elif verseString[4]==' ': marker, verseString = verseString[2:4], verseString[5:]
                    else: halt
                    #print( '', '\\'+marker )
                    thisBook.appendLine( marker, '' )
                assert( not verseString.startswith( '\\\\' ) )
                bits = verseString.split( '\\\\' ) # Split on paragraph markers (but not character markers)
                for j,bit in enumerate(bits):
                    #print( "loop", j, repr(bit), repr(verseString) )
                    if j==0: thisBook.appendLine( 'v', verseNumberString + ' ' + verseString.rstrip() )
                    else:
                        if bit[1]==' ': marker, bit = bit[0], bit[2:]
                        elif bit[2]==' ': marker, bit = bit[0:2], bit[3:]
                        else: halt
                        #print( "mV", marker, repr(bit), repr(verseString) )
                        thisBook.appendLine( marker, bit.rstrip() )
            self.saveBook( thisBook )
    # end of YETBible.load
# end of YETBible class



def testYB( TUBfilename ):
    # Crudely demonstrate the YET Bible class
    import VerseReferences
    TUBfolder = "../../../../../Data/Work/Bibles/YET modules/" # Must be the same as below

    if Globals.verbosityLevel > 1: print( _("Demonstrating the YET Bible class...") )
    if Globals.verbosityLevel > 0: print( "  Test folder is '{}' '{}'".format( TUBfolder, TUBfilename ) )
    ub = YETBible( TUBfolder, TUBfilename )
    ub.load() # Load and process the file
    if Globals.verbosityLevel > 1: print( ub ) # Just print a summary
    for reference in ( ('OT','GEN','1','1'), ('OT','GEN','1','3'), ('OT','PSA','3','0'), ('OT','PSA','3','1'), \
                        ('OT','DAN','1','21'),
                        ('NT','MAT','3','5'), ('NT','JDE','1','4'), ('NT','REV','22','21'), \
                        ('DC','BAR','1','1'), ('DC','MA1','1','1'), ('DC','MA2','1','1',), ):
        (t, b, c, v) = reference
        if t=='OT' and len(ub)==27: continue # Don't bother with OT references if it's only a NT
        if t=='NT' and len(ub)==39: continue # Don't bother with NT references if it's only a OT
        if t=='DC' and len(ub)<=66: continue # Don't bother with DC references if it's too small
        svk = VerseReferences.SimpleVerseKey( b, c, v )
        #print( svk, ob.getVerseDataList( reference ) )
        shortText = svk.getShortText()
        try:
            verseText = ub.getVerseText( svk )
        except KeyError:
            verseText = "Verse not available!"
        if Globals.verbosityLevel > 1: print( reference, shortText, verseText )
# end of testYB


def demo():
    """
    Main program to handle command line parameters and then run what they want.
    """
    if Globals.verbosityLevel > 0: print( ProgNameVersion )


    testFolder = "../../../../../Data/Work/Bibles/YET modules/"


    if 1: # demo the file checking code -- first with the whole folder and then with only one folder
        result1 = YETBibleFileCheck( testFolder )
        if Globals.verbosityLevel > 1: print( "YET TestA1", result1 )
        result2 = YETBibleFileCheck( testFolder, autoLoad=True )
        if Globals.verbosityLevel > 1: print( "YET TestA2", result2 )
        #testSubfolder = os.path.join( testFolder, 'kjv/' )
        #result3 = YETBibleFileCheck( testSubfolder )
        #if Globals.verbosityLevel > 1: print( "YET TestB1", result3 )
        #result4 = YETBibleFileCheck( testSubfolder, autoLoad=True )
        #if Globals.verbosityLevel > 1: print( "YET TestB2", result4 )


    if 1: # specified modules
        single = ( "kjv", )
        good = ( "kjv", "kjv-red", "in-tsi", )
        nonEnglish = (  )
        bad = ( )
        for j, testFilename in enumerate( good ): # Choose one of the above: single, good, nonEnglish, bad
            if Globals.verbosityLevel > 1: print( "\nYET C{}/ Trying {}".format( j+1, testFilename ) )
            #myTestFolder = os.path.join( testFolder, testFilename+'/' )
            #testFilepath = os.path.join( testFolder, testFilename+'/', testFilename+'_utf8.txt' )
            testYB( testFilename )


    if 1: # all discovered modules in the test folder
        foundFolders, foundFiles = [], []
        for something in os.listdir( testFolder ):
            somepath = os.path.join( testFolder, something )
            if os.path.isdir( somepath ): foundFolders.append( something )
            elif os.path.isfile( somepath ): foundFiles.append( something )

        if Globals.maxProcesses > 1: # Get our subprocesses ready and waiting for work
            if Globals.verbosityLevel > 1: print( "\nTrying all {} discovered modules...".format( len(foundFolders) ) )
            parameters = [folderName for folderName in sorted(foundFolders)]
            with multiprocessing.Pool( processes=Globals.maxProcesses ) as pool: # start worker processes
                results = pool.map( testYB, parameters ) # have the pool do our loads
                assert( len(results) == len(parameters) ) # Results (all None) are actually irrelevant to us here
        else: # Just single threaded
            for j, someFolder in enumerate( sorted( foundFolders ) ):
                if Globals.verbosityLevel > 1: print( "\nYET D{}/ Trying {}".format( j+1, someFolder ) )
                #myTestFolder = os.path.join( testFolder, someFolder+'/' )
                testYB( someFolder )
# end of demo


if __name__ == '__main__':
    # Configure basic set-up
    parser = Globals.setup( ProgName, ProgVersion )
    Globals.addStandardOptionsAndProcess( parser )

    multiprocessing.freeze_support() # Multiprocessing support for frozen Windows executables

    demo()

    Globals.closedown( ProgName, ProgVersion )
# end of YETBible.py