function path = baseToolboxPath;

% BASETOOLBOXPATH Returns the base directory where all toolboxes are stored.

% REPRODUCIBLE

HOME = getenv('HOME');
dirSep = filesep;
path = {[HOME dirSep 'SheffieldML' dirSep],[HOME dirSep 'lawrennd' dirSep],[HOME dirSep 'sods' dirSep]};