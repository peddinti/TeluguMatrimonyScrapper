@echo off
cat %1|sed s/"<script[^<]*<\/script>"/""/g|sed s/"<!DOCTYPE[^>]*>"/""/g