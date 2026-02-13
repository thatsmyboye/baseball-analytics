#!/bin/bash
# Setup daily cron job for automated scraping

# Get the project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"

# Create cron job that runs daily at 3 AM
CRON_COMMAND="0 3 * * * cd $PROJECT_DIR && /usr/local/bin/python -m src.automation.daily_scraper >> $PROJECT_DIR/cron.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

echo "✅ Cron job installed!"
echo "   Runs daily at 3:00 AM"
echo "   Logs to: $PROJECT_DIR/cron.log"
echo ""
echo "To view current crontab:"
echo "   crontab -l"
echo ""
echo "To remove cron job:"
echo "   crontab -r"