function strVers = vers2string(version)

% VERS2STRING Convert version to a string.

% REPRODUCIBLE

if ~ischar(version)
  strVers = num2str(version);
  if ~rem(version, 1)
    strVers = [strVers '.0'];
  end
else
  strVers = version;
end
charVers = double(strVers);
index = find(charVers==46);
charVers(index) = 112;
strVers = char(charVers);
