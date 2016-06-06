#!/bin/bash

echo "kill $$" > kill-ai.sh

while true
do
  python main.py 4 localhost 2016
done
