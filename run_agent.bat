@echo off
chcp 65001 > nul
title AI AGENT SKILL RUNNER - SALON HAIR HA MINH
echo =========================================================================
echo    🤖 KHOI DONG AI AGENT SKILL RUNNER - SALON HAIR HA MINH
echo    Du An: He Thong Quan Ly Dat Lich Salon Toc Tich Hop AI
echo =========================================================================
python "%~dp0Agent\agent_runner.py" %*
pause
