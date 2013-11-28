#!/usr/bin/env python

# File for packaging MATLAB and C++ software for the web.

import os
import sys
import re
import shutil
import time
import string
import glob
import datetime
import posix

sys.path.append(os.path.join(posix.environ['HOME'], 'public_html/cgi-bin'))
import ndltext
import ndlfile
import ndlhtml

def writeIndexHtml():
    global downloadAddText
    indexHTML = ''
    homeDir = os.environ.get("HOME")
    basePath = os.path.join(homeDir, 'public_html')
    if not anonPublish:
        file = open(os.path.join(basePath, 'softwareHeader.txt'))
        lines = file.readlines()
        for line in lines:
            indexHTML += line + "\n"
        file.close()
        file = open(os.path.join(basePath, 'softwareStyle.txt'))
        lines = file.readlines()
        for line in lines:
            indexHTML += line + "\n"
        file.close()
    file = open(os.path.join('..', 'html', 'index.txt'), 'r')
    lines = file.readlines()
    file.close()
    releaseRe = re.compile(r'RELEASEINFORMATION')
    for line in lines:
        line = releaseRe.sub(downloadAddText, line)
        indexHTML += line + "\n"
    indexHTML += "<body><p><center>Page updated on " + datetime.datetime.now().ctime() + "</center></body>"
    if not anonPublish:
        file = open(os.path.join(basePath, 'softwareFooter.txt'))
        lines = file.readlines()
        for line in lines:
            indexHTML += line + "\n"
        file.close()
    file = open(os.path.join('..', 'html', 'index.html'), 'w')
    file.write(indexHTML)
    file.close()

def getLatestVersion(toolboxName, basename='mlprojects'):
    """Get the latest version of a given MATLAB toolbox."""

    #Rangl
    homeDir = os.environ.get("HOME")
    basePath = os.path.join(homeDir, basename);
    if os.path.exists(os.path.join(basePath, toolboxName)):
        # Some home grown code
        baseToolBox = os.path.join(basePath, toolboxName, 'matlab')
    elif os.path.exists(os.path.join(basePath, 'matlab', toolboxName)):
        # someone else's code.
        baseToolBox = os.path.join(basePath, 'matlab', toolboxName)
    else:
        print 'Could note find toolbox ' + toolboxName + "\n"
        return []
    fileNames = glob.glob(os.path.join(baseToolBox, toolboxName.upper() + '*'))
    posVerDirs = []
    for fileName in fileNames:
        if os.path.isdir(fileName):
            posVerDirs.append(fileName)
            
    vers = []
    versions = []
    if len(posVerDirs)==0:
        return vers
    vrsNumRe = re.compile(r'([0-9]*)p([0-9]*)$')
    for posVerDir in posVerDirs:
        posVerDir = os.path.basename(posVerDir)
        vrsNumsMatch = re.search(vrsNumRe, posVerDir)
        grps = vrsNumsMatch.groups()
        if len(grps)>0:
            vers.append(float(grps[0] + '.' + grps[1]))

    return vers

def checkToolboxes(toolboxFile):
    """Add the toolboxes to the webpages."""
    global diagOtherToolboxes
    global downloadAddText
    toolText = ''
    file = open(toolboxFile, 'r')
    toolboxLines = file.readlines()
    if not anonPublish:
        toolText += '''<p>As well as downloading the ''' + packageName.upper() + ''' software you need to obtain the toolboxes specified below. <b>These can be downloaded using the <i>same</i> password you get from registering for the  ''' + packageName.upper() + ''' software.</b>'''
    else:
        toolText += '''<p>We made use of software available from the University of Manchester. To operate our software you must also download the following toolboxes from that site.'''
    toolText += '''
    <table>
    <tr>
    <td width="65%"><b>Toolbox</b></td>
    <td width="35%"><b>Version</b></td>
    </tr>'''
    toolsExist = 0
    for line in toolboxLines:
        line = re.sub(re.compile(r'\r'), '', line)
        versionNumber = ''
        toolboxName = ''
        foundTool = 0
        if re.findall(re.compile(r'^importTool\([^,]*\)'), line):
            print "Warning " + line + " in " + toolboxFile
            diagOtherToolboxes += line + "\n"
        else:
            vrsNum = re.search(re.compile(r'^importTool\(\'(.*)\'\s*,(.*)\)'), line)
            if vrsNum:
                toolboxName = vrsNum.groups()[0]
                versionNumber = vrsNum.groups()[1]
                foundTool = 1
            else:
                latestRe = re.search(re.compile(r'^importLatest\(\'(.*)\'\)'), line)
                if latestRe:
                    toolboxName = latestRe.groups()[0]
                    versions = getLatestVersion(toolboxName, 'mlprojects')
                    versions.extend(getLatestVersion(toolboxName, 'projects'))
                    if len(versions)>0:
                        versions.sort()
                        versionNumber = str(versions[-1])
                        foundTool = 1
        if foundTool:
            toolsExist = 1
            pRe = re.compile(r'\.')
            pvers = pRe.sub(r'p', versionNumber)
            toolText += "<tr><td><a href=\"" +codeBaseURL + toolboxName + "/downloadFiles/vrs" + pvers + "\">" + toolboxName.upper() + "</a></td><td> " + versionNumber + '</td></tr>\n'
    toolText += '</table>'
    
    if toolsExist:
        downloadAddText += toolText
            
        
