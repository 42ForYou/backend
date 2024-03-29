#!/bin/bash

# 'ssl-init' 컨테이너의 작업 완료를 기다림
while [ ! -f /etc/backend/ssl/backend.crt ]; do
  echo "Waiting for ssl-init to complete..."
  sleep 1
done

>&2 echo "ssl-init is done!"