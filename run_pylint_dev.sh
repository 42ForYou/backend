#!/bin/bash

export_env_vars() {
    while IFS= read -r line; do
        # Skip empty lines and lines starting with #
        if [ ! -z "$line" ] && [ "${line:0:1}" != "#" ]; then
            export "$line"
        fi
    done < "$1"
}

# Call the function with each environment file
export_env_vars ".env.dev"
export_env_vars "../../.env.dev"

# Check if there is a first argument
if [ -n "$1" ]; then
    # If there's a first argument, use it in the pylint command
    pylint ./src --disable=all --enable="$1"
else
    # If there's no argument, just run pylint ./src
    pylint ./src
fi