def copyMatlabToPackageDir(fileName):
    """Prepare a MATLAB file and copy it to the software publish directory."""
    
    global diagNoCommentText
    global diagNotInToolbox
    global diagNotInCVSorSVNorGITText
    global diagCommentedLinesRemoved
    global contentsText
    global readMeMatlabFiles
    global techFileText
    global dummyRun
    if os.path.islink(fileName):
        fullPath = os.readlink(fileName)
    else:
        fullPath = fileName

    copyAuthorYear = []
    copyAuthorNames = []
    modAuthorNames = []
    modAuthorYear = []
    basedAuthorNames = []
    basedAuthorYear = []
    commentNotFound = 1
    wrongToolbox = 1
    inDescription = 0
    padding = '\t'
    inFormat = 0
    inArg = 0
    inDesc = 0
    inReturn = 0
    function = 0
    inFunction = 0
    storeLine = ''
    functionLine = ''
    fileComment = 0
    thisFileText = "";

    # Infer the function name
    baseName = os.path.basename(fileName)
    dir_name = os.path.dirname(fileName)
    print dir_name
    fileParts = string.split(baseName, '.')
    funcName = fileParts[0]
    seeAlso = []
    # Get CVS and/or SVN version.
    cvsVer = ndlfile.getCvsVersion(fileName, fullPath)
    svnVer = ndlfile.getSvnVersion(fileName, fullPath)
    gitVer = ndlfile.getGitVersion(fileName, dir_name, os.path.join(dir_name, '..'))
    
    if cvsVer=='' and svnVer==[] and gitVer==[]:
        print "Warning file " + fileName + " is not in CVS or SVN or GIT." + '\n'
        diagNotInCVSorSVNorGITText += fileName + '\n'
    if fileName == "Contents.m":
        return "Contents file\n."
    file = open(fileName, 'r')
    transFileLines = file.readlines()
    file.close()
    for line in transFileLines:
        line = re.sub(re.compile(r'\r'), '', line)
        if re.findall(re.compile(r'^function '), line) or inFunction:
            function = 1
            if re.findall(re.compile(r'\.\.\.\s*\n'), line):
                inFunction = 1
            else:
                inFunction = 0
            functionLine += line
            thisFileText += line            
        elif re.findall(re.compile(r'^%\s*' + capitalPackage + '\s*\n'), line):
            # We have found the toolbox indicator.
            wrongToolbox = 0;
        elif re.findall(re.compile(r'^\s*%\s*\/~'), line):
            # Start of a comment out section.
            fileComment = 1;
        elif fileComment:
            if re.findall(re.compile(r'^\s*%\s*~\/'), line):
                # End of a comment out section.
                fileComment = 0;
            elif not re.findall(re.compile(r'^\s*%.*'), line):
                print "Line: " + line + " removed from exported file.\n"
                diagCommentedLinesRemoved += line + " removed from exported " + fileName + "\n";
        elif commentNotFound:
            # search for comment line.
            if re.findall(re.compile(r'^%\s*' + funcName.upper() + '\s.*'), line):
                storeLine = line
                titleLineText = '\n% ' + line[1:-1].strip() + '\n'
                descriptionText = ''
                commentNotFound = 0;
                # Modify the function line and add it as part of comments.
                functionLine=re.sub(re.compile(r'function\s*'), '', functionLine)
                functionLine=re.sub(re.compile(r'\n'), '\n%', functionLine)
                inDescription = 1
            
        elif inDescription:
            if inFormat:
                # giving format of MATLAB command
                if re.findall(re.compile(r'^%\s*RETURN\s*'), line):
                    # These are returned values.
                    inReturn = 1
                    inArg = 0
                    inDesc = 0
                    splits = string.split(line, ':')
                    nameParts = string.split(splits[0].strip(), ' ')
                    returnList.append(nameParts[-1].strip())
                    returnDesc.append(splits[-1].strip() + ' ')
                elif re.findall(re.compile(r'^%\s*ARG.*'), line):
                    # These are the arguments.
                    inArg = 1
                    inReturn = 0
                    inDesc = 0
                    splits = string.split(line, ':')
                    nameParts = string.split(splits[0].strip(), ' ')
                    argList.append(nameParts[-1].strip())
                    argDesc.append(splits[-1].strip() + ' ') 
                elif re.findall(re.compile(r'^%\s*DESC.*'), line):
                    # These are the arguments.
                    inDesc = 1
                    inArg = 0
                    inReturn = 0
                    splits = string.split(line, 'DESC')
                    descDesc += splits[-1].strip() + ' '
                elif re.findall(re.compile(r'^%\s*$'), line):
                    # The format has ended.
                    inDesc = 0
                    inArg = 0
                    inReturn = 0
                    inFormat = 0;
                elif inDesc:
                    descDesc += line[1:-1].strip() + ' '
                elif inArg:
                    argDesc[-1] += line[1:-1].strip() + ' ' 
                elif inReturn:
                    returnDesc[-1] += line[1:-1].strip() + ' ' 
                if not inFormat:
                    # Now print the format.
                    funcSyntax = ''
                    if len(returnList)>0:
                        if len(returnList)>1:
                            funcSyntax += '['
                            for argNo in range(len(returnList)):
                                funcSyntax += returnList[argNo].upper()
                                if argNo < len(returnList)-1:
                                    funcSyntax += ', '
                            funcSyntax += ']'
                        else:
                            funcSyntax += returnList[0].upper()
                        funcSyntax += ' = '
                    funcSyntax += funcName.upper()
                    if len(argList)>0:
                        funcSyntax += '('
                        for argNo in range(len(argList)):
                            funcSyntax += argList[argNo].upper()
                            if argNo < len(argList)-1:
                                funcSyntax += ', '
                        funcSyntax += ')'
                    descriptionText += '%\n' + ndltext.wrapText(funcSyntax + ' ' + descDesc, padding)
                    if len(returnList)>0:
                        descriptionText += '%' + padding + ' Returns:\n'
                        for argNo in range(len(returnList)):
                            descriptionText += ndltext.wrapText(returnList[argNo].upper() + ' - ' + returnDesc[argNo], padding + '  ', 68, 1)
                    if len(argList)>0:
                        descriptionText += '%' + padding + ' Arguments:\n'
                        for argNo in range(len(argList)):
                            descriptionText += ndltext.wrapText(argList[argNo].upper() + ' - ' + argDesc[argNo], padding + '  ', 68, 1)
                        
                    
                    inFormat = 0
        
                            
            elif re.findall(re.compile(r'^%\s*FORMAT.*'), line):
                # prepare for format of MATLAB command.
                descDesc = ''  # This is a description of the command
                argList = []
                argDesc = []
                returnList = []
                returnDesc = []
                inFormat = 1
            elif re.findall(re.compile(r'^%\s*SEEALSO.*'), line):
                # access see also stuff.
                splits = string.split(line, ':')
                parts = splits[-1].split(',')
                for part in parts:
                    seeAlso.append(part.strip())
                
            elif re.findall(re.compile(r'^%\s*COPYRIGHT.*'), line):
                # access copyright line
                splits = string.split(line, ':')
                parts = splits[-1].split(',')
                copyAuthorNames.append(parts[0].strip())
                if anonPublish:
                    copyAuthorNames = []
                copyYear = ''
                for partNo in range(len(parts)-1):
                    copyYear += parts[partNo+1].strip()
                    if partNo < len(parts)-2:
                        copyYear += ', '
                copyAuthorYear.append(copyYear)
            elif re.findall(re.compile(r'^%\s*MODIFICATIONS.*'), line) or re.findall(re.compile(r'^%\s*MODIFIED.*'), line) :
                # access modifications line
                splits = string.split(line, ':')
                parts = splits[-1].split(',')
                modAuthorNames.append(parts[0].strip()) 
                if anonPublish:
                    modAuthorNames = []
                modYear = ''
                for partNo in range(len(parts)-1):
                    modYear += parts[partNo+1].strip()
                    if partNo < len(parts)-2:
                        modYear += ', '
                modAuthorYear.append(modYear)

            elif re.findall(re.compile(r'^%\s*BASEDON.*'), line):
                # access modifications line
                splits = string.split(line, ':')
                parts = splits[-1].split(',')
                basedAuthorNames.append(parts[0].strip()) 
                if anonPublish:
                    basedAuthorNames = []
                basedYear = ''
                for partNo in range(len(parts)-1):
                    basedYear += parts[partNo+1].strip()
                    if partNo < len(parts)-2:
                        basedYear += ', '
                basedAuthorYear.append(basedYear)
                    
                
            elif re.findall(re.compile(r'^%'), line):
                # Normal line of description.
                descriptionText += '%' + padding + line[1:-1].strip() + "\n"
            if not re.findall(re.compile(r'^%.*'), line):
                writeFuncLine = 0
                # description has finished.
                if descriptionText == '':
                    writeFuncLine = 1
                if writeFuncLine:
                    descriptionText += "%" + padding + functionLine 
                if len(seeAlso)>0:
                    descriptionText += "%\n%" + padding + 'See also\n'
                    descriptionText += '%' + padding
                    for seeNo in range(len(seeAlso)):
                        descriptionText += seeAlso[seeNo].upper()
                        if seeNo < len(seeAlso)-1:
                            descriptionText += ', '
                        else:
                            descriptionText += '\n'
                        
                # Add copyright information
                if len(copyAuthorNames)>0:
                    descriptionText+= "\n\n"
                
                for i in range(0,len(copyAuthorNames)):
                    descriptionText += "%" + padding + "Copyright (c) " + copyAuthorYear[i] + " " + copyAuthorNames[i] + "\n"                
                for i in range(0, len(basedAuthorNames)):
                    descriptionText += "\n\n%" + padding + "Based on code by " + basedAuthorNames[i] + " Copyright (c) " + basedAuthorYear[i] + "\n"                
                for i in range(0, len(modAuthorNames)):
                    descriptionText += "\n\n%" + padding + "With modifications by " + modAuthorNames[i] + " " + modAuthorYear[i] + "\n"                
                    
                # Add file version info.    
                if not cvsVer == '':
                    descriptionText += '% ' + padding + fileName + ' CVS version ' + cvsVer + "\n"
                if not svnVer == []:
                    descriptionText += '% ' + padding + fileName + ' SVN version ' + svnVer['version'] + '\n'
                if not gitVer == []:
                    descriptionText += '% ' + padding + fileName + ' Git release' + gitVer['version'] + '\n'
