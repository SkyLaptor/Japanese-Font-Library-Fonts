@echo off
setlocal
cd /d %~dp0

rem If not specified, set a safer default Java heap for FFDec
if NOT DEFINED JFL_JAVA_OPTS (
	if NOT DEFINED JFL_JAVA_MAX_HEAP_MB (
		set JFL_JAVA_MAX_HEAP_MB=4096
		echo [run] JFL_JAVA_MAX_HEAP_MB not set. Using default 4096 MB for FFDec.
	)
)

uv run main.py %*