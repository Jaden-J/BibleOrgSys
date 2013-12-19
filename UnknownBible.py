#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# UnknownBible.py
#   Last modified: 2013-12-19 (also update ProgVersion below)
#
# Module handling a unknown Bible object
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
Module handling an unknown Bible object.

Given a folder name, analyses the files in it
    and tries to determine what type of Bible it probably contains (if any).

Currently aware of the following Bible types:
    USFM
    Unbound Bible (table based), theWord (line based), MySword (SQLite based), e-Sword (SQLite based)
    OSIS, USX, USFX, OpenSong, Zefania, Haggai (all XML)
    Sword modules (binary).
"""

ProgName = "Unknown Bible object handler"
ProgVersion = "0.12"
ProgNameVersion = "{} v{}".format( ProgName, ProgVersion )

debuggingThisModule = False


import logging, os.path
from gettext import gettext as _

import Globals
#from USFMFilenames import USFMFilenames
#from USXFilenames import USXFilenames

from USFMBible import USFMBibleFileCheck, USFMBible
from USXXMLBible import USXXMLBibleFileCheck, USXXMLBible
from USFXXMLBible import USFXXMLBibleFileCheck, USFXXMLBible
from OpenSongXMLBible import OpenSongXMLBibleFileCheck, OpenSongXMLBible
from OSISXMLBible import OSISXMLBibleFileCheck, OSISXMLBible
from ZefaniaXMLBible import ZefaniaXMLBibleFileCheck, ZefaniaXMLBible
from HaggaiXMLBible import HaggaiXMLBibleFileCheck, HaggaiXMLBible
from UnboundBible import UnboundBibleFileCheck, UnboundBible
from TheWordBible import TheWordBibleFileCheck, TheWordBible
from MySwordBible import MySwordBibleFileCheck, MySwordBible
from ESwordBible import ESwordBibleFileCheck, ESwordBible
from YETBible import YETBibleFileCheck, YETBible
from PalmDBBible import PalmDBBibleFileCheck, PalmDBBible
#from SwordResources import SwordInterface # What about these?



class UnknownBible:
    """
    Class for handling an entire Bible.
    """

    def __init__( self, givenFolderName ):
        """
        Constructor: creates an empty Bible object.
        """
        if Globals.debugFlag: assert( givenFolderName and isinstance( givenFolderName, str ) )
        self.givenFolderName = givenFolderName

        # Check that the given folder is readable
        if not os.access( givenFolderName, os.R_OK ):
            logging.critical( _("UnknownBible: Given '{}' folder is unreadable").format( self.givenFolderName ) )
            if Globals.debugFlag and debuggingThisModule: halt
            self.folderReadable = False
        else: self.folderReadable = True

        self.foundType = None
    # end of UnknownBible.__init__


    def __str__( self ):
        """
        This method returns the string representation of a Bible.

        @return: the name of a Bible object formatted as a string
        @rtype: string
        """
        result = _("Unknown Bible object")
        result += ('\n' if result else '') + "  " + _("Folder: {}{}").format( self.givenFolderName, '' if self.folderReadable else ' UNREADABLE' )
        if self.foundType: result += ('\n' if result else '') + "  " + _("Type: {} ").format( self.foundType )
        return result
    # end of UnknownBible.__str__


    def search( self, strictCheck=True, autoLoad=False ):
        """
        Search our folder to found what if any Bible versions can be found.

        These searches are best done in a certain order to avoid false detections.
        """
        if not self.folderReadable: return None

        totalBibleCount, totalBibleTypes, typesFound = 0, 0, []

        # Search for TheWord Bibles
        theWordBibleCount = TheWordBibleFileCheck( self.givenFolderName, strictCheck=strictCheck )
        if theWordBibleCount:
            totalBibleCount += theWordBibleCount
            totalBibleTypes += 1
            typesFound.append( 'theWord' )
            if Globals.verbosityLevel > 2: print( "TheWordBible.search: theWordBibleCount", theWordBibleCount )

        # Search for MySword Bibles
        MySwordBibleCount = MySwordBibleFileCheck( self.givenFolderName, strictCheck=strictCheck )
        if MySwordBibleCount:
            totalBibleCount += MySwordBibleCount
            totalBibleTypes += 1
            typesFound.append( 'MySword' )
            if Globals.verbosityLevel > 2: print( "MySwordBible.search: MySwordBibleCount", MySwordBibleCount )

        # Search for e-Sword Bibles
        ESwordBibleCount = ESwordBibleFileCheck( self.givenFolderName, strictCheck=strictCheck )
        if ESwordBibleCount:
            totalBibleCount += ESwordBibleCount
            totalBibleTypes += 1
            typesFound.append( 'e-Sword' )
            if Globals.verbosityLevel > 2: print( "ESwordBible.search: ESwordBibleCount", ESwordBibleCount )

        # Search for Unbound Bibles
        UnboundBibleCount = UnboundBibleFileCheck( self.givenFolderName, strictCheck=strictCheck )
        if UnboundBibleCount:
            totalBibleCount += UnboundBibleCount
            totalBibleTypes += 1
            typesFound.append( 'Unbound' )
            if Globals.verbosityLevel > 2: print( "UnknownBible.search: UnboundBibleCount", UnboundBibleCount )

        # Search for USFM Bibles
        USFMBibleCount = USFMBibleFileCheck( self.givenFolderName, strictCheck=strictCheck )
        if USFMBibleCount:
            totalBibleCount += USFMBibleCount
            totalBibleTypes += 1
            typesFound.append( 'USFM' )
            if Globals.verbosityLevel > 2: print( "UnknownBible.search: USFMBibleCount", USFMBibleCount )

        # Search for USX XML Bibles
        USXBibleCount = USXXMLBibleFileCheck( self.givenFolderName, strictCheck=strictCheck )
        if USXBibleCount:
            totalBibleCount += USXBibleCount
            totalBibleTypes += 1
            typesFound.append( 'USX' )
            if Globals.verbosityLevel > 2: print( "UnknownBible.search: USXBibleCount", USXBibleCount )

        # Search for USFX XML Bibles
        USFXBibleCount = USFXXMLBibleFileCheck( self.givenFolderName, strictCheck=strictCheck )
        if USFXBibleCount:
            totalBibleCount += USFXBibleCount
            totalBibleTypes += 1
            typesFound.append( 'USFX' )
            if Globals.verbosityLevel > 2: print( "UnknownBible.search: USFXBibleCount", USFXBibleCount )

        # Search for OSIS XML Bibles
        OSISBibleCount = OSISXMLBibleFileCheck( self.givenFolderName, strictCheck=strictCheck )
        if OSISBibleCount:
            totalBibleCount += OSISBibleCount
            totalBibleTypes += 1
            typesFound.append( 'OSIS' )
            if Globals.verbosityLevel > 2: print( "UnknownBible.search: OSISBibleCount", OSISBibleCount )

        # Search for OpenSong XML Bibles
        OpenSongBibleCount = OpenSongXMLBibleFileCheck( self.givenFolderName, strictCheck=strictCheck )
        if OpenSongBibleCount:
            totalBibleCount += OpenSongBibleCount
            totalBibleTypes += 1
            typesFound.append( 'OpenSong' )
            if Globals.verbosityLevel > 2: print( "UnknownBible.search: OpenSongBibleCount", OpenSongBibleCount )

        # Search for Zefania XML Bibles
        ZefaniaBibleCount = ZefaniaXMLBibleFileCheck( self.givenFolderName, strictCheck=strictCheck )
        if ZefaniaBibleCount:
            totalBibleCount += ZefaniaBibleCount
            totalBibleTypes += 1
            typesFound.append( 'Zefania' )
            if Globals.verbosityLevel > 2: print( "UnknownBible.search: ZefaniaBibleCount", ZefaniaBibleCount )

        # Search for Haggai XML Bibles
        HaggaiBibleCount = HaggaiXMLBibleFileCheck( self.givenFolderName, strictCheck=strictCheck )
        if HaggaiBibleCount:
            totalBibleCount += HaggaiBibleCount
            totalBibleTypes += 1
            typesFound.append( 'Haggai' )
            if Globals.verbosityLevel > 2: print( "UnknownBible.search: HaggaiBibleCount", HaggaiBibleCount )

        # Search for YET Bibles
        YETBibleCount = YETBibleFileCheck( self.givenFolderName, strictCheck=strictCheck )
        if YETBibleCount:
            totalBibleCount += YETBibleCount
            totalBibleTypes += 1
            typesFound.append( 'YET' )
            if Globals.verbosityLevel > 2: print( "UnknownBible.search: YETBibleCount", YETBibleCount )

        # Search for PalmDB Bibles
        PDBBibleCount = PalmDBBibleFileCheck( self.givenFolderName, strictCheck=strictCheck )
        if PDBBibleCount:
            totalBibleCount += PDBBibleCount
            totalBibleTypes += 1
            typesFound.append( 'PalmDB' )
            if Globals.verbosityLevel > 2: print( "UnknownBible.search: PDBBibleCount", PDBBibleCount )


        assert( len(typesFound) == totalBibleTypes )
        if totalBibleCount == 0:
            if Globals.verbosityLevel > 0: print( "UnknownBible.search: No Bibles found" )
            self.foundType = 'None found'
        elif totalBibleCount > 1:
            if totalBibleTypes == 1:
                if Globals.verbosityLevel > 0:
                    print( "UnknownBible.search: Multiple ({}) {} Bibles found".format( totalBibleCount, typesFound[0] ) )
            else:
                if Globals.verbosityLevel > 0:
                    print( "UnknownBible.search: Multiple ({}) Bibles found: {}".format( totalBibleCount, typesFound ) )
                self.foundType = 'Many found'

        # Put the binary formats first here
        elif theWordBibleCount == 1:
            self.foundType = "theWord Bible"
            if autoLoad: return TheWordBibleFileCheck( self.givenFolderName, strictCheck=strictCheck, autoLoad=autoLoad )
            else: return self.foundType, theWordBibleCount
        elif MySwordBibleCount == 1:
            self.foundType = "MySword Bible"
            if autoLoad: return MySwordBibleFileCheck( self.givenFolderName, strictCheck=strictCheck, autoLoad=autoLoad )
            else: return self.foundType, MySwordBibleCount
        elif ESwordBibleCount == 1:
            self.foundType = "e-Sword Bible"
            if autoLoad: return ESwordBibleFileCheck( self.givenFolderName, strictCheck=strictCheck, autoLoad=autoLoad )
            else: return self.foundType, ESwordBibleCount
        elif PDBBibleCount == 1:
            self.foundType = "PalmDB Bible"
            if autoLoad: return PalmDBBibleFileCheck( self.givenFolderName, strictCheck=strictCheck, autoLoad=autoLoad )
            else: return self.foundType, PDBBibleCount
        elif UnboundBibleCount == 1:
            self.foundType = "Unbound Bible"
            if autoLoad: return UnboundBibleFileCheck( self.givenFolderName, strictCheck=strictCheck, autoLoad=autoLoad )
            else: return self.foundType, UnboundBibleCount
        elif USFMBibleCount == 1:
            self.foundType = "USFM Bible"
            if autoLoad: return USFMBibleFileCheck( self.givenFolderName, strictCheck=strictCheck, autoLoad=autoLoad )
            else: return self.foundType, USFMBibleCount
        elif USXBibleCount == 1:
            self.foundType = "USX XML Bible"
            if autoLoad: return USXXMLBibleFileCheck( self.givenFolderName, strictCheck=strictCheck, autoLoad=autoLoad )
            else: return self.foundType, USXBibleCount
        elif USFXBibleCount == 1:
            self.foundType = "USFX XML Bible"
            if autoLoad: return USFXXMLBibleFileCheck( self.givenFolderName, strictCheck=strictCheck, autoLoad=autoLoad )
            else: return self.foundType, USFXBibleCount
        elif OSISBibleCount == 1:
            self.foundType = "OSIS XML Bible"
            if autoLoad: return OSISXMLBibleFileCheck( self.givenFolderName, strictCheck=strictCheck, autoLoad=autoLoad )
            else: return self.foundType, OSISBibleCount
        elif OpenSongBibleCount == 1:
            self.foundType = "OpenSong XML Bible"
            if autoLoad: return OpenSongXMLBibleFileCheck( self.givenFolderName, strictCheck=strictCheck, autoLoad=autoLoad )
            else: return self.foundType, OpenSongBibleCount
        elif ZefaniaBibleCount == 1:
            self.foundType = "Zefania XML Bible"
            if autoLoad: return ZefaniaXMLBibleFileCheck( self.givenFolderName, strictCheck=strictCheck, autoLoad=autoLoad )
            else: return self.foundType, ZefaniaBibleCount
        elif HaggaiBibleCount == 1:
            self.foundType = "Haggai XML Bible"
            if autoLoad: return HaggaiXMLBibleFileCheck( self.givenFolderName, strictCheck=strictCheck, autoLoad=autoLoad )
            else: return self.foundType, HaggaiBibleCount
        elif YETBibleCount == 1:
            self.foundType = "YET Bible"
            if autoLoad: return YETBibleFileCheck( self.givenFolderName, strictCheck=strictCheck, autoLoad=autoLoad )
            else: return self.foundType, YETBibleCount
    # end of UnknownBible.search
# end of class UnknownBible



def demo():
    """
    Main program to handle command line parameters and then run what they want.
    """
    if Globals.verbosityLevel > 0: print( "{} V{}".format(ProgName, ProgVersion ) )

    # Now demo the class
    testFolders = ( #"/home/robert/Logs",
                    #"../../../../../Data/Work/Bibles/theWord modules/",
                    #"../../../../../Data/Work/Bibles/Biola Unbound modules/",
                    #"../../../../../Data/Work/Bibles/OpenSong Bibles/",
                    #"../../../../../Data/Work/Bibles/Zefania modules/",
                    #"../../../../../Data/Work/Bibles/YET modules/",
                    #"../../../../../Data/Work/Matigsalug/Bible/MBTV/",
                    #"../../../../../SSD/AutoProcesses/Processed/",
                    #"Tests/DataFilesForTests/USFMTest1/", "Tests/DataFilesForTests/USFMTest2/",
                    #"Tests/DataFilesForTests/USFM-OEB/", "Tests/DataFilesForTests/USFM-WEB/",
                    #"Tests/DataFilesForTests/USXTest1/", "Tests/DataFilesForTests/USXTest2/",
                    #"Tests/DataFilesForTests/USFXTest1/", "Tests/DataFilesForTests/USFXTest2/",
                    #"Tests/DataFilesForTests/USFX-ASV/", "Tests/DataFilesForTests/USFX-WEB/",
                    #"Tests/DataFilesForTests/OSISTest1/", "Tests/DataFilesForTests/OSISTest2/",
                    #"Tests/DataFilesForTests/ZefaniaTest/", "Tests/DataFilesForTests/HaggaiTest/",
                    #"Tests/DataFilesForTests/theWordTest/", "Tests/DataFilesForTests/MySwordTest/",
                    "Tests/DataFilesForTests/YETTest/", "Tests/DataFilesForTests/PDBTest/",
                    #"Tests/DataFilesForTests/", # Up a level
                    )
    if 1: # Just find the files
        for j, testFolder in enumerate( testFolders ):
            if Globals.verbosityLevel > 0: print( "\n\nUnknownBible A{}/ Trying {}...".format( j+1, testFolder ) )
            B = UnknownBible( testFolder )
            #print( B )
            result = B.search( autoLoad=False )
            #result2 = B.search( autoLoad=True ) if result1 else None
            if Globals.verbosityLevel > 2: print( "  Result is: {}".format( result ) )
            if Globals.verbosityLevel > 0: print( B )

    if 1: # Just load the files
        for j, testFolder in enumerate( testFolders ):
            if Globals.verbosityLevel > 0: print( "\n\nUnknownBible B{}/ Loading {}...".format( j+1, testFolder ) )
            B = UnknownBible( testFolder )
            #print( B )
            #result1 = B.search( autoLoad=False )
            result = B.search( autoLoad=True )
            if Globals.verbosityLevel > 2: print( "  Result is: {}".format( result ) )
            if Globals.verbosityLevel > 0: print( B )

    if 1: # Load, check, and export the files
        for j, testFolder in enumerate( testFolders ):
            if Globals.verbosityLevel > 0: print( "\n\nUnknownBible C{}/ Processing {}...".format( j+1, testFolder ) )
            B = UnknownBible( testFolder )
            #print( B )
            result = B.search( autoLoad=True )
            #result2 = B.search( autoLoad=True ) if result1 else None
            #if Globals.verbosityLevel > 2: print( "  Results are: {} and {}".format( result1, result2 ) )
            if Globals.verbosityLevel > 0: print( B )
            if result:
                result.check()
                results = result.doAllExports()
                if Globals.verbosityLevel > 2: print( "  Results are: {}".format( results ) )
# end of demo


if __name__ == '__main__':
    # Configure basic set-up
    parser = Globals.setup( ProgName, ProgVersion )
    Globals.addStandardOptionsAndProcess( parser )

    demo()

    Globals.closedown( ProgName, ProgVersion )
# end of UnknownBible.py