#                if not anonPublish and not svnVer == []:
#                    descriptionText += '% ' + padding + 'checked in by ' + user[svnVer['userName']] + '\n'
                if not svnVer == []:
                    descriptionText += '% ' + padding + 'last update ' + svnVer['textLastUpdate']
                descriptionText += '\n'
                inDescription = 0
                thisFileText += titleLineText
                thisFileText += '%\n%' + padding + 'Description:\n'
                thisFileText += descriptionText
        else:
            thisFileText += line

    if fileComment:
        print "Warning suspected unfinished comment in " + fileName + ".\n"
    if dummyRun:
        fileOut = '/dev/null'
    else:
        fileOut = os.path.join(os.curdir, verDir, fileName);
    file = open(fileOut, 'w')
    file.write(thisFileText)
    file.close()
    
    if commentNotFound:
        print "Warning " + fileName + " is not described.\n"
        print diagNoCommentText
        diagNoCommentText += fileName + "\n"
    if wrongToolbox and not fileName == lowerPackage + 'Toolboxes.m':
        if declutter and not dummyRun:
            # move file to declutter directory.
            clutterFullPath = os.path.join(os.curdir, clutterDir)
            if not os.path.exists(clutterFullPath):
                os.mkdir(clutterFullPath)
            shutil.copyfile(fileName, os.path.join(clutterFullPath, fileName))
            os.unlink(fileName)
        print "Warning " + fileName + " is not in this toolbox.\n"
        diagNotInToolbox += fileName + "\n"
    else:
        line = re.sub(re.compile(r'\r'), '', line)
        contentsText += storeLine
        storeLine = re.sub(re.compile(r'% \w*'), fileName + ":", storeLine)
        readMeMatlabFiles += storeLine
        techFileText += functionLine + "\n"
    toReturn = ''
    if not cvsVer =='':
        toReturn += ' CVS version ' + cvsVer 
    if not svnVer ==[]:
        toReturn += ' SVN version ' + svnVer['version'] 
    return fileName + ' ' + toReturn + '\n'


            
                
            
                
