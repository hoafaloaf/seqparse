@echo off

set pythonpath_bak=%PYTHONPATH%
set PYTHONPATH=%~dp0
set PYTHONPATH=%PYTHONPATH:~0,-1%

for %%A in ("%PYTHONPATH%") do (@set PYTHONPATH=%%~dpA)

set PYTHONPATH=%PYTHONPATH:~0,-1%
set PYTHONPATH=%PYTHONPATH%;%pythonpath_bak%
echo PYTHONPATH: %PYTHONPATH%

nosetests -v

python -m coverage xml --include=seqparse*

>pylint.out (
  pylint -d I0011,R0204,R0801,W0622 seqparse ^
    --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" ^
    --reports=yes
)

rem Reset PYTHONPATH back to its original state because Windows is stupid.
set PYTHONPATH=%pythonpath_bak%

@echo on
