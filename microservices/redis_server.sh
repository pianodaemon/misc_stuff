#!/bin/bash

REDIS_IMG_NAME="redislabs/rebloom:latest"
docker run --rm -p 6379:6379 $REDIS_IMG_NAME