def commentAndCopyToPackageDir(fileName):
    copyAuthorYear = [year]
    copyAuthorNames = [authorName]

    if os.path.islink(fileName):
        fullPath = os.readlink(fileName)
    else:
        fullPath = fileName
        
    cvsVer = ndlfile.getCvsVersion(fileName, fullPath)
    svnVer = ndlfile.getSvnVersion(fileName, fullPath)
    file = open(fileName, 'r')
    transFileLines = file.readlines()
    file.close()
    writeString = '/* ' + fileName + ' version ' + cvsVer + "\n\n"
    hMatch = re.findall(hRe, fileName);
    if hMatch:
        txtFileName = re.sub(re.compile(r'.h$', re.IGNORECASE), '.txt', fullPath)
        if os.path.exists(txtFileName):
            file = open(txtFileName, 'r')
            txtFileLines = file.readlines()
            file.close()
            for line in txtFileLines:
                writeString += line
    for i in range(0,len(copyAuthorNames)-1):
        descriptionText += "\n\n" + padding + "Copyright (c) " + copyAuthorYear[i] + " " + copyAuthorNames[i] + "\n"                
    writeString += packageName.upper() + ' distribution version '
    writeString += versionNumber + ' published on ' + timeStamp + "\n\n"
    writeString += licenseText
    writeString += '*/\n\n'
    for line in transFileLines:
        line = re.sub(re.compile(r'\r'), '', line)
        writeString += line
    if dummyRun:
        fileOut = '/dev/null'
    else:
        fileOut = os.path.join(os.curdir, verDir, fileName);
    file = open(fileOut, 'w')
    file.write(writeString)
    file.close()
    toReturn = ''
    if not cvsVer =='':
        toReturn += ' CVS version ' + cvsVer 
    if not svnVer ==[]:
        toReturn += ' SVN version ' + svnVer['version'] 
    return fileName + ' ' + toReturn + '\n'
    
