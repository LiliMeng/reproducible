function versions = versTool(toolBoxName)

% VERSTOOL Get available versions of a toolbox.
% FORMAT
% DESC gets all the version numbers of a toolbox that are in the
% local filesystem.
% ARG toolboxName : name of the toolbox.
% RETURN versions: vector of different version numbers in toolbox.

% SEEALSO importLatest, closeLatest

% COPYRIGHT : Neil D. Lawrence, 2008, 2011, 2013
  
% REPRODUCIBLE

dirSep = filesep;
pathToAdd = [];
basepathList = baseToolboxPath;
toolboxFound = false;
counter = 0;
for i = 1:length(basepathList)
  toolboxHere = false;
  basepath = basepathList{i};
  disp(basepath)
  if exist([basepath toolBoxName dirSep 'matlab']) == 7
    % internal project one of Neil's.
    baseToolBox = [basepath toolBoxName dirSep 'matlab'];
    toolboxHere = true;
    toolboxFound = true;
  elseif exist([basepath 'matlab' dirSep toolBoxName]) == 7
    % someone else's code.
    baseToolBox = [basepath 'matlab' dirSep toolBoxName];
    toolboxHere = true;
    toolboxFound = true;
  elseif exist([basepath dirSep toolBoxName]) == 7
    baseToolBox = [basepath dirSep toolBoxName];
    toolboxHere = true;
    toolboxFound = true;
  end
  if toolboxHere
    dirToRead = [baseToolBox dirSep];
    if isoctave
      fileNames = readdir(dirToRead);
    else
      fileNames = dir([dirToRead  upper(toolBoxName) '*']);
    end
    for j = 1:length(fileNames)
      if isoctave
        dirToRead = [baseToolBox dirSep];
        if isdir([dirToRead fileNames{j}])
          counter = counter+1;
          posVerDir{counter} = fileNames{j};
        end
      else
        if fileNames(j).isdir
          counter = counter+1;
          posVerDir{counter} = fileNames(j).name;
        end
      end
    end
  end
end
if toolboxFound
  if counter == 0
    versions = [];
    return
  end
  counter = 0;
  for j = 1:length(posVerDir)
    m = regexp(posVerDir{j}, ...
               [upper(toolBoxName) '(?<first>[0-9]*)p(?<last>[0-9]*)'], ...
               'names');
    if (length(m)>0 && ~isoctave) || ~isempty(m.first)
      counter = counter + 1;
      versions(counter) = str2num([m.first '.' m.last]);
    end
  end
  if counter == 0
    versions = [];
    return
  end
else
  error(['Could note find toolbox ' toolBoxName]);
end