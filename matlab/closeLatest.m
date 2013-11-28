function pathToAdd = closeLatest(toolBoxName)

% CLOSELATEST Remove the latest version of a toolbox.

% REPRODUCIBLE

pathToAdd = closeTool(toolBoxName, max(versTool(toolBoxName)));