def copyToPackageDir(fileName):
    global dummyRun
    if os.path.islink(fileName):
        fullPath = os.readlink(fileName)
    else:
        fullPath = fileName
        
    cvsVer = ndlfile.getCvsVersion(fileName, fullPath)
    svnVer = ndlfile.getSvnVersion(fileName, fullPath)
    if not dummyRun:
        shutil.copyfile(fullPath, os.path.join(os.curdir, verDir, fileName))
    toReturn = ''
    if not cvsVer =='':
        toReturn += ' CVS version ' + cvsVer 
    if not svnVer ==[]:
        toReturn += ' SVN version ' + svnVer['version'] 
    return fileName + ' ' + toReturn + '\n'
 


user = {}
user['lawrennd'] = "Neil D. Lawrence"
user['alvarezm'] = "Mauricio A. Alvarez"
user['dluengo'] = "David Luengo"

downloadFormLocation = "http://ml.sheffield.ac.uk/~neil/cgi-bin/software/downloadForm.cgi?toolbox="
codeBaseURL = "http://staffwww.dcs.sheffield.ac.uk/people/N.Lawrence/"
codeDir = os.curdir
diagOtherToolboxes = ''
diagNotInToolbox = ''
global diagNotInCVSorSVNorGITText
diagNotInCVSorSVNorGITText = ''
diagNoCommentText = ''
diagCommentedLinesRemoved = ''
readMeMatlabFiles = ''
techFileText = ''
clutterDir = "clutterDir"
declutter = True
isMatlab = False
isPython = False
# arguments PACKAGENAME VRS AUTHORS
if len(sys.argv) < 3:
    raise "There should be two input arguments"
year = time.strftime('%Y')
timeStamp = time.strftime('%A %d %b %Y at %H:%M')
dateStamp = time.strftime('%d-%b-%Y')
packageName = sys.argv[1]
versionNumber = sys.argv[2]
if len(sys.argv) > 3:
    dummyRun = int(sys.argv[3])
else:
    dummyRun = False
if len(sys.argv) > 4:
    anonPublish = int(sys.argv[4])
else:
    anonPublish = False
    
# copyright.txt contains author information
file = 'copyright.txt'
if os.path.exists(file):
    copyFileHandle = open(file, 'r');
    copyFileLines = copyFileHandle.readlines()
    copyFileHandle.close()
    for line in copyFileLines:
        if line[0]=='#':
            continue
        else:
            authorNames = string.split(line, ',')
else:
    authorNames = ["Neil D. Lawrence"]

if anonPublish:
    authorNames = ["Anonymous"]
if anonPublish:
    downloadAddText = '''
    <p>Background details for submitted software.'''
