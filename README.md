# Pizza 4P's Slot Checker

Automated slot checker for Pizza 4P's restaurant reservations. This serverless function checks for available slots every 30 minutes and sends email notifications when slots are found.

## Features

- Checks for slots on May 17th and 18th, 2025
- Looks for slots between 12 PM to 9 PM
- Tries booking for 2-4 adults
- Sends email notifications when slots are found

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file based on `.env.example` and add your Gmail credentials:
   ```
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   ```

4. Deploy to Netlify:
   ```bash
   netlify deploy
   ```

## Configuration

You can modify the following in `netlify/functions/check_slots.js`:
- TARGET_DATES
- TIME_RANGE
- BOOKING_INFO (name, phone, number of adults)

## Development

To run locally:
```bash
netlify dev
```

## Environment Variables

- `EMAIL_USER`: Gmail address for sending notifications
- `EMAIL_PASSWORD`: Gmail App Password (not your regular password)
