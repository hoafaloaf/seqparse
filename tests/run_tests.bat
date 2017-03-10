@echo off

set pythonpath_bak=%PYTHONPATH%
set PYTHONPATH=%~dp0
set PYTHONPATH=%PYTHONPATH:~0,-1%

for %%A in ("%PYTHONPATH%") do (@set PYTHONPATH=%%~dpA)
set PYTHONPATH=%PYTHONPATH%python;%pythonpath_bak%
echo PYTHONPATH: %PYTHONPATH%

nosetests -v -s tests --with-xunit --all-modules --traverse-namespace ^
  --cover-erase --cover-html --with-coverage --cover-inclusive --with-id

python -m coverage xml --include=seqparse*

@echo off
>pylint.out (
  pylint -d I0011,R0204,R0801 seqparse ^
    --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}"
)

rem Reset PYTHONPATH back to its original state because Windows is stupid.
set PYTHONPATH=%pythonpath_bak%

@echo on
