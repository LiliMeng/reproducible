function pathToAdd = importTool(toolBoxName, version)

% IMPORTTOOL Import a toolbox.
% FORMAT
% DESC imports a toolbox from the local file system into the path.
% ARG toolboxName : name of the toolbox.
% ARG version : version of the toolbox (if not given the current toolbox
% version is used).
% RETURN pathToAdd : the path to be added.
%
% SEEALSO : importLatest, closeTool
%
% COPYRIGHT : Neil D. Lawrence, 2008, 2011, 2013
  
% REPRODUCIBLE

% Need to throw an warning if a toolbox is already in the path.

if ~iscell(toolBoxName)
  toolBoxName = {toolBoxName};
  if nargin > 1
    version = {version};
  end
end
dirSep = filesep;
baseToolboxList = baseToolboxPath;
pathToAdd = [];
toolboxFound = false;
for k = 1:length(baseToolboxList)
  basepath = baseToolboxList{k};
  for i = 1:length(toolBoxName)
    if exist([basepath toolBoxName{i} dirSep 'matlab']) == 7
      % internal project one of the research group's.
      baseToolBox = [basepath toolBoxName{i} dirSep 'matlab'];
      toolboxFound = true;
    elseif exist([basepath 'matlab' dirSep toolBoxName{i}]) == 7
      % someone else's code.
      baseToolBox = [basepath 'matlab' dirSep toolBoxName{i}];
      toolboxFound = true;
    elseif exist([basepath dirSep toolBoxName{i}]) == 7
      baseToolBox = [basepath dirSep toolBoxName{i}];
      toolboxFound = true;
    end
  end
  if toolboxFound
    if nargin < 2 || isempty(version{i})
      if ~any(findstr(baseToolBox, path));
        pathToAdd = [baseToolBox dirSep];
      end
    else
      version{i} = vers2string(version{i});
      toolBoxNameVersion = [upper(toolBoxName{i}) version{i}];
      toolBoxPath = [baseToolBox dirSep toolBoxNameVersion];
      if ~any(findstr(toolBoxPath, path));
        pathToAdd = [toolBoxPath dirSep];
      end
    end
  end
end  
if toolboxFound
  if ~isempty(pathToAdd);
    disp(['Adding ' pathToAdd]);
    %addpath(pathToAdd);
    path(genpath(pathToAdd), path);
    disp(['Added.']);
  end
else
  error(['Could not find toolbox ' toolBoxName{i} '.']);
end

