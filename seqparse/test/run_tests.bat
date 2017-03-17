@echo off

set pythonpath_bak=%PYTHONPATH%
set PYTHONPATH=%~dp0
set PYTHONPATH=%PYTHONPATH:~0,-1%

for %%A in ("%PYTHONPATH%") do (@set PYTHONPATH=%%~dpA)

set PYTHONPATH=%PYTHONPATH:~0,-1%
set PYTHONPATH=%PYTHONPATH%;%pythonpath_bak%
echo PYTHONPATH: %PYTHONPATH%

nosetests -v -s seqparse --with-xunit --all-modules --traverse-namespace ^
  --cover-erase --cover-html --cover-inclusive --with-coverage --with-id

rem python -m coverage xml --include=seqparse*

>pylint.out (
  pylint -d I0011,R0204,R0801 seqparse ^
    --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}"
)

rem Reset PYTHONPATH back to its original state because Windows is stupid.
set PYTHONPATH=%pythonpath_bak%

@echo on
