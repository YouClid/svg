#!/bin/sh
#echo off
ls | grep .json | xargs python3 ../svg.py
