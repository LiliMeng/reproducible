function pathToRemove = closeTool(toolBoxName, version)

% CLOSETOOL Remove a toolbox from path.

% REPRODUCIBLE

if ~iscell(toolBoxName)
  toolBoxName = {toolBoxName};
  if nargin > 1
    version = {version};
  end
end
dirSep = filesep;
baseToolboxList = baseToolboxPath;
for j = 1:length(baseToolboxList)
for k = 1:length(baseToolboxList)
    basepath = baseToolboxList{j};
    for i = 1:length(toolBoxName)
      if exist([basepath toolBoxName{i} dirSep 'matlab']) == 7
        % internal project one of the group's.
        baseToolBox = [basepath toolBoxName{i} dirSep 'matlab'];
      elseif exist([basepath 'matlab' dirSep toolBoxName{i}]) == 7
        % someone else's code.
        baseToolBox = [basepath 'matlab' dirSep toolBoxName{i}];
      else
        error(['Could note find toolbox ' toolBoxName{i}]);
      end
      if nargin < 2
        pathToRemove = baseToolBox;
      else
        version{i} = vers2string(version{i});
        toolBoxNameVersion = [upper(toolBoxName{i}) version{i}];
        pathToRemove = [baseToolBox dirSep toolBoxNameVersion];
    
    
      end
      rmpath(pathToRemove);
    end
end
end