else:
    downloadAddText = '''
    <p>The ''' + packageName.upper() + ''' software can be downloaded
    <a href="''' + downloadFormLocation + packageName +'''\">here</a>.
    <h2>Release Information</h2>
    <p><b>Current release is ''' + versionNumber + '''</b>.
    '''
pRe = re.compile(r'\.')
versionString = re.sub(pRe, 'p', versionNumber)
lowerPackage = packageName.lower();
capitalPackage = packageName.upper()
verDir = capitalPackage+versionString
fileVersionFileString='File Version listing for ' + packageName + ' ' + versionNumber + '\n'

# Start text for MATLAB contents.
contentsText = '% ' + capitalPackage + ' toolbox\n'
contentsText += '% Version ' + versionNumber + '\t\t' + dateStamp + '\n'
contentsText +=  "% Copyright (c) " + year
for authorName in authorNames:
    contentsText += ', ' + authorName
contentsText += '\n'

contentsText +=  "% \n"

# Start text for Read Me file
readMeTxt = capitalPackage + ' software\n';
readMeTxt += 'Version ' + versionNumber + '\t\t' + timeStamp + '\n';
for authorName in authorNames:
    contentsText += ', ' + authorName
contentsText += '\n'
readMeTxt +=  "\n";

# Make a list of files to ignore
file = 'ignorefiles.txt'
ignoreFiles=[]
if os.path.exists(file):
    ignoreFileHandle = open(file, 'r')
    ignoreFileLines = ignoreFileHandle.readlines()
    ignoreFileHandle.close()
    for line in ignoreFileLines:
        
        if line[0]=='#':
            continue

        fileFullName = line[0:-1]
        fileFullName.strip()
        ignoreFiles.append(fileFullName)

# Add MATLAB toolboxes file to files to ignore.
ignoreFiles.append(os.path.join(codeDir, packageName + 'Toolboxes.m'))

## Sort out directories to publish in.
publishBase=os.path.expanduser(os.path.join("~", "public_html", lowerPackage))
publishDownloadDir=os.path.join(publishBase, "downloadFiles")
publishDownloadStoreDir=os.path.join(publishDownloadDir, "vrs"+versionString)
if not anonPublish:
    if os.path.exists(publishDownloadStoreDir):
        raise Exception(publishDownloadDir + " already exists, please delete and retry.")

    if not os.path.exists(publishBase):
        if not dummyRun:
            os.mkdir(publishBase)
    if not os.path.exists(publishDownloadDir):
        if not dummyRun:
            os.mkdir(publishDownloadDir)
    else:
        if not os.path.isdir(publishDownloadDir):
            raise Exception("Cannot create directory " + publishDownloadDir+ ".")

    if not dummyRun:
        os.mkdir(publishDownloadStoreDir)


file = 'license.txt'
licenseText = ''
if os.path.exists(file):
    fileHand = open(file, 'r')
    licenseLines = fileHand.readlines()
    fileHand.close()
    for line in licenseLines:
        if line[0]=='#':
            continue
        licenseText += line

if not licenseText=='':
    readMeTxt += "License Details" + "\n---------------" + "\n\n" +  licenseText + "\n\n"

pathName = os.path.join(codeDir, verDir)
if os.path.exists(pathName):
    if not os.path.isdir(pathName):
        raise "Cannot create directory " + pathName + "."
    else:
        raise pathName + " already exists, please delete and retry."
else:
    if not dummyRun:
        os.mkdir(pathName)
 

fileNames=os.listdir(codeDir)
toolboxFileRe = re.compile(r'^' + lowerPackage + 'Toolboxes.m$')
matlabRe = re.compile(r'^.*\.m$', re.IGNORECASE)                      
pyRe = re.compile(r'^.*\.py$', re.IGNORECASE)                      
cppRe = re.compile(r'^.*\.cpp$', re.IGNORECASE)
cRe = re.compile(r'^.*\.c$', re.IGNORECASE)
hRe = re.compile(r'^.*\.h$', re.IGNORECASE)
fortranRe = re.compile(r'^.*\.f$', re.IGNORECASE)
makeRe = re.compile(r'^make[^~]*$', re.IGNORECASE)
readmeRe = re.compile(r'^readme[^~]*$', re.IGNORECASE)

