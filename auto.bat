@echo off
for /l %%x in (1, 1, 10) do python pacman.py  -q -n 10 -p MDPAgent -l mediumClassic
pause