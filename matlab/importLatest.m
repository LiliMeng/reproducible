function pathToAdd = importLatest(toolBoxName)

% IMPORTLATEST Import the latest version of a toolbox.

% REPRODUCIBLE

pathToAdd = importTool(toolBoxName, max(versTool(toolBoxName)));