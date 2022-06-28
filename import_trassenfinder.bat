@echo off
set script_path=%0
set pyscript=%script_path:.bat=.py%
python %pyscript% %*