for fileName in fileNames:
    fileName.strip()
    matchTrue = 0
    # Check if we should be ignoring the file
    for ignoreFileName in ignoreFiles:
        if ignoreFileName==os.path.basename(fileName):
            matchTrue = 1
            print "Ignoring: "  + fileName
            break 
    if not matchTrue:
        cppMatch = re.findall(cppRe, fileName)
        if cppMatch:
            fileVersionFileString+=commentAndCopyToPackageDir(fileName)
            continue
        cMatch = re.findall(cRe, fileName)
        hMatch = re.findall(hRe, fileName)
        if hMatch:
            fileVersionFileString+=commentAndCopyToPackageDir(fileName)
            continue
        if cMatch:
            fileVersionFileString+=commentAndCopyToPackageDir(fileName)
            continue
        fMatch = re.findall(fortranRe, fileName)
        if fMatch:
            fileVersionFileString+=copyToPackageDir(fileName)
            continue
        makeMatch = re.findall(makeRe, fileName)
        if makeMatch:
            fileVersionFileString+=copyToPackageDir(fileName)
            continue
        readMeMatch = re.findall(readmeRe, fileName)
        if readMeMatch:
            fileVersionFileString+=copyToPackageDir(fileName)
            continue
        toolboxFileMatch = re.findall(toolboxFileRe, fileName)
        if toolboxFileMatch:
            checkToolboxes(fileName)
        pyMatch = re.findall(pyRe, fileName)
        if pyMatch:
            isPython = True
            fileVersionFileString+=copyToPackageDir(fileName)
            continue
        matlabMatch = re.findall(matlabRe, fileName)
        if matlabMatch:
            isMatlab = True
            fileVersionFileString+=copyMatlabToPackageDir(fileName)
            continue

writeIndexHtml()
    
# additionalfiles.txt contains location of any additional files to copy.
file = 'additionalfiles.txt'
if os.path.exists(file):
    addFileHandle = open(file, 'r')
    addFileLines = addFileHandle.readlines()
    addFileHandle.close()
    subDir='.'
    dirRe = re.compile(r'^dir\:\s*([\w|/]*)')
    tildeRe = re.compile(r'^~')
    returnRe = re.compile(r'\n')
    for line in addFileLines:
        
        if line[0]=='#':
            continue
        dirMatch = re.findall(dirRe, line)
        if dirMatch:
            subDirs = os.path.split(dirMatch[0])
            pathName = os.path.join(codeDir, verDir)
            for subDir in subDirs:
                pathName = os.path.join(pathName, subDir)
                if os.path.exists(pathName):
                    if os.path.isdir(pathName):
                        continue
                    else:
                        raise "Cannot create directory " + pathName + "."
                else:
                    if not dummyRun:
                        os.mkdir(pathName)
            continue

        fileFullName = line
        fileFullName = re.sub(tildeRe, os.environ['HOME'], fileFullName)
        fileFullName = re.sub(returnRe, '', fileFullName).strip()
        print fileFullName + " -> " + os.path.join(pathName, os.path.basename(fileFullName))
        #        if subDir=='.':
        #            shutil.copyfile(fileFullName, os.path.join(codeDir, verDir, os.path.basename(fileFullName)))
        #        else:
        if not dummyRun:
            if os.path.exists(fileFullName):
                shutil.copy(fileFullName, os.path.join(pathName, os.path.basename(fileFullName)))
            else: 
                print "Warning " + fileFullName + " does not exist."

# Read and augment the readme file.
if not anonPublish:
    file = 'readme.txt'
    if os.path.exists(file):
        readMeFileHandle = open(file, 'r')
        readMeFileLines = readMeFileHandle.readlines()
        readMeFileHandle.close()
        for line in readMeFileLines:
            readMeTxt += line
        if isMatlab:
            readMeTxt += "\n\nMATLAB Files\n------------\n\nMatlab files associated with the toolbox are:\n\n"
            readMeTxt += readMeMatlabFiles
        if dummyRun:
            fileOut = '/dev/null'
        else:
            fileOut = os.path.join(codeDir, verDir, file)
        readMeFileHandle = open(fileOut, 'w')
        readMeFileHandle.write(readMeTxt)
        readMeFileHandle.close()
    
# Create a file containing the CVS version numbers.
if dummyRun:
    versionsFile = '/dev/null'
else:
    versionsFile = os.path.join(codeDir, verDir, 'fileVersions.dat')
file = open(versionsFile, 'w')
file.write(fileVersionFileString)
file.close()

if isMatlab:
    if dummyRun:
        contentsFile = '/dev/null'
    else:
        contentsFile = os.path.join(codeDir, verDir, 'Contents.m')
    file = open(contentsFile,'w')
    file.write(contentsText)
    file.close()

