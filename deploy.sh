#!/bin/sh
set -e

if [ -z "$DDUWASH_SERVER" ] || [ -z "$DDUWASH_PATH" ]; then
	echo "Missing env:"
    [ -z "$DDUWASH_SERVER" ] && echo "  - DDUWASH_SERVER"
    [ -z "$DDUWASH_PATH" ] && echo "  - DDUWASH_PATH"
	exit 1
fi

rsync -avz api cv db "$DDUWASH_SERVER":"$DDUWASH_PATH"/
rsync -avz docker-compose.prod.yml "$DDUWASH_SERVER":"$DDUWASH_PATH"/docker-compose.yml
rsync -avz .env.prod "$DDUWASH_SERVER":"$DDUWASH_PATH"/.env

ssh "$DDUWASH_SERVER" << EOF
    cd "$DDUWASH_PATH" || { echo "❌ Failed to access $DDUWASH_PATH"; exit 1; }
    docker compose down
    docker compose up -d
EOF