# Remove redundant packages
if not anonPublish:

    fileNames=os.listdir(publishDownloadDir)
    deleteRe = re.compile(r'^'+capitalPackage+'.*\.zip$', re.IGNORECASE)              
    for fileName in fileNames:
        fileName.strip()
        matchTrue = 0
        # Check if we should be ignoring the file
        if not matchTrue:
            deleteMatch = re.findall(deleteRe, fileName)
            if deleteMatch and not dummyRun:
                print "Removing file " + fileName + " from web page.\n"
                os.unlink(os.path.join(publishDownloadDir, fileName))
                continue

## Now zip everything up and move to public_html
if not dummyRun:
    zipDir = os.path.join(codeDir, verDir)
    zipName = verDir+".zip"
    zipCommand = "zip -r -D " +zipName + " "+ zipDir
    os.system(zipCommand)
    if not anonPublish:
        shutil.copyfile(zipName, os.path.join(publishDownloadStoreDir, zipName))
        shutil.copyfile(zipName, os.path.join(publishDownloadDir, zipName))
        shutil.copyfile(os.path.join(verDir, "readme.txt"), os.path.join(publishDownloadDir, "readme.txt"))
        shutil.copyfile(os.path.join(verDir, "readme.txt"), os.path.join(publishDownloadStoreDir, "readme.txt"))
    
        print zipDir
        fileNames=os.listdir(os.path.join(zipDir, "html"))
        for fileName in fileNames:
            shutil.copyfile(os.path.join(zipDir, "html", fileName), os.path.join(publishBase, fileName))
        os.unlink(zipName)

diagFileString = "Files not tagged as in toolbox: \n"
diagFileString += diagNotInToolbox + "\n"
diagFileString += "Files not commented:\n"
diagFileString += diagNoCommentText + "\n"
diagFileString += "Files not in CVS or SVN or GIT:\n"
diagFileString += diagNotInCVSorSVNorGITText + "\n"
diagFileString += "Dependent toolbox problems\n"
diagFileString += diagOtherToolboxes
diagFileString += "File Comments Removed\n"
diagFileString += diagCommentedLinesRemoved

if dummyRun:
    diagFile = os.path.join(codeDir, 'diagnostics.dat')
else:
    diagFile = os.path.join(codeDir, verDir, 'diagnostics.dat')
file = open(diagFile, 'w')
file.write(diagFileString)
file.close()
# texFileLines = []
# texFile = sys.argv;
# for file in texFile:
#     texFileHandle = open(file, 'r')
#     texFileLines = texFileLines + texFileHandle.readlines()
    
# bibFiles = []
# citationsList = []
# matchBib = re.compile(r"""\\bibliography{([^}]*)}""")
# matchCite = re.compile(r"""\\cite\w*{([^}]*)}""")
# for line in texFileLines:
#     lineCite = matchCite.findall(line)
#     lineBib = matchBib.findall(line)
#     if lineCite:
#         for cite in lineCite:
#             citationsList = citationsList + cite.split(',')
#     if lineBib:
#         for bib in lineBib:
#             bibFiles = bibFiles + bib.split(',')
# for i in range(len(citationsList)):
#     for j in range(i+1, len(citationsList)):
#         if citationsList[i] == citationsList[j]:
#             citationsList[j] = [];
            
        
# bibDir = os.environ['BIBINPUTS'].split(':')
# matchBibField = re.compile(r"""(\@\w+{)""")
# out = ''
# matchCrossRef = re.compile(r"""\bcrossref\s*=\s*[\"|{](.*)[}|\"]""", re.IGNORECASE)
# for dir in bibDir:
#     if not dir:
#         dir = '.'
#     for file in bibFiles:
#         if os.access(dir+'/'+file+".bib", os.F_OK):
#             bibFileHandle = open(dir + '/' + file + ".bib", 'r')
#             bibFile = bibFileHandle.read()
#             bibComp = matchBibField.split(bibFile)
#             for i in range(len(citationsList)):
#                 if citationsList[i]:
#                     for j in range(2, len(bibComp)):
#                         if not bibComp[j].find(citationsList[i])==-1:
#                             out = out + bibComp[j-1] + bibComp[j]
#                             citationsList[i] = []
#                             crossRefs = matchCrossRef.findall(bibComp[j])
#                             if crossRefs:
#                                 citationsList = citationsList + crossRefs
#                             break
            
# print out            
# #print citationsList

# #print out
# # fileNames = ['lawrence.bib', 'other.bib', 'zbooks.bib', 'winkler.bib'];
# # arg = 'scp'
# # for fileName in fileNames:
# #     arg = arg + ' /home/neil/tex/inputs/' + fileName
# # arg = arg + ' u0015@cherry.dcs.shef.ac.uk:public_html/cgi-bin/'
# # os.system(